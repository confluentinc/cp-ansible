    #!/usr/bin/python

# Copyright: (c) 2019, Confluent Inc

ANSIBLE_METADATA = {
    'metadata_version': '0.9',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: confluent_connector_reset

short_description: This module allows resetting connector offsets when deleted as described here:
https://rmoff.net/2019/08/15/reset-kafka-connect-source-connector-offsets/

version_added: "2.4"

description:
    - "This module creates a tombstone message for connectors that have been deleted.
    This allows them to start from scratch if they are re-created with the same name."

options:
    broker_url:
        description:
            - URL of a broker from the cluster
        required: true
    deleted_connector_name:
        description:
            - name of the deleted connector (to write a tombstone message for)
        required: true
    offset_storage_topic:
        description:
            - name of the topic used to store connector offsets
        required: true


author:
    - Laurent Domenech-Cabaud (@ldom)
'''

EXAMPLES = '''
- name: Write tombstone messages
  confluent_connector_reset:
    broker_url: {{kafka_broker.hosts[0]}}:{{kafka_broker_listeners.external.port}}
    deleted_connector_name: {{item.value}}
    {{kafka_connect.properties['offset.storage.topic']}}
  loop: "{{ connectors.deleted_connector_names|dict2items }}"
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

from tombstone_msg import create_tombstone_msg


def run_module():
    module_args = dict(
        broker_url=dict(type='str', required=True),
        deleted_connector_name=dict(type='str', required=True),
        offset_storage_topic=dict(type='str', required=True),
    )

    result = dict(changed=False, message='')

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)

    if module.check_mode:
        module.exit_json(**result)

    #
    # module action: calls tombstone_msg.create_tombstone_msg()
    #
    output_messages = []
    try:
        msgs_written = create_tombstone_msg(
            kafka_url=module.params['broker_url'],
            connector_name=module.params['deleted_connector_name'],
            offset_storage_topic=module.params['offset_storage_topic'],
        )
        result['message'] = ", ".join(msgs_written)

    except Exception as e:
        result['message'] = str(e)
        module.fail_json(msg='An error occurred while running the module', **result)

    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
