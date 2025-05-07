#!/usr/bin/python3

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
---
module: update_log4j2
short_description: Update log4j2 YAML RollingFile policies
version_added: "1.0.0"
description:
    - Removes TimeBasedTriggeringPolicy from RollingFile appenders in a log4j2 YAML file and adds/updates SizeBasedTriggeringPolicy and DefaultRolloverStrategy.
    - Optionally updates the root logger level.
options:
    path:
        type: str
        required: true
        description:
            - Path to the log4j2 YAML file to update.
    size:
        type: str
        required: true
        description:
            - Value for SizeBasedTriggeringPolicy (e.g., '100MB').
    max:
        type: str
        required: true
        description:
            - Value for DefaultRolloverStrategy max (e.g., '10').
    root_level:
        type: str
        required: false
        description:
            - If set, update the root logger level to this value.
    root_appenders:
        type: list
        elements: str
        required: true
author:
    - Your Name (@yourgithub)
'''

EXAMPLES = '''
- name: Update log4j2.yaml policies
  update_log4j2:
    path: /path/to/log4j2.yaml
    size: 100MB
    max: 10
    root_level: INFO
    root_appenders:
      - RollingFile
'''

RETURN = '''
changed:
    description: Whether the file was changed
    type: bool
    returned: always
message:
    description: Summary of actions taken
    type: str
    returned: always
'''

import yaml
import os
from ansible.module_utils.basic import AnsibleModule

def main():
    module_args = dict(
        path=dict(type='str', required=True),
        size=dict(type='str', required=True),
        max=dict(type='str', required=True),
        root_level=dict(type='str', required=False, default=None),
        root_appenders=dict(type='list', elements='str', required=True),
    )

    result = dict(changed=False, message='')
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    path = module.params['path']
    size = module.params['size']
    max_backup = module.params['max']
    root_level = module.params['root_level']
    root_appenders = module.params['root_appenders']

    if not os.path.exists(path):
        module.fail_json(msg=f"File {path} does not exist.", **result)

    with open(path, 'r') as f:
        data = yaml.safe_load(f)

    changed = False
    # Normalize RollingFile to always be a list for processing
    rollingfiles = data['Configuration']['Appenders'].get('RollingFile', [])
    single_rollingfile = False
    if isinstance(rollingfiles, dict):
        rollingfiles = [rollingfiles]
        single_rollingfile = True
    # Update RollingFile appenders
    for appender in rollingfiles:
        # Remove direct TimeBasedTriggeringPolicy if present
        if 'TimeBasedTriggeringPolicy' in appender:
            appender.pop('TimeBasedTriggeringPolicy')
            changed = True
        # If Policies block exists, remove TimeBasedTriggeringPolicy from it and add/update SizeBasedTriggeringPolicy
        if 'Policies' in appender and isinstance(appender['Policies'], dict):
            if 'TimeBasedTriggeringPolicy' in appender['Policies']:
                appender['Policies'].pop('TimeBasedTriggeringPolicy')
                changed = True
            if appender['Policies'].get('SizeBasedTriggeringPolicy', {}).get('size') != size:
                appender['Policies']['SizeBasedTriggeringPolicy'] = {'size': size}
                changed = True
        else:
            # If no Policies block, add SizeBasedTriggeringPolicy as a direct key
            if appender.get('SizeBasedTriggeringPolicy', {}).get('size') != size:
                appender['SizeBasedTriggeringPolicy'] = {'size': size}
                changed = True
        # Add or update DefaultRolloverStrategy
        if appender.get('DefaultRolloverStrategy', {}).get('max') != (int(max_backup) if max_backup.isdigit() else max_backup):
            appender['DefaultRolloverStrategy'] = {'max': int(max_backup) if max_backup.isdigit() else max_backup}
            changed = True
    # Write back as dict if only one RollingFile appender, else as list
    if rollingfiles:
        data['Configuration']['Appenders']['RollingFile'] = rollingfiles[0] if single_rollingfile and len(rollingfiles) == 1 else rollingfiles

    # Optionally update root logger level
    if root_level:
        loggers = data['Configuration'].get('Loggers', {})
        if 'Root' in loggers and loggers['Root'].get('level') != root_level:
            loggers['Root']['level'] = root_level
            changed = True
    # Always update root logger appenders
    loggers = data['Configuration'].get('Loggers', {})
    if 'Root' in loggers:
        # Ensure AppenderRef is a list of dicts with 'ref' keys, as per Log4j2 standard
        new_refs = [{'ref': ref} for ref in root_appenders]
        if loggers['Root'].get('AppenderRef', []) != new_refs:
            loggers['Root']['AppenderRef'] = new_refs
            changed = True

    if changed and not module.check_mode:
        with open(path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
        result['message'] = f"Updated {path}: removed TimeBasedTriggeringPolicy and added/updated SizeBasedTriggeringPolicy for all RollingFile appenders."
        if root_level:
            result['message'] += f" Set root logger level to {root_level}."
        result['message'] += f" Set root logger appenders to {root_appenders}."
    else:
        result['message'] = "No changes needed."

    result['changed'] = changed
    module.exit_json(**result)

if __name__ == '__main__':
    main() 