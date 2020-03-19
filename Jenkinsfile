#!/usr/bin/env groovy

def config = jobConfig {
    nodeLabel = 'docker-oraclejdk8'
    slackChannel = '#ansible-eng'
    timeoutHours = 4
    runMergeCheck = false
}

def job = {
    stage("Hello world") {
        echo "Running unit and integration tests"
        sh "env"
    }
}

runJob config, job
