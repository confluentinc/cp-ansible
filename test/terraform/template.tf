locals {
  hosts = <<EOT
all:
  vars:
    rbac_ldap_url: ${aws_instance.kerberos.private_dns}

    kerberos:
      kdc_hostname: ${aws_instance.kerberos.private_dns}
      admin_hostname: ${aws_instance.kerberos.private_dns}

zookeeper:
  vars:
    zookeeper_kerberos_principal: \"zookeeper/{{inventory_hostname}}@{{kerberos.realm | upper}}\"
    zookeeper_kerberos_keytab_path: \"{{inventory_dir}}/keytabs/zookeeper-{{inventory_hostname}}.keytab\"
  hosts:%{ for host in aws_instance.zookeeper.* }
    ${host.private_dns}:
      ansible_ssh_host: ${host.public_dns}%{ endfor }

kafka_broker:
  vars:
    kafka_broker_kerberos_principal: \"{{kerberos_kafka_broker_primary}}/{{inventory_hostname}}@{{kerberos.realm | upper}}\"
    kafka_broker_kerberos_keytab_path: \"{{inventory_dir}}/keytabs/kafka_broker-{{inventory_hostname}}.keytab\"
    ssl_signed_cert_filepath: \"{{inventory_dir}}/certs/kafka_broker.{{inventory_hostname}}-ca1-signed.crt\"
    ssl_key_filepath: \"{{inventory_dir}}/certs/kafka_broker.{{inventory_hostname}}-key.pem\"
    ssl_keystore_filepath: \"{{inventory_dir}}/certs/kafka_broker.{{inventory_hostname}}.keystore.jks\"
  hosts:%{ for host in aws_instance.kafka.* }
    ${host.private_dns}:
      ansible_ssh_host: ${host.public_dns}
      kafka_broker_custom_listeners:
        super:
          hostname: ${host.public_dns}%{ endfor }

schema_registry:
  vars:
    schema_registry_kerberos_principal: \"schema_registry/{{inventory_hostname}}@{{kerberos.realm | upper}}\"
    schema_registry_kerberos_keytab_path: \"{{inventory_dir}}/keytabs/schema_registry-{{inventory_hostname}}.keytab\"
    ssl_signed_cert_filepath: \"{{inventory_dir}}/certs/schema_registry.{{inventory_hostname}}-ca1-signed.crt\"
    ssl_key_filepath: \"{{inventory_dir}}/certs/schema_registry.{{inventory_hostname}}-key.pem\"
    ssl_keystore_filepath: \"{{inventory_dir}}/certs/schema_registry.{{inventory_hostname}}.keystore.jks\"
  hosts:%{ for host in aws_instance.schema_registry.* }
    ${host.private_dns}:
      ansible_ssh_host: ${host.public_dns}%{ endfor }

kafka_rest:
  vars:
    kafka_rest_kerberos_principal: \"kafka_rest/{{inventory_hostname}}@{{kerberos.realm | upper}}\"
    kafka_rest_kerberos_keytab_path: \"{{inventory_dir}}/keytabs/kafka_rest-{{inventory_hostname}}.keytab\"
    ssl_signed_cert_filepath: \"{{inventory_dir}}/certs/kafka_rest.{{inventory_hostname}}-ca1-signed.crt\"
    ssl_key_filepath: \"{{inventory_dir}}/certs/kafka_rest.{{inventory_hostname}}-key.pem\"
    ssl_keystore_filepath: \"{{inventory_dir}}/certs/kafka_rest.{{inventory_hostname}}.keystore.jks\"
  hosts:%{ for host in aws_instance.rest_proxy.* }
    ${host.private_dns}:
      ansible_ssh_host: ${host.public_dns}%{ endfor }

kafka_connect:
  vars:
    kafka_connect_kerberos_principal: \"kafka_connect/{{inventory_hostname}}@{{kerberos.realm | upper}}\"
    kafka_connect_kerberos_keytab_path: \"{{inventory_dir}}/keytabs/kafka_connect-{{inventory_hostname}}.keytab\"
    ssl_signed_cert_filepath: \"{{inventory_dir}}/certs/kafka_connect.{{inventory_hostname}}-ca1-signed.crt\"
    ssl_key_filepath: \"{{inventory_dir}}/certs/kafka_connect.{{inventory_hostname}}-key.pem\"
    ssl_keystore_filepath: \"{{inventory_dir}}/certs/kafka_connect.{{inventory_hostname}}.keystore.jks\"
  hosts:%{ for host in aws_instance.connect.* }
    ${host.private_dns}:
      ansible_ssh_host: ${host.public_dns}%{ endfor }

ksql:
  vars:
    ksql_kerberos_principal: \"ksql/{{inventory_hostname}}@{{kerberos.realm | upper}}\"
    ksql_kerberos_keytab_path: \"{{inventory_dir}}/keytabs/ksql-{{inventory_hostname}}.keytab\"
    ssl_signed_cert_filepath: \"{{inventory_dir}}/certs/ksql.{{inventory_hostname}}-ca1-signed.crt\"
    ssl_key_filepath: \"{{inventory_dir}}/certs/ksql.{{inventory_hostname}}-key.pem\"
    ssl_keystore_filepath: \"{{inventory_dir}}/certs/ksql.{{inventory_hostname}}.keystore.jks\"
  hosts:%{ for host in aws_instance.ksql.* }
    ${host.private_dns}:
      ansible_ssh_host: ${host.public_dns}%{ endfor }

control_center:
  vars:
    control_center_kerberos_principal: \"control_center/{{inventory_hostname}}@{{kerberos.realm | upper}}\"
    control_center_kerberos_keytab_path: \"{{inventory_dir}}/keytabs/control_center-{{inventory_hostname}}.keytab\"
    ssl_signed_cert_filepath: \"{{inventory_dir}}/certs/control_center.{{inventory_hostname}}-ca1-signed.crt\"
    ssl_key_filepath: \"{{inventory_dir}}/certs/control_center.{{inventory_hostname}}-key.pem\"
    ssl_keystore_filepath: \"{{inventory_dir}}/certs/control_center.{{inventory_hostname}}.keystore.jks\"
  hosts:%{ for host in aws_instance.control_center.* }
    ${host.private_dns}:
      ansible_ssh_host: ${host.public_dns}%{ endfor }

kerberos_server:
  hosts:
    ${aws_instance.kerberos.private_dns}:
      ansible_ssh_host: ${aws_instance.kerberos.public_dns}
      realm_name: \"{{ kerberos.realm | upper }}\"

ldap_server:
  hosts:
    ${aws_instance.kerberos.private_dns}:
      ansible_ssh_host: ${aws_instance.kerberos.public_dns}
EOT
}

resource "null_resource" "hosts_provisioner" {
  provisioner "local-exec" {
    command = "echo \"${local.hosts}\" > hosts.yml"
  }
}

locals {
  cert_hosts = <<EOT
%{ for host in aws_instance.kafka.* }kafka_broker:${host.private_dns}:${host.public_dns}
%{ endfor }%{ for host in aws_instance.schema_registry.* }schema_registry:${host.private_dns}:${host.public_dns}
%{ endfor }%{ for host in aws_instance.rest_proxy.* }kafka_rest:${host.private_dns}:${host.public_dns}
%{ endfor }%{ for host in aws_instance.connect.* }kafka_connect:${host.private_dns}:${host.public_dns}
%{ endfor }%{ for host in aws_instance.ksql.* }ksql:${host.private_dns}:${host.public_dns}
%{ endfor }%{ for host in aws_instance.control_center.* }control_center:${host.private_dns}:${host.public_dns}
%{ endfor }
EOT
}

resource "null_resource" "cert_hosts_provisioner" {
  provisioner "local-exec" {
    command = "echo \"${local.cert_hosts}\" > certs/hosts"
  }
}
