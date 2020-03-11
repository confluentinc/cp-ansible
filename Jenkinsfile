#!/usr/bin/env groovy

def config = jobConfig {
    nodeLabel = 'docker-oraclejdk8'
    slackChannel = '#ansible-eng'
    timeoutHours = 4
    runMergeCheck = false
}

def job = {
    stage("Hello world") {
        echo "NON confluent engineer"
        sh "env"
    }
}

runJob config, job
