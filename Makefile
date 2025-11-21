# send the makefile to containers
send-mk-b:
	for i in {1..3}; do docker cp Makefile kafka-broker$$i:/; done

send-mk-c:
	for i in {1..5}; do docker cp Makefile controller$$i:/; done

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
go-c1:
	docker exec -it controller1 bash

# molecule commands
converge:
	molecule converge -s plaintext-basic-rhel
verify:
	molecule verify -s plaintext-basic-rhel
destroy:
	molecule destroy -s plaintext-basic-rhel

# edit molecule file
edit-mole:
	vim molecule/archive-plain-rhel-fips/molecule.yml

setup:
	sudo yum install -y vim
	grep -qxF 'PATH=/home/ec2-user/.local/bin:$$PATH' ~/.bash_profile || echo 'PATH=/home/ec2-user/.local/bin:$$PATH' >> ~/.bash_profile
	bash -c "source ~/.bash_profile"