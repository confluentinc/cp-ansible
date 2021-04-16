# Contributing to CP-Ansible

Thank you for your interest in contributing to the CP-Ansible project.

Before contributing any changes, we would ask that you open an issue on github and discuss with the wider community the changes being made.

While we appreciate all code changes submitted, please understand that some PR's may not be committed for a variety of reasons.  We will do our best to explain why a PR cannot be merged when closing the request.

#### Table Of Contents

[Code of Conduct](#code-of-conduct)

[How to ask questions](#how-to-ask-questions)

[How to file a bug](#how-to-file-a-bug)

[How to file a feature request](#how-to-file-a-feature-request)

[How to test](#how-to-test)

[How to file a pull request](#how-to-file-a-pull-request)


## Code of Conduct

This project and everyone participating in it is governed by the [CP-Ansible Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to [support@confluent.io](mailto:support@confluent.io).

## How to ask questions

You can ask questions via two methods:

1. You can open an issue on the project itself, here on github, which will be answered on a best effort basis:

    ```https://github.com/confluentinc/cp-ansible/issues/new```

    Please be sure to tag the post as a `question`.


2. For Confluent Enterprise Support customers, we would strongly advise you to open a Support ticket which will be addressed within your Support contract SLA:

    ```https://support.confluent.io```


## How to file a bug

You can file bugs via two methods:

1. You can open an issue on the project itself, here on github, which will be answered on a best effort basis:

    ```https://github.com/confluentinc/cp-ansible/issues/new```

    Please be sure to tag the post as a `bug`.

2. For Confluent Enterprise Support customers, we would strongly adivse you to open a Support ticket which will be addressed within your Support contract SLA:

    ```https://support.confluent.io```

    Please include the following on all bug reports:

* Use a clear and descriptive title for the issue to identify the problem.

* Describe the exact steps which reproduce the problem in as many details as possible. For example, run the Ansible playbook with the `-vvv` switch and pipe the output to a file.  Provide a link to the file

* Provide specific examples to demonstrate the steps. Include links to files or GitHub projects, or copy/pasteable snippets, which you use in those examples. If you're providing snippets in the issue, use Markdown code blocks.

* Any changes which have been made to the playbooks or environments (please be as specific as possible).

* Explain which behavior you expected to see instead and why.

## How to file a feature request

1. You can open an issue on the project itself, here on github, which will be answered on a best effort basis:

    ```https://github.com/confluentinc/cp-ansible/issues/new```

Please be sure to tag the post as a `enhancement`.

2. For Confluent Enterprise Support customers, we would strongly adivse you to open a Support ticket which will be addressed within your Support contract SLA:

    ```https://support.confluent.io```

Please include the following on all enhancement requests:

* Use a clear and descriptive title for the issue to identify the problem.

* Provide a step-by-step description of the suggested enhancement in as many details as possible.

* Provide specific examples to demonstrate the steps. Include copy/pasteable snippets which you use in those examples, as Markdown code blocks.

* Describe the current behavior and explain which behavior you expected to see instead and why.

## How to file a Pull Request

The process described here has several goals:

* Maintain CP-Ansible's quality
* Fix problems that are important to users
* Engage the community in working toward the best possible CP-Ansible
* Enable a sustainable system for CP-Ansible's maintainers to review contributions

Please follow these steps to have your contribution considered by the maintainers:

1. Follow all instructions in [the template](PULL_REQUEST_TEMPLATE.md)
2. Make sure you have reviewed [How to test](HOW_TO_TEST.md) and our [Development Guide](DEVELOPMENT_GUIDE.md)
3. Follow the styleguides
4. After you submit your pull request, verify that all status checks are passing

While the prerequisites above must be satisfied prior to having your pull request reviewed, the reviewer(s) may ask you to complete additional design work, tests, or other changes before your pull request can be ultimately accepted.


## Style guide

Git Commit Messages

* Use the present tense ("Add feature" not "Added feature")
* Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
* Limit the first line to 72 characters or less
* Reference issues and pull requests liberally after the first line
