#!/usr/bin/python
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
# Make coding more python3-ish

from __future__ import (absolute_import, division, print_function)

ANSIBLE_METADATA = {
    'metadata_version': '0.9',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: kafka_connectors

short_description: This module allows setting up Kafka connectors from Ansible.

version_added: "7.0.0"

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

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import open_url
import ansible.module_utils.six.moves.urllib.error as urllib_error
__metaclass__ = type


def get_current_connectors(connect_url):
    try:
        res = open_url(connect_url)
        return json.loads(res.read())
    except urllib_error.HTTPError as e:
        if e.code != 404:
            raise
        return []


def remove_connector(connect_url, name):
    url = "{}/{}".format(connect_url, name)
    r = open_url(method='DELETE', url=url)
    return r.getcode() == 200


def create_new_connector(connect_url, name, config):
    data = json.dumps({'name': name, 'config': config})
    headers = {'Content-Type': 'application/json'}
    r = open_url(method='POST', url=connect_url, data=data, headers=headers)
    return r.getcode() in (200, 201, 409)


def update_existing_connector(connect_url, name, config):
    url = "{}/{}/config".format(connect_url, name)
    restart_url = "{}/{}/restart".format(connect_url, name)

    res = open_url(url)
    current_config = json.loads(res.read())

    existing_config = config.copy()
    existing_config.update({'name': name})

    if current_config == existing_config:
        return False

    data = json.dumps(config)
    headers = {'Content-Type': 'application/json'}
    r = open_url(method='PUT', url=url, data=data, headers=headers)

    changed = r.getcode() in (200, 201, 409)

    r = open_url(method='POST', url=restart_url)
    if r.getcode() not in (200, 204, 409):
        raise Exception("Connector {} failed to restart after a configuration update. {}".format(name, r.msg))

    return changed


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
    output_messages = []
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

                changed = update_existing_connector(
                    connect_url=module.params['connect_url'],
                    name=connector['name'],
                    config=connector['config']
                )
                if changed:
                    output_messages.append("Connector {} updated.".format(connector['name']))

                result['changed'] = changed

            except ValueError:
                result['changed'] = create_new_connector(
                    connect_url=module.params['connect_url'],
                    name=connector['name'],
                    config=connector['config'])
                output_messages.append("New connector {} created.".format(connector['name']))

        result['message'] = " ".join(output_messages)

    except Exception as e:
        result['message'] = str(e)
        module.fail_json(msg='An error occurred while running the module', **result)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
