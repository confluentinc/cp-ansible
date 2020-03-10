#!/usr/bin/env groovy

def config = jobConfig {
    nodeLabel = 'docker-oraclejdk8'
    slackChannel = '#ansible-eng'
    timeoutHours = 4
    runMergeCheck = false
}

def job = {
    stage("Access to git url?") {
        echo "Running unit and integration tests"
        sh "env"
        sh "pwd"
        sh "git branch"
        sh "git log"



    }
}

runJob config, job
