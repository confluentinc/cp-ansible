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

        echo "Git commit: ${GIT_COMMIT}"

        build job: '/ansible-dom-master', parameters: [
                        string(name: 'BRANCH_OR_COMMIT', value: "commit"),
                        string(name: 'GIT_COMMIT_HASH', value: GIT_COMMIT),
                        string(name: 'QUICK_OR_FULL', value: "quick")
                    ]
    }
}

runJob config, job
