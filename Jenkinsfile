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
        stage('Run Integration Tests') {
            parallel (
                'common': {
                    sh '''
                        cd roles/confluent.commom
                        molecule test --all
                    '''
                },
                'c3': {
                    sh '''
                        cd roles/confluent.control_center
                        molecule test --all
                    '''
                }
            )
        }
    }

}

runJob config, job
