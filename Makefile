# send the makefile to containers
send-mk-b:
	for i in {1..3}; do docker cp Makefile kafka-broker$$i:/; done

send-mk-c:
	for i in {1..5}; do docker cp Makefile controller$$i:/; done

# print meta.properties file
print-meta:
	cat /var/lib/controller/data/meta.properties

# topic
create-topic:
	kafka-topics --create --topic test-topic --bootstrap-server kafka-broker1:9092,kafka-broker2:9092,kafka-broker3:9092 --command-config /etc/kafka/client.properties --replication-factor 1 --partitions 3

# quorum related check commands
leader-check:
	kafka-metadata-quorum --bootstrap-controller controller1:9093,controller2:9093,controller3:9093,controller4:9093,controller5:9093 --command-config /etc/controller/server.properties describe --replication

status-check:
	kafka-metadata-quorum --bootstrap-controller controller1:9093,controller2:9093,controller3:9093,controller4:9093,controller5:9093 --command-config /etc/controller/server.properties describe --status

# check the version of the metadata
metadata-v-check:
	kafka-features --bootstrap-controller controller1:9093,controller2:9093,controller3:9093,controller4:9093,controller5:9093 --command-config /etc/controller/server.properties describe

metadata-v-check-old:
	kafka-features --bootstrap-server kafka-broker1:9092,kafka-broker2:9092,kafka-broker3:9092 --command-config /etc/controller/server.properties describe

# recovery commands
log-length:
	touch /var/lib/controller/data/.lock; kafka-metadata-recovery reconfig log-length --metadata-log-dir /var/lib/controller/data

data-clean:
	rm -rf /var/lib/controller/data

data-clean-b:
	rm -rf /var/lib/kafka/data/__cluster_metadata-0

data-own:
	chown -R cp-kafka:confluent /var/lib/controller/data/

reformat:
	kafka-storage format -t=nUP8evXQS2Ksz6HZRB_Ubw -c /etc/controller/server.properties --initial-controllers 9991@controller1:9093:nUP8evXQS2Ksz6HZRB_Ubw,9992@controller2:9093:nUP8evXQS2Ksz6HZRB_Ubw,9993@controller3:9093:nUP8evXQS2Ksz6HZRB_Ubw,9994@controller4:9093:nUP8evXQS2Ksz6HZRB_Ubw,9995@controller5:9093:nUP8evXQS2Ksz6HZRB_Ubw

format-standalone:
	kafka-storage format -t=nUP8evXQS2Ksz6HZRB_Ubw -c /etc/controller/server.properties --standalone

format-observer:
	kafka-storage format -t=nUP8evXQS2Ksz6HZRB_Ubw -c /etc/controller/server.properties --no-initial-controllers

start-standalone:
	kafka-metadata-recovery reconfig force-standalone --config /etc/controller/server.properties; systemctl restart confluent-kcontroller

join-q:
	kafka-metadata-quorum --bootstrap-controller controller1:9093,controller2:9093,controller3:9093,controller4:9093,controller5:9093 --command-config /etc/controller/server.properties add-controller

leave-q:
	kafka-metadata-quorum --bootstrap-controller controller1:9093,controller2:9093,controller3:9093,controller4:9093,controller5:9093 --command-config /etc/controller/server.properties remove-controller --controller-id 999x --controller-directory-id hello
# systemctl commands
restart-kr:
	systemctl restart confluent-kcontroller

status-kr:
	systemctl status confluent-kcontroller

stop-kr:
	systemctl stop confluent-kcontroller

restart-bk:
	systemctl restart confluent-server

status-bk:
	systemctl status confluent-server

stop-bk:
	systemctl stop confluent-server

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
converge-k45:
	molecule --env-file molecule/kraft.yml converge -s plaintext-basic-rhel -- --limit controller4,controller5 -vvv
converge:
	molecule --env-file molecule/kraft.yml converge -s plaintext-basic-rhel
verify:
	molecule verify -s plaintext-basic-rhel
destroy:
	molecule --env-file molecule/kraft.yml destroy -s plaintext-basic-rhel

# edit molecule file
edit-mole:
	vim molecule/plaintext-basic-rhel/molecule.yml

edit-meta:
	vim roles/kafka_controller/tasks/get_meta_properties.yml

setup:
	sudo yum install -y vim
	grep -qxF 'PATH=/home/ec2-user/.local/bin:$$PATH' ~/.bash_profile || echo 'PATH=/home/ec2-user/.local/bin:$$PATH' >> ~/.bash_profile
	bash -c "source ~/.bash_profile"