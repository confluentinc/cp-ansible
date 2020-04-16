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
        stage('RBAC - mTLS') {
            // TODO investigate parallelizing this
            // TODO might need to delete docker image before starting run
            sh '''
                docker rmi molecule_local/geerlingguy/docker-centos7-ansible || true
                cd roles/confluent.test
                molecule test -s default
            '''
        }
        stage('RBAC - Scram - 1way SSL w Custom Certs') {
            sh '''
                cd roles/confluent.test
                molecule test -s rbac-scram-custom-1way
            '''
        }
        stage('RBAC - Kerberos - no SSL') {
            sh '''
                cd roles/confluent.test
                molecule test -s rbac-kerberos-no-ssl
            '''
        }
    }
}

runJob config, job
