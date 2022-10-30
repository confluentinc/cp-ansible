def my_event_handler(event):
    # Do something here
    if event.get('event', None) == 'runner_on_ok':
        print(event.get('event_data').get('res').get('stdout'))
        print(event.get('event_data').get('res').get('ansible_facts'))


if __name__ == "__main__":
    import ansible_runner

    r = ansible_runner.run(
        host_pattern='zookeeper1',
        inventory={
            'all':
                {
                    'vars': {
                        'ansible_connection': 'docker'
                    },

                    'hosts': {'zookeeper1': None,'zookeeper2': None}

                }
        },
        module='service_facts',
        # module_args='whoami',
        event_handler=my_event_handler)

    # print("{}: {}".format(r.status, r.rc))
    # # successful: 0
    # for each_host_event in r.events:
    #     print(each_host_event['event'])
    # print("Final status:")
    # print(r.stats)
