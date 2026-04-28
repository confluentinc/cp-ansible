#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Ansible callback plugin to automatically collect support bundle on playbook failure.

This plugin detects when the main deployment playbook (all.yml) fails and
automatically triggers support bundle collection if enabled.

Configuration:
  Enable in ansible.cfg:
    [defaults]
    callbacks_enabled = support_bundle_on_failure

  Enable auto-collection:
    support_bundle_auto_collect_on_failure: true

Usage:
  ansible-playbook -i inventory.yml all.yml
  # Set support_bundle_auto_collect_on_failure: true in inventory
  # If deployment fails, support bundle is automatically collected
"""

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    callback: support_bundle_on_failure
    type: notification
    short_description: Automatically collect support bundle on playbook failure
    version_added: "1.0"
    description:
        - This callback plugin detects when a Confluent Platform deployment fails
        - Automatically triggers support bundle collection if enabled
        - Re-raises the original error after collection
    requirements:
      - Ansible >= 2.9
    options:
      support_bundle_auto_collect_on_failure:
        description: Enable automatic support bundle collection on failure
        default: False
        type: bool
        env:
          - name: SUPPORT_BUNDLE_AUTO_COLLECT_ON_FAILURE
        ini:
          - section: defaults
            key: support_bundle_auto_collect_on_failure
        vars:
          - name: support_bundle_auto_collect_on_failure
'''

import os
import subprocess
import sys
from ansible.plugins.callback import CallbackBase
from ansible import constants as C
from ansible import context
from ansible.utils.display import Display

display = Display()


class CallbackModule(CallbackBase):
    """
    Callback plugin to auto-collect support bundle on playbook failure.
    """
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'notification'
    CALLBACK_NAME = 'support_bundle_on_failure'
    CALLBACK_NEEDS_ENABLED = True

    def __init__(self):
        super(CallbackModule, self).__init__()
        self.playbook_name = None
        self.playbook_dir = None
        self.deployment_failed = False
        self.auto_collect_enabled = None
        self.play_context = None

    def v2_playbook_on_start(self, playbook):
        """
        Called when playbook starts - capture playbook info.
        """
        self.playbook_name = os.path.basename(playbook._file_name)
        self.playbook_dir = os.path.dirname(os.path.abspath(playbook._file_name))

        display.vvv("Support bundle callback loaded for playbook: %s" % self.playbook_name)

    def v2_playbook_on_play_start(self, play):
        """
        Called when a play starts - capture variables from play context.
        """
        # Skip if we already found the variable
        if self.auto_collect_enabled:
            return

        # Try to get the auto-collect setting from play variables
        if play and hasattr(play, '_variable_manager'):
            try:
                # Get the variable manager and inventory
                variable_manager = play.get_variable_manager()
                inventory = variable_manager._inventory

                # Get actual hosts from the play (resolves groups to hosts)
                actual_hosts = inventory.get_hosts(pattern=play.hosts)

                display.vvv("Play '%s' has %d hosts: %s" % (play.get_name(), len(actual_hosts), [h.name for h in actual_hosts]))

                # Check variables for each actual host
                if actual_hosts:
                    for host_obj in actual_hosts:
                        try:
                            all_vars = variable_manager.get_vars(play=play, host=host_obj, task=None)

                            # Check for the auto-collect flag
                            auto_collect = all_vars.get('support_bundle_auto_collect_on_failure', False)

                            display.vvv("Checking host %s: support_bundle_auto_collect_on_failure = %s" % (host_obj.name, auto_collect))

                            if auto_collect in [True, 'true', 'True', 'yes', '1']:
                                self.auto_collect_enabled = True
                                display.vvv("Auto-collect enabled via inventory/vars for host %s" % host_obj.name)
                                break  # Found it, no need to check other hosts
                        except Exception as e:
                            display.vvv("Error checking host %s: %s" % (host_obj.name, str(e)))
                else:
                    display.vvv("No hosts in play: %s" % play.get_name())
            except Exception as e:
                display.vvv("Could not read support_bundle_auto_collect_on_failure from play vars: %s" % str(e))

    def v2_playbook_on_stats(self, stats):
        """
        Called when playbook completes - check for failures and trigger support bundle.
        """
        # Check if this is the main deployment playbook
        if self.playbook_name not in ['all.yml', 'confluent.yml']:
            display.vvv("Skipping support bundle collection - not main playbook (%s)" % self.playbook_name)
            return

        # Check if there were any failures
        hosts = sorted(stats.processed.keys())
        failed_hosts = []
        unreachable_hosts = []

        for host in hosts:
            summary = stats.summarize(host)
            if summary.get('failures', 0) > 0:
                failed_hosts.append(host)
            if summary.get('unreachable', 0) > 0:
                unreachable_hosts.append(host)

        # Determine if deployment failed
        self.deployment_failed = len(failed_hosts) > 0 or len(unreachable_hosts) > 0

        if not self.deployment_failed:
            display.vvv("Playbook succeeded - no support bundle needed")
            return

        # Check if auto-collection is enabled (check all sources)
        auto_collect = self._get_auto_collect_setting()

        if not auto_collect:
            display.display("")
            display.display("=" * 80, color=C.COLOR_ERROR)
            display.display("Confluent Platform Deployment FAILED", color=C.COLOR_ERROR)
            display.display("=" * 80, color=C.COLOR_ERROR)
            display.display("")
            display.display("To collect diagnostics, run:", color=C.COLOR_HIGHLIGHT)
            display.display("  ansible-playbook support_bundle.yml", color=C.COLOR_HIGHLIGHT)
            display.display("")
            display.display("Or enable auto-collection:", color=C.COLOR_HIGHLIGHT)
            display.display("  support_bundle_auto_collect_on_failure: true", color=C.COLOR_HIGHLIGHT)
            display.display("")
            return

        # Auto-collection is enabled - collect support bundle
        display.display("")
        display.display("=" * 80, color=C.COLOR_ERROR)
        display.display("Deployment Failed - Auto-collecting Support Bundle", color=C.COLOR_ERROR)
        display.display("=" * 80, color=C.COLOR_ERROR)
        display.display("")

        try:
            self._collect_support_bundle()
        except Exception as e:
            display.warning("Support bundle collection failed: %s" % str(e))
            display.display("")
            display.display("Run manually: ansible-playbook support_bundle.yml", color=C.COLOR_HIGHLIGHT)
            display.display("")

    def _get_auto_collect_setting(self):
        """
        Get the support_bundle_auto_collect_on_failure setting.
        Check in order: inventory/play vars (captured earlier), extra vars, environment.
        """
        # Check if we captured it from play vars (highest priority for inventory)
        if self.auto_collect_enabled is True:
            display.vvv("Using auto-collect setting from inventory/play vars: True")
            return True

        # Check extra vars from CLI args
        try:
            if hasattr(context, 'CLIARGS') and context.CLIARGS:
                extra_vars = context.CLIARGS.get('extra_vars', [])
                for extra_var_dict in extra_vars:
                    if isinstance(extra_var_dict, dict):
                        if extra_var_dict.get('support_bundle_auto_collect_on_failure') in [True, 'true', 'True', 'yes', '1']:
                            display.vvv("Auto-collect enabled via CLI extra_vars")
                            return True
        except Exception as e:
            display.vvv("Could not check CLIARGS for extra_vars: %s" % str(e))

        # Check environment variable
        env_value = os.environ.get('SUPPORT_BUNDLE_AUTO_COLLECT_ON_FAILURE', '').lower()
        if env_value in ['true', '1', 'yes']:
            display.vvv("Auto-collect enabled via environment variable")
            return True

        # Check if passed via sys.argv (command line)
        for arg in sys.argv:
            if 'support_bundle_auto_collect_on_failure=true' in arg.lower():
                display.vvv("Auto-collect enabled via command line argument")
                return True

        display.vvv("Auto-collect disabled (not enabled in any source)")
        return False

    def _collect_support_bundle(self):
        """
        Execute support_bundle.yml playbook.
        """
        support_bundle_playbook = os.path.join(self.playbook_dir, 'support_bundle.yml')

        if not os.path.exists(support_bundle_playbook):
            raise Exception("support_bundle.yml not found at: %s" % support_bundle_playbook)

        # Collection root is parent of playbook_dir (for ansible.cfg and collection resolution)
        collection_root = os.path.dirname(self.playbook_dir)

        # Build ansible-playbook command with relative path from collection root
        cmd = ['ansible-playbook', 'playbooks/support_bundle.yml']

        # Get inventory from CLIARGS
        try:
            if hasattr(context, 'CLIARGS') and context.CLIARGS:
                inventory = context.CLIARGS.get('inventory')
                if inventory:
                    # Handle different inventory formats
                    if isinstance(inventory, (list, tuple)):
                        inventory_path = str(inventory[0])
                    else:
                        inventory_path = str(inventory)
                    cmd.extend(['-i', inventory_path])

                # Get verbosity
                verbosity = context.CLIARGS.get('verbosity', 0)
                if verbosity > 0:
                    cmd.append('-' + 'v' * verbosity)
        except Exception as e:
            display.vvv("Could not get inventory/verbosity from CLIARGS: %s" % str(e))

        display.display("Executing: %s" % ' '.join(cmd), color=C.COLOR_DEBUG)
        display.display("")

        # Execute support bundle collection
        try:
            result = subprocess.run(
                cmd,
                cwd=collection_root,
                capture_output=False,  # Show output in real-time
                text=True
            )

            display.display("")
            if result.returncode == 0:
                display.display("=" * 80, color=C.COLOR_OK)
                display.display("Support Bundle Collected Successfully", color=C.COLOR_OK)
                display.display("=" * 80, color=C.COLOR_OK)
                display.display("Check support_bundle_*.tar.gz in output directory", color=C.COLOR_HIGHLIGHT)
            else:
                display.display("=" * 80, color=C.COLOR_ERROR)
                display.display("Support Bundle Collection Failed", color=C.COLOR_ERROR)
                display.display("=" * 80, color=C.COLOR_ERROR)
                display.display("Run manually: ansible-playbook support_bundle.yml", color=C.COLOR_HIGHLIGHT)
            display.display("")

        except Exception as e:
            raise Exception("Failed to execute support_bundle.yml: %s" % str(e))
