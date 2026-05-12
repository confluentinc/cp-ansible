#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Ansible callback plugin to auto-collect support bundle on playbook failure."""

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
    callback: support_bundle_on_failure
    type: notification
    short_description: Automatically collect support bundle on playbook failure
    description:
        - Triggers support_bundle.yml when any playbook fails
        - Skips support_bundle.yml itself to prevent recursion
        - Defaults to true (matches role default in confluent.platform.variables)
        - Variable precedence: extra vars (-e) > inventory vars > default (true)
    options:
      support_bundle_auto_collect_on_failure:
        description: Enable automatic support bundle collection on failure
        default: True
        type: bool
        vars:
          - name: support_bundle_auto_collect_on_failure
'''

import os
import subprocess
from ansible.plugins.callback import CallbackBase
from ansible import constants as C
from ansible import context
from ansible.utils.display import Display

display = Display()


class CallbackModule(CallbackBase):
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'notification'
    CALLBACK_NAME = 'support_bundle_on_failure'
    CALLBACK_NEEDS_ENABLED = True

    def __init__(self):
        super(CallbackModule, self).__init__()
        self.playbook_name = None
        self.playbook_dir = None
        self.play = None

    def v2_playbook_on_start(self, playbook):
        self.playbook_name = os.path.basename(playbook._file_name)
        self.playbook_dir = os.path.dirname(os.path.abspath(playbook._file_name))

    def v2_playbook_on_play_start(self, play):
        # Capture the first play to access variable manager
        if self.play is None:
            self.play = play

    def v2_playbook_on_stats(self, stats):
        # Skip support_bundle.yml itself to prevent recursion
        if self.playbook_name == 'support_bundle.yml':
            return

        # Check if there were any failures
        failed = any(
            stats.summarize(h).get('failures', 0) > 0 or
            stats.summarize(h).get('unreachable', 0) > 0
            for h in stats.processed
        )

        if not failed:
            return

        # Get variable value respecting Ansible's variable precedence
        # Priority: extra vars (-e) > inventory vars > default (true)
        auto_collect = True  # Default value

        # Read from inventory 'all' group vars (deployment-wide setting)
        # We check 'all' group specifically because this is a deployment-wide setting
        # (callbacks run on control node, not per-host)
        if self.play and hasattr(self.play, '_variable_manager'):
            try:
                variable_manager = self.play.get_variable_manager()
                inventory = variable_manager._inventory
                all_group = inventory.groups.get('all')
                if all_group:
                    group_vars = all_group.get_vars()
                    if 'support_bundle_auto_collect_on_failure' in group_vars:
                        value = group_vars['support_bundle_auto_collect_on_failure']
                        auto_collect = value in [True, 'true', 'True', 'yes', '1', 1]
            except Exception as e:
                display.vvv(f"Failed to read variable from inventory: {e}")
                pass

        # Check for extra vars override (highest precedence)
        if hasattr(context, 'CLIARGS') and context.CLIARGS:
            extra_vars = context.CLIARGS.get('extra_vars', ())
            for ev_str in (extra_vars if isinstance(extra_vars, tuple) else []):
                if 'support_bundle_auto_collect_on_failure=' in ev_str:
                    value_str = ev_str.split('=', 1)[1].lower()
                    auto_collect = value_str not in ('false', 'no', '0', 'off')
                    break

        if not auto_collect:
            display.display("\nTo collect diagnostics: ansible-playbook support_bundle.yml", color=C.COLOR_HIGHLIGHT)
            display.display("Or set: support_bundle_auto_collect_on_failure: true\n", color=C.COLOR_HIGHLIGHT)
            return

        self._collect_support_bundle()

    def _collect_support_bundle(self):
        support_bundle_playbook = os.path.join(self.playbook_dir, 'support_bundle.yml')
        if not os.path.exists(support_bundle_playbook):
            display.warning("support_bundle.yml not found at: %s" % support_bundle_playbook)
            return

        collection_root = os.path.dirname(self.playbook_dir)
        cmd = ['ansible-playbook', support_bundle_playbook]

        # Get inventory and verbosity from CLIARGS
        if hasattr(context, 'CLIARGS') and context.CLIARGS:
            inventory = context.CLIARGS.get('inventory')
            if inventory:
                # inventory is a tuple of paths - add each with -i
                for inv_path in (inventory if isinstance(inventory, tuple) else [inventory]):
                    cmd.extend(['-i', os.path.abspath(str(inv_path))])

            verbosity = context.CLIARGS.get('verbosity', 0)
            if verbosity > 0:
                cmd.append('-' + 'v' * verbosity)

        display.vvv("Executing: %s" % ' '.join(cmd))
        subprocess.run(cmd, cwd=collection_root)
