# quorum related check commands
leader-check:
	kafka-metadata-quorum --bootstrap-controller controller1:9093 --command-config /etc/controller/server.properties describe --replication

status-check:
	kafka-metadata-quorum --bootstrap-controller controller1:9093 --command-config /etc/controller/server.properties describe --status

leader-check-2:
	kafka-metadata-quorum --bootstrap-controller controller2:9093 --command-config /etc/controller/server.properties describe --replication

status-check-2:
	kafka-metadata-quorum --bootstrap-controller controller2:9093 --command-config /etc/controller/server.properties describe --status

leader-check-3:
	kafka-metadata-quorum --bootstrap-controller controller3:9093 --command-config /etc/controller/server.properties describe --replication

status-check-3:
	kafka-metadata-quorum --bootstrap-controller controller3:9093 --command-config /etc/controller/server.properties describe --status

leader-check-4:
	kafka-metadata-quorum --bootstrap-controller controller4:9093 --command-config /etc/controller/server.properties describe --replication

status-check-4:
	kafka-metadata-quorum --bootstrap-controller controller4:9093 --command-config /etc/controller/server.properties describe --status

leader-check-5:
	kafka-metadata-quorum --bootstrap-controller controller5:9093 --command-config /etc/controller/server.properties describe --replication

status-check-5:
	kafka-metadata-quorum --bootstrap-controller controller5:9093 --command-config /etc/controller/server.properties describe --status

# check the version of the metadata
metadata-v-check:
	kafka-features --bootstrap-controller controller1:9093 --command-config /etc/controller/server.properties describe

metadata-v-check-old:
	kafka-features --bootstrap-server kafka-broker1:9092 --command-config /etc/controller/server.properties describe

# recovery commands
start-standalone:
	kafka-metadata-recovery reconfig force-standalone --config /etc/controller/secret.properties

join-q:
	kafka-metadata-quorum --bootstrap-controller controller1:9093 --command-config /etc/controller/server.properties add-controller

# systemctl commands
restart-kr:
	systemctl restart confluent-kcontroller

status-kr:
	systemctl status confluent-kcontroller

restart-bk:
	systemctl restart confluent-server

status-bk:
	systemctl status confluent-server

# docker commands
go-b1:
	docker exec -it kafka-broker1 bash
go-b2:
	docker exec -it kafka-broker2 bash
go-b3:
	docker exec -it kafka-broker3 bash
go-c1:
	docker exec -it controller1 bash
go-c2:
	docker exec -it controller2 bash
go-c3:
	docker exec -it controller3 bash
go-c4:
	docker exec -it controller4 bash
go-c5:
	docker exec -it controller5 bash

# molecule commands
converge:
	molecule --env-file molecule/kraft.yml converge -s plaintext-basic-rhel
verify:
	molecule verify -s plaintext-basic-rhel
destroy:
	molecule destroy -s plaintext-basic-rhel

# edit molecule file
edit-m:
	vim molecule/plaintext-basic-rhel/molecule.yml
