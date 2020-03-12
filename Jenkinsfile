#!/usr/bin/env groovy

def config = jobConfig {
    nodeLabel = 'docker-oraclejdk8'
    slackChannel = '#ansible-eng'
    timeoutHours = 4
    runMergeCheck = false
}

def job = {
    stage('Install Latest Terraform and Ansible') {
        sh '''
            wget --quiet https://releases.hashicorp.com/terraform/0.12.17/terraform_0.12.17_linux_amd64.zip
            unzip terraform_*.zip
            sudo mv terraform /usr/local/bin/

            sudo pip install --upgrade 'ansible==2.9.*'
        '''
    }

    stage('Set AWS Env Vars') {
        sh '''
            export AWS_IAM=$(curl -s http://169.254.169.254/latest/meta-data/iam/info | grep InstanceProfileArn | cut -d '"' -f 4 | cut -d '/' -f 2)
            export AWS_ACCESS_KEY_ID=$(curl -s http://169.254.169.254/latest/meta-data/iam/security-credentials/$AWS_IAM | grep AccessKeyId | cut -d '"' -f 4)
            export AWS_SECRET_ACCESS_KEY=$(curl -s http://169.254.169.254/latest/meta-data/iam/security-credentials/$AWS_IAM | grep SecretAccessKey | cut -d '"' -f 4)

            if [ -z "$AWS_ACCESS_KEY_ID" ]; then
                echo "Failed to populate environment variables AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_SESSION_TOKEN."
                echo "AWS_IAM is currently $AWS_IAM. Double-check that this is correct. If not, update AWS_IAM env in aws.sh"
                exit 1
            fi

            export AWS_DEFAULT_REGION=us-west-2
        '''
    }

    try {
        stage('Terraform Apply') {
            withCredentials([
                string(credentialsId: 'cp-ansible-aws-vpc-id', variable: 'VPC_ID'),
                string(credentialsId: 'cp-ansible-aws-subnet-id', variable: 'SUBNET_ID')
            ]){
                sh '''
                    # Create SSH keys for terraform/ansible
                    ssh-keygen -b 2048 -t rsa -f "/home/jenkins/.ssh/id_rsa" -q -N ""

                    cd test/terraform
                    terraform init
                    terraform apply --auto-approve -var vpc_id=$VPC_ID -var subnet=$SUBNET_ID
                    cat hosts.yml
                    sleep 60s
                '''
            }
        }

        stage('Generate Certs') {
            sh '''
                cd test/terraform/certs
                chmod +x certs-create.sh
                ./certs-create.sh
            '''
        }

        stage('Provision KDC Server/ Pull Keytabs'){
            sh """
                ansible-playbook -i test/terraform/hosts.yml test/kerberos_server.yml
            """
        }

        stage('SSL Custom Certs/ SASL Kerberos'){
            sh """
                ansible-playbook -i test/terraform/hosts.yml all.yml \
                    -e ssl_enabled=true -e ssl_custom_certs=true -e sasl_protocol=kerberos
            """
        }

    } catch (caughtError) {
        echo "Ansible errored out!"

        try {
            timeout(time: 30, unit: 'MINUTES') {
                userInput = input(message: 'Infrastructure will be destroyed in 6 hours, destroy now instead? (Clicking abort will also destroy now)', ok: 'Destroy it!')
                echo "Destroying Infrastructure then!"
            }
        } catch(err) {
            echo "Reached timeout (or aborted), proceeding with Infrastructure destroy!"
        }

    }

    stage('Destroy Infra'){
        sh '''
            cd test/terraform
            terraform destroy --auto-approve
        '''
    }

}

runJob config, job
