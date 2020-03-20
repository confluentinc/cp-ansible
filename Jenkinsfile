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
    stage('Run Integration Tests') {
        withDockerServer([uri: dockerHost()]) {
            parallel {
                stage('Run C3 Tests') {
                    sh '''
                        cd roles/confluent.control_center
                        molecule test --all
                    '''
                }
                stage('Run Common Tests') {
                    sh '''
                        cd roles/confluent.commom
                        molecule test --all
                    '''
                }
            }
        }
    }
}

runJob config, job
