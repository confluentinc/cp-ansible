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
        - Priority: inventory vars > role default (true)
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
        self.auto_collect_enabled = None
        self.variable_found_in_inventory = False

    def v2_playbook_on_start(self, playbook):
        self.playbook_name = os.path.basename(playbook._file_name)
        self.playbook_dir = os.path.dirname(os.path.abspath(playbook._file_name))

    def v2_playbook_on_play_start(self, play):
        if self.variable_found_in_inventory or not play or not hasattr(play, '_variable_manager'):
            return

        try:
            variable_manager = play.get_variable_manager()
            inventory = variable_manager._inventory

            # Check group-level variables only (not host-level overrides)
            # Look in 'all' group variables which apply to entire deployment
            all_group = inventory.groups.get('all')
            if all_group:
                group_vars = all_group.get_vars()
                value = group_vars.get('support_bundle_auto_collect_on_failure')

                if value is not None:
                    self.variable_found_in_inventory = True
                    self.auto_collect_enabled = value in [True, 'true', 'True', 'yes', '1']
        except Exception:
            pass

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

        # Use inventory value if found, otherwise default to true (role default)
        auto_collect = self.auto_collect_enabled if self.variable_found_in_inventory else True

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
