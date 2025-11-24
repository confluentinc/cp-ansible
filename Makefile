# send the makefile to containers
send-mk-b:
	docker cp Makefile kafka-broker1:/

send-mk-c:
	docker cp Makefile controller1:/

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
	molecule converge -s aprf-fips
verify:
	molecule verify -s aprf-fips
destroy:
	molecule destroy -s aprf-fips

# edit molecule file
edit-mole:
	vim molecule/aprf-fips/molecule.yml

setup:
	sudo yum install -y vim
	grep -qxF 'PATH=/home/ec2-user/.local/bin:$$PATH' ~/.bash_profile || echo 'PATH=/home/ec2-user/.local/bin:$$PATH' >> ~/.bash_profile
	bash -c "source ~/.bash_profile"