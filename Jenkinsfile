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
        stage('Plaintext - RHEL') {
            sh '''
                cd roles/confluent.test
                molecule test -s plaintext-rhel
            '''
        }
    }
}

runJob config, job
