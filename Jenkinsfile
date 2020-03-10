#!/usr/bin/env groovy

def config = jobConfig {
    nodeLabel = 'docker-oraclejdk8'
    slackChannel = '#ansible-eng'
    timeoutHours = 4
    runMergeCheck = false
}

def job = {
    stage("Trigger Master Pipeline with Git Info") {

        GIT_COMMIT = sh (
            script: 'git rev-parse --short HEAD',
            returnStdout: true
        ).trim()

        echo "Git committer: ${GIT_COMMIT}"

        build job: 'Jenkins/ansible-dom-test', parameters: [string(name:'GIT_COMMIT_HASH', value: "${GIT_COMMIT}")]
    }
}

runJob config, job
