#!/usr/bin/env groovy

def config = jobConfig {
    nodeLabel = 'docker-debian-jdk8'
    slackChannel = '#ansible-eng'
    timeoutHours = 4
    runMergeCheck = false
}

def job = {
    withDockerServer([uri: dockerHost()]) {
        stage('Plaintext') {
            sh '''
                cd roles/confluent.test
                molecule test -s plaintext-rhel
            '''
        }
    }
}

runJob config, job
