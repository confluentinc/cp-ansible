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
            - When enabled, uses 1-to-1 mapping between redactor_logger_names and redactor_refs.
            - Each logger in redactor_logger_names[i] will have redactor_refs[i] removed from its AppenderRef and replaced with RedactorAppender.
    redactor_refs:
        type: list
        elements: str
        required: false
        description:
            - List of appender names the RedactorAppender should reference.
            - Must have the same length as redactor_logger_names for 1-to-1 mapping.
            - redactor_logger_names[i] will have redactor_refs[i] removed from its AppenderRef.
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
      - ConnectAppender
      - STDOUT
    add_redactor: true
    redactor_refs:
      - ConnectAppender
      - FileAppender
    redactor_rules: /etc/kafka/redactor-rules.json
    redactor_logger_names:
      - Root
      - org.apache.kafka
# Result: 1-to-1 mapping
# Root logger: ConnectAppender removed, gets [STDOUT, RedactorAppender]
# org.apache.kafka logger: FileAppender removed, gets [RedactorAppender] + any existing non-FileAppender refs
# RedactorAppender handles both ConnectAppender and FileAppender with redaction
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

import os
from ansible.module_utils.basic import AnsibleModule
try:
    import yaml
except ImportError:
    HAS_YAML = False
else:
    HAS_YAML = True


def update_logger_appender_refs(logger, logger_redacted_appender, redactor_name):
    """
    Update a logger's AppenderRef list by removing the redacted appender and adding the redactor appender.

    Args:
        logger: The logger dictionary to update
        logger_redacted_appender: The appender to remove from this logger
        redactor_name: The redactor appender name to add

    Returns:
        bool: True if the logger was changed, False otherwise
    """
    # Ensure AppenderRef is a list
    if 'AppenderRef' not in logger:
        logger['AppenderRef'] = []
    elif isinstance(logger['AppenderRef'], dict):
        logger['AppenderRef'] = [logger['AppenderRef']]

    # Remove this logger's specific redacted appender and add redactor appender
    current_refs = [ref.get('ref') for ref in logger['AppenderRef']]
    # Keep only appenders that are NOT this logger's redacted appender
    filtered_refs = [ref for ref in current_refs if ref != logger_redacted_appender]
    # Add redactor if not already present
    if redactor_name not in filtered_refs:
        filtered_refs.append(redactor_name)

    # Update AppenderRef if changed
    new_refs = [{'ref': ref} for ref in filtered_refs]
    if logger['AppenderRef'] != new_refs:
        logger['AppenderRef'] = new_refs
        return True
    return False


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
        module.fail_json(msg="The python PyYAML module is required on Target nodes. Install it with 'pip install PyYAML'")

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
        if not redactor_logger_names:
            module.fail_json(msg="redactor_logger_names is required when add_redactor=true", **result)
        if len(redactor_refs) != len(redactor_logger_names):
            module.fail_json(msg=f"number of appenderRefs ({len(redactor_refs)}) and logger_name ({len(redactor_logger_names)}) must be equal", **result)

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

        # Only update root logger appenders if redactor is NOT enabled
        # If redactor is enabled, root logger will be handled in the redactor logger loop
        if not add_redactor:
            # Update AppenderRef
            new_refs = [{'ref': ref} for ref in root_appenders]
            if root_logger.get('AppenderRef', []) != new_refs:
                root_logger['AppenderRef'] = new_refs
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
            for i, logger_name in enumerate(redactor_logger_names):
                # Get the corresponding appender for this logger
                logger_redacted_appender = redactor_refs[i]

                # Handle Root logger specially
                if logger_name == 'Root':
                    root_logger = data['Configuration']['Loggers']['Root']
                    # Update the root logger's appender references
                    if update_logger_appender_refs(root_logger, logger_redacted_appender, redactor_name):
                        changed = True
                    continue

                # Find the logger by name (case sensitive match)
                found = False
                for logger in loggers_list:
                    if logger.get('name') == logger_name:
                        found = True
                        # Update the logger's appender references
                        if update_logger_appender_refs(logger, logger_redacted_appender, redactor_name):
                            changed = True
                        break

                # If logger not found, add it (with exact name, preserving case)
                if not found:
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

        # Update message for root logger appenders
        if not add_redactor:
            result['message'] += f" Set root logger appenders to {root_appenders}."

        if add_redactor:
            result['message'] += f" Added/updated Rewrite appender '{redactor_name}', referencing {redactor_refs} to {len(redactor_logger_names)} logger(s)."
    else:
        result['message'] = "No changes needed."

    result['changed'] = changed
    module.exit_json(**result)


if __name__ == '__main__':
    main()
