#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
---
module: update_log4j2
short_description: Update log4j2 YAML RollingFile policies and configure log redaction
version_added: "1.0.0"
description:
    - Removes TimeBasedTriggeringPolicy from RollingFile appenders in a log4j2 YAML file and adds/updates SizeBasedTriggeringPolicy and DefaultRolloverStrategy.
    - Optionally updates the root logger level and adds a Rewrite appender with RedactorPolicy for log redaction.
requirements:
    - PyYAML
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
        description:
            - List of appender names to set in the root logger's AppenderRef.
    add_redactor:
        type: bool
        required: false
        default: false
        description:
            - Whether to add/update a Rewrite appender with RedactorPolicy.
    redactor_refs:
        type: list
        elements: str
        required: false
        description:
            - List of appender names the RedactorAppender should reference.
    redactor_rules:
        type: str
        required: false
        description:
            - Path to the redactor rules file.
    redactor_policy_refresh_interval:
        type: str
        required: false
        description:
            - Policy refresh interval for the RedactorAppender (e.g., '60').
    redactor_logger_names:
        type: list
        elements: str
        required: false
        description:
            - List of logger names to apply the RedactorAppender to.
author:
    - Mansi Sinha (@mansisinha)
'''

EXAMPLES = '''
# Update log4j2.yaml policies only
- name: Update log4j2.yaml policies
  update_log4j2:
    path: /path/to/log4j2.yaml
    size: 100MB
    max: 10
    root_level: INFO
    root_appenders:
      - RollingFile

# Update log4j2.yaml with log redaction using Rewrite appender
- name: Update log4j2.yaml with redactor appender
  update_log4j2:
    path: /path/to/log4j2.yaml
    size: 100MB
    max: 10
    root_level: INFO
    root_appenders:
      - RollingFile
    add_redactor: true
    redactor_refs:
      - RollingFile
      - STDOUT
    redactor_rules: /etc/kafka/redactor-rules.json
    redactor_logger_names:
      - org.apache.kafka
      - org.reflections
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

# Note: yaml import moved inside main() to avoid sanity test issues
import os
from ansible.module_utils.basic import AnsibleModule
try:
    import yaml
except ImportError:
    HAS_YAML = False
else:
    HAS_YAML = True


