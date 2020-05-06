#!/usr/bin/env groovy

def config = jobConfig {
    nodeLabel = 'docker-oraclejdk8'
    slackChannel = '#ansible-eng'
    timeoutHours = 4
    runMergeCheck = false
}

def job = {
    stage('Install Molecule and Latest Ansible') {
        sh '''
            sudo pip install --upgrade 'ansible==2.9.*'
            sudo pip install molecule docker
        '''
    }

    withDockerServer([uri: dockerHost()]) {
        stage('RBAC - Scram - Custom Certs - RHEL') {
            sh '''
                docker rmi molecule_local/geerlingguy/docker-centos7-ansible || true

                cd roles/confluent.test
                molecule test -s rbac-scram-custom-rhel
            '''
        }
    }
}

runJob config, job
