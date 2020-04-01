# Description

This PR allows the user to skip the plays that copies the CA, cert and key.

Relevant when these are provided by other sources, for example another Ansible playbook.

Also allows import of a full CA chain into truststores.

## Type of change

- [ ] Bug fix (non-breaking change which fixes an issue)
- [X] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] This change requires a documentation update

# How Has This Been Tested?

Was tested on a 3 broker, 3 zookeeper cluster. Running common, kafka_broker, kafka_connect, kafka_rest, ksql, schema_registry and zookeeper roles. 

All nodes running CentOS Linux release 7.7.1908 (Core)

added the following in `/inventory/group_vars/all.yml` instead of `hosts.yml` since I have myltiple inventories.

```
ssl_custom_certs_skip_copy: true
ssl_add_ca_chain: true
```



# Checklist:

- [ ] My code follows the style guidelines of this project *(didn't find any style guide)*
- [x] I have performed a self-review of my own code
- [x] I have commented my code, particularly in hard-to-understand areas
- [x] I have made corresponding changes to the documentation
- [x] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [x] Any dependent changes have been merged and published in downstream modules (no dependencies)