def main():

    module_args = dict(
        path=dict(type='str', required=True),
        size=dict(type='str', required=True),
        max=dict(type='str', required=True),
        root_level=dict(type='str', required=False, default=None),
        root_appenders=dict(type='list', elements='str', required=True),
        add_redactor=dict(type='bool', required=False, default=False),
        redactor_refs=dict(type='list', elements='str', required=False),
        redactor_rules=dict(type='str', required=False),
        redactor_policy_refresh_interval=dict(type='str', required=False),
        redactor_logger_names=dict(type='list', elements='str', required=False),
    )

    result = dict(changed=False, message='')
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    if not HAS_YAML:
        module.fail_json(msg="The python PyYAML module is required. Install it with 'pip install PyYAML'")

    path = module.params['path']
    size = module.params['size']
    max_backup = module.params['max']
    root_level = module.params['root_level']
    root_appenders = module.params['root_appenders']

    # New redactor parameters
    add_redactor = module.params['add_redactor']
    redactor_refs = module.params['redactor_refs']
    redactor_rules = module.params['redactor_rules']
    redactor_policy_refresh_interval = module.params['redactor_policy_refresh_interval']
    redactor_logger_names = module.params['redactor_logger_names'] or []

    # Validate parameters when adding redactor
    if add_redactor:
        if not redactor_refs:
            module.fail_json(msg="redactor_refs is required when add_redactor=true", **result)
        if not redactor_rules:
            module.fail_json(msg="redactor_rules is required when add_redactor=true", **result)

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
        max_backup_value = int(max_backup) if max_backup.isdigit() else max_backup
        if appender.get('DefaultRolloverStrategy', {}).get('max') != max_backup_value:
            appender['DefaultRolloverStrategy'] = {'max': max_backup_value}
            changed = True
    # Write back as dict if only one RollingFile appender, else as list
    if rollingfiles:
        data['Configuration']['Appenders']['RollingFile'] = rollingfiles[0] if single_rollingfile and len(rollingfiles) == 1 else rollingfiles

    # Optionally update root logger level and update root logger appenders
    loggers = data['Configuration'].get('Loggers', {})
    redactor_name = 'RedactorAppender'

    if 'Root' in loggers:
        root_logger = loggers['Root']

        # Update level if needed
        if root_level and root_logger.get('level') != root_level:
            root_logger['level'] = root_level
            changed = True

        # Update AppenderRef always
        new_refs = [{'ref': ref} for ref in root_appenders]
        if root_logger.get('AppenderRef', []) != new_refs:
            root_logger['AppenderRef'] = new_refs
            changed = True

        # Add redactor appender to Root if requested
        if add_redactor:
            # Make sure AppenderRef exists and is a list
            if 'AppenderRef' not in root_logger:
                root_logger['AppenderRef'] = []
            elif not isinstance(root_logger['AppenderRef'], list):
                # If it's a single element, convert to list
                root_logger['AppenderRef'] = [root_logger['AppenderRef']]

            # Check if redactor is already in the list
            if not any(ref.get('ref') == redactor_name for ref in root_logger['AppenderRef']):
                root_logger['AppenderRef'].append({'ref': redactor_name})
                changed = True

    # Add or update Rewrite appender with RedactorPolicy if requested
    if add_redactor:
        appenders = data['Configuration']['Appenders']

        # Create the RedactorPolicy configuration
        redactor_policy = {
            'name': 'io.confluent.log4j2.redactor.RedactorPolicy',
            'rules': redactor_rules
        }

        if redactor_policy_refresh_interval:
            redactor_policy['refreshInterval'] = redactor_policy_refresh_interval

        # Create the Rewrite appender config with RedactorPolicy
        rewrite_config = {
            'name': redactor_name,
            'RedactorPolicy': redactor_policy,
            'AppenderRef': [{'ref': ref} for ref in list(set(redactor_refs))]
        }

        # Check if Rewrite appender already exists with exactly the same configuration
        existing_rewrite = appenders.get('Rewrite')
        if existing_rewrite != rewrite_config:
            # If it doesn't exist or is different, update it
            appenders['Rewrite'] = rewrite_config
            changed = True

        # Update specified loggers to include the redactor appender
        if redactor_logger_names:
            # Make sure Loggers section exists and Logger is a list
            if 'Loggers' not in data['Configuration']:
                data['Configuration']['Loggers'] = {}

            if 'Logger' not in data['Configuration']['Loggers']:
                data['Configuration']['Loggers']['Logger'] = []
            elif isinstance(data['Configuration']['Loggers']['Logger'], dict):
                data['Configuration']['Loggers']['Logger'] = [data['Configuration']['Loggers']['Logger']]

            # For each specified logger, ensure it has the redactor appender
            loggers_list = data['Configuration']['Loggers']['Logger']
            for logger_name in redactor_logger_names:
                # Skip 'Root' logger as we've handled it above specifically
                if logger_name == 'Root':
                    continue

                # Find the logger by name (case sensitive match)
                found = False
                for logger in loggers_list:
                    if logger.get('name') == logger_name:
                        found = True
                        # Ensure AppenderRef is a list
                        if 'AppenderRef' not in logger:
                            logger['AppenderRef'] = []
                        elif isinstance(logger['AppenderRef'], dict):
                            logger['AppenderRef'] = [logger['AppenderRef']]

                        # Check if redactor is already in the list
                        if not any(ref.get('ref') == redactor_name for ref in logger['AppenderRef']):
                            logger['AppenderRef'].append({'ref': redactor_name})
                            changed = True
                        break

                # If logger not found, add it (with exact name, preserving case)
                if not found and logger_name != 'Root':
                    new_logger = {
                        'name': logger_name,
                        'level': 'info',  # Default level
                        'additivity': False,
                        'AppenderRef': [{'ref': redactor_name}]
                    }
                    loggers_list.append(new_logger)
                    changed = True

            # If only one logger and it was originally a dict, convert back to dict
            if len(loggers_list) == 1 and isinstance(data['Configuration']['Loggers'].get('Logger', []), dict):
                data['Configuration']['Loggers']['Logger'] = loggers_list[0]

    if changed and not module.check_mode:
        with open(path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

        result['message'] = f"Updated {path}: removed TimeBasedTriggeringPolicy and added/updated SizeBasedTriggeringPolicy for all RollingFile appenders."
        if root_level:
            result['message'] += f" Set root logger level to {root_level}."
        result['message'] += f" Set root logger appenders to {root_appenders}."

        if add_redactor:
            result['message'] += f" Added/updated Rewrite appender '{redactor_name}' with RedactorPolicy and applied to {len(redactor_logger_names)} logger(s)."
    else:
        result['message'] = "No changes needed."

    result['changed'] = changed
    module.exit_json(**result)


if __name__ == '__main__':
    main()
