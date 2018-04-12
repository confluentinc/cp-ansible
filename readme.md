# Introduction 

Ansible playbooks for installing the [Confluent Platform](http://www.confluent.io).

## Examples

PLAINTEXT, SSL, SASL_SSL each have example playbooks and hosts files in their respective `plaintext`, `ssl`, sasl_ssl` directories

## Running

### Check for Changes

```bash
ansible-playbook --check -i hosts.yml all.yaml
```

### Apply Changes

```bash
ansible-playbook -i hosts.yml all.yaml
```

```yaml
# service, user
#confluent-schema-registry, cp-schema-registry
#confluent-kafka-rest, cp-kafka-rest
#confluent-control-center, cp-control-center
#confluent-kafka-connect, cp-kafka-connect
#confluent-kafka, cp-kafka
#confluent-zookeeper, cp-kafka   <-- Take note!
#confluent-ksql, cp-ksql
```
