#!/usr/bin/python

# Copyright: (c) 2019, Confluent Inc

from __future__ import (absolute_import, division, print_function)

ANSIBLE_METADATA = {
    'metadata_version': '0.91',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: kafka_connectors

short_description: This module allows setting up Kafka connectors from Ansible.

version_added: "2.9.0"

description:
    - "This module allows setting up Kafka connectors from Ansible. It registers the new ones,
    updates the existing ones and removes the deleted ones."

options:
    connect_url:
        type: str
        description:
            - URL of the Connect REST server to use to add/edit connectors
        required: true
    active_connectors:
        type: list
        elements: dict
        description:
            - Dict of active connectors (each connector object must have a 'name' and a 'config' field)
        required: true

author:
    - Laurent Domenech-Cabaud (@ldom)
'''

EXAMPLES = '''
- name: Deploy Some connector
  connect_url: kafka_connect_http_protocol://0.0.0.0:kafka_connect_rest_port/connectors
  active_connectors: [{"name": "test-6-sink", "config": { .../... }},{"name": "test-5-sink", "config": { .../... }}]
'''

RETURN = '''
message:
    description: The output message that the module generates
    type: str
    returned: always
'''

import json
import time

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import open_url
import ansible.module_utils.six.moves.urllib.error as urllib_error
__metaclass__ = type

RUNNING_STATE = "RUNNING"
WAIT_TIME_BEFORE_GET_STATUS = 1  # seconds
TIMEOUT_WAITING_FOR_TASK_STATUS = 30  # seconds


def get_current_connectors(connect_url):
    try:
        res = open_url(connect_url, validate_certs=False)
        return json.loads(res.read())
    except urllib_error.HTTPError as e:
        if e.code != 404:
            raise
        return []


def remove_connector(connect_url, name):
    url = "{}/{}".format(connect_url, name)
    r = open_url(method='DELETE', url=url, validate_certs=False)
    return r.getcode() == 200


# return value: success (bool), changed (bool), message (str)
def create_new_connector(connect_url, name, config):
    data = json.dumps({'name': name, 'config': config})
    headers = {'Content-Type': 'application/json'}
    try:
        r = open_url(method='POST', url=connect_url, data=data, headers=headers, validate_certs=False)
    except urllib_error.HTTPError as e:
        message = "error while adding new connector configuration ({})".format(e)
        return False, False, message

    success = r.getcode() in (200, 201, 409)
    changed = True
    message = "new connector added"

    is_running, failures_msg = get_connector_status(connect_url, name)
    if not is_running:
        success = False
        message = failures_msg

    return success, changed, message


# truncates to 200 chars or the first line feed
def truncate_error_message(message):
    lines = message.splitlines()
    if lines:
        return lines[0][0:200]
    return message[0:200]


# to be successful, the connector and all its tasks must be running
# if anything fails, we fail and return the associated error messages
def get_connector_status(connect_url, connector_name):
    time.sleep(WAIT_TIME_BEFORE_GET_STATUS)
    status_url = "{}/{}/status".format(connect_url, connector_name)

    res = open_url(status_url, validate_certs=False)
    current_status = json.loads(res.read())

    connector_status = current_status['connector']['state']

    failures = []
    if connector_status != RUNNING_STATE:
        failures.append("connector state paused or failed")

    nb_tasks = len(current_status['tasks'])
    time_waited = 0
    while not nb_tasks:
        time_waited += 1
        time.sleep(1)
        if time_waited > TIMEOUT_WAITING_FOR_TASK_STATUS:
            return False, "timeout getting task status"

        res = open_url(status_url, validate_certs=False)
        current_status = json.loads(res.read())
        nb_tasks = len(current_status['tasks'])

    for task in current_status['tasks']:
        if task['state'] != RUNNING_STATE:
            failures.append("task {}: {}".format(task['id'], truncate_error_message(task.get('trace'))))

    if failures:
        return False, ", ".join(failures)

    return True, None


# return value: success (bool), changed (bool), message (str)
def update_existing_connector(connect_url, name, config):
    url = "{}/{}/config".format(connect_url, name)
    restart_url = "{}/{}/restart".format(connect_url, name)

    res = open_url(url, validate_certs=False)
    current_config = json.loads(res.read())

    existing_config = config.copy()
    existing_config.update({'name': name})

    if current_config == existing_config:
        return True, False, "no configuration change"

    success = True
    message = ""

    # configuration has changed, let's update it

    data = json.dumps(config)
    headers = {'Content-Type': 'application/json'}
    r = None
    try:
        r = open_url(method='PUT', url=url, data=data, headers=headers, validate_certs=False)
    except urllib_error.HTTPError as e:
        message = "error while updating configuration ({})".format(e)
        success = False
    finally:
        changed = r is not None and r.getcode() in (200, 201)

    if not success:
        return success, changed, message

    # configuration was updated, let's restart the connector

    message = "connector configuration updated"
    success = True
    try:
        r = open_url(method='POST', url=restart_url, validate_certs=False)
    except urllib_error.HTTPError:
        pass
    finally:
        if r.getcode() not in (200, 204, 409):
            success = False
            message = "connector configuration updated but failed to restart " \
                      "after a configuration update. {}".format(r.msg)

    # get the connector's status
    # if failed, return it
    # if there's a rebalance, wait for it to finish? how?
    is_running, failures_msg = get_connector_status(connect_url, name)
    if not is_running:
        success = False
        message = failures_msg

    return success, changed, message


def format_output(connector_name, success, message):
    if not success:
        return "{}: ERROR {}".format(connector_name, message)
    else:
        return "{}: {}".format(connector_name, message)


def run_module():
    module_args = dict(
        connect_url=dict(type='str', required=True),
        active_connectors=dict(type='list', elements='dict', required=True),
    )

    result = dict(changed=False, message='')

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    if module.check_mode:
        module.exit_json(**result)

    #
    # module action:
    # - make a diff of existing (current) vs kept (active) connectors and removes the un-kept ones
    # - update the connector if it already exists, otherwise create a new one
    #
    # note: using the logic below because PUT /connectors/<name>/config has proven to be unreliable
    # when the connector doesn't exist
    #
    result['changed'] = False
    connector_failure = False
    output_messages = []
    added_updated_messages = []
    try:
        current_connector_names = get_current_connectors(connect_url=module.params['connect_url'])
        active_connector_names = (c['name'] for c in module.params['active_connectors'])
        deleted_connector_names = set(current_connector_names) - set(active_connector_names)

        for to_delete in deleted_connector_names:
            remove_connector(connect_url=module.params['connect_url'], name=to_delete)

        if deleted_connector_names:
            output_messages.append("Connectors removed: {}.".format(', '.join(deleted_connector_names)))

        active_connectors = module.params['active_connectors']

        for connector in active_connectors:
            try:
                _unused = current_connector_names.index(connector['name'])

                success, changed, message = update_existing_connector(
                    connect_url=module.params['connect_url'],
                    name=connector['name'],
                    config=connector['config']
                )
            except ValueError:
                success, changed, message = create_new_connector(
                    connect_url=module.params['connect_url'],
                    name=connector['name'],
                    config=connector['config']
                )

            if changed:  # one connector changed is enough
                result['changed'] = True

            if not success:
                connector_failure = True

            added_updated_messages.append(format_output(connector['name'], success, message))

        output_messages.append("Connectors added or updated: {}.".format(', '.join(added_updated_messages)))
        result['message'] = " ".join(output_messages)

        if connector_failure:
            module.fail_json(msg='An error occurred while running the module', **result)

    except Exception as e:
        result['message'] = str(e)

        module.fail_json(msg='An error occurred while running the module', **result)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
