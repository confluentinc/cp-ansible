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
            sudo pip install molecule docker virtualenv
            cd roles/confluent.test
            virtualenv virtenv
        '''
    }

    withDockerServer([uri: dockerHost()]) {
        stage('RBAC - Scram - Custom Certs - RHEL') {
            // TODO investigate parallelizing this
            // TODO might need to delete docker image before starting run
            sh '''
                docker rmi molecule_local/geerlingguy/docker-centos7-ansible || true
                docker rmi molecule_local/geerlingguy/docker-debian9-ansible || true
                docker rmi molecule_local/geerlingguy/docker-ubuntu1804-ansible || true

                cd roles/confluent.test
                . virtenv/bin/activate
                molecule test -s rbac-scram-custom-rhel
            '''
        }
        stage('RBAC - mTLS - Provided Keystores - Ubuntu') {
            sh '''
                cd roles/confluent.test
                . virtenv/bin/activate
                molecule test -s rbac-mtls-provided-ubuntu
            '''
        }
        stage('RBAC - Kerberos - no SSL - Debian') {
            sh '''
                cd roles/confluent.test
                . virtenv/bin/activate
                molecule test -s rbac-kerberos-debian
            '''
        }
    }
}

runJob config, job
