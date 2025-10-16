leader-check:
	kafka-metadata-quorum --bootstrap-controller controller1:9093 --command-config /etc/controller/server.properties describe --replication

leader-check-2:
	kafka-metadata-quorum --bootstrap-controller controller2:9093 --command-config /etc/controller/server.properties describe --replication

leader-check-3:
	kafka-metadata-quorum --bootstrap-controller controller3:9093 --command-config /etc/controller/server.properties describe --replication

metadata-v-check:
	kafka-features --bootstrap-controller controller1:9093 --command-config /etc/controller/server.properties describe

metadata-v-check-old:
	kafka-features --bootstrap-server kafka-broker1:9092 --command-config /etc/controller/server.properties describe

start-standalone:
	kafka-metadata-recovery reconfig force-standalone --config /etc/controller/secret.properties

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

converge:
	molecule --env-file molecule/kraft.yml converge -s plaintext-basic-rhel
verify:
	molecule verify -s plaintext-basic-rhel