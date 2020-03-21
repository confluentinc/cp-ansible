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
            // TODO investigate parallelizing this
            // TODO might need to delete docker image before starting run
            // docker rmi molecule_local/geerlingguy/docker-centos7-ansible
            sh '''
                cd roles/confluent.control_center
                molecule test --all
            '''
        }
    }

}

runJob config, job
