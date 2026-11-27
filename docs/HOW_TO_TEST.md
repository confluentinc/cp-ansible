# How to test

CP-Ansible is tested with [Molecule](https://molecule.readthedocs.io/en/latest/). Each Molecule scenario builds a real Confluent Platform cluster in Docker containers and runs CP-Ansible against it, then checks the result.

## Who this guide is for

- **External contributors:** before you open a pull request, run the sanity scenario below on your machine and make sure it passes. The maintainers run the full test suite on your pull request, so you do not need to run every scenario yourself.
- **Internal engineering team:** you can run any scenario in the internal CI pipeline. For local testing, you can follow the guide below. Local runs are only for basic sanity testing. Run the entire test suite in CI to make sure your change works end to end.

## Sanity scenario

External contributors run this scenario before opening a pull request:

| Scenario | What it covers | Containers |
| --- | --- | --- |
| `archive-plain-debian12` | A basic secured cluster with every component, including Control Center. SASL PLAIN over TLS, archive install. | 8 |

Follow the steps below in order.

- [1. Prerequisites](#1-prerequisites)
- [2. Get the code](#2-get-the-code)
- [3. Create the Python environment](#3-create-the-python-environment)
- [4. Set up your terminal](#4-set-up-your-terminal)
- [5. Run the sanity scenario](#5-run-the-sanity-scenario)
- [6. Open your pull request](#6-open-your-pull-request)
- [Debugging a failing scenario](#debugging-a-failing-scenario)
- [Every time you open a new terminal](#every-time-you-open-a-new-terminal)
- [Other scenarios](#other-scenarios)
- [Creating and modifying scenarios](#creating-and-modifying-scenarios)
- [Troubleshooting](#troubleshooting)

## 1. Prerequisites

- Git
- curl
- Python 3.12 (exactly 3.12; the Molecule version used here does not work with newer Python versions)
- Docker, runnable by your user without `sudo`
- On Windows: WSL2. Run every command in this guide inside your WSL2 Linux distribution.

Docker needs enough resources for the scenario you run:

| Scenario | Memory for Docker | CPUs | Free disk space |
| --- | --- | --- | --- |
| `archive-plain-debian12` | 14 GB | 4 | 30 GB |

## 2. Get the code

CP-Ansible is an Ansible collection. Molecule can only find its roles and plugins when the code sits in a folder named `ansible_collections/confluent/platform`. Clone it like this:

```
mkdir -p ~/cp-ansible-dev
cd ~/cp-ansible-dev
git clone --branch <your-branch> https://github.com/confluentinc/cp-ansible.git ansible_collections/confluent/platform
cd ~/cp-ansible-dev/ansible_collections/confluent/platform
```

## 3. Create the Python environment

Install these exact versions. The Molecule scenarios are tested with them, and other versions may not work.

```
python3.12 -m venv ~/cp-ansible-dev/venv
source ~/cp-ansible-dev/venv/bin/activate
python -m pip install --upgrade pip wheel
python -m pip install "ansible==9.13.0" "ansible-compat==3.0.2" "molecule==4.0.1" "molecule-docker==2.1.0" \
  yamllint pytest-molecule "urllib3<2.0.0" "requests==2.31.0" bcrypt
ansible-galaxy collection install community.docker:==3.10.2
```

Use `ansible==10.7.0` for the `master` branch and `8.0.x` and later branches. Use `ansible==9.13.0` for `7.9.x` and earlier branches.

Check the install:

```
molecule --version
```

It should show `molecule 4.0.1` and `docker:2.1.0`.

## 4. Set up your terminal

```
export VERSION=8.4.0
```

`VERSION` is the Confluent Platform version.

To test another version, check that it works with this branch:

- CP-Ansible and Confluent Platform: [General requirements](https://docs.confluent.io/ansible/current/ansible-requirements.html#general-requirements)

On an arm64 machine, also run:

```
export ARCHITECTURE=arm64 ARCHITECTURE_SHORTHAND=aarch64
```

Point Molecule at the Docker socket your `docker` command uses:

```
export DOCKER_HOST=$(docker context inspect --format '{{.Endpoints.docker.Host}}')
```

## 5. Run the sanity scenario

`archive-plain-debian12` downloads everything it needs by itself. Run it:

```
molecule test -s archive-plain-debian12 -- \
  -e confluent_package_version=$VERSION
```

This creates the containers, runs CP-Ansible, runs the checks, and removes the containers. The first run takes a while (often 20 to 40 minutes) because Docker builds the images and downloads Confluent Platform.

The scenario passed if the command ends without an error. If it fails, see [Debugging a failing scenario](#debugging-a-failing-scenario).

## 6. Open your pull request

This step is for external contributors.

In the pull request description, confirm that the sanity scenario passed, and include the Confluent Platform version you tested with. The maintainers then run the full test suite, including the scenarios that cannot run outside Confluent, and post the results on the pull request.

## Debugging a failing scenario

`molecule test` removes the containers at the end, even when it fails. To keep them so you can look around, add `--destroy=never`:

```
molecule test -s <scenario> --destroy=never -- \
  -e confluent_package_version=$VERSION
```

Then:

- Open a shell in a container. Use a name from the `platforms` list in `molecule/<scenario>/molecule.yml`:

    ```
    molecule login -s <scenario> -h <container-name>
    ```

- After you change the code, run CP-Ansible again on the same containers:

    ```
    molecule converge -s <scenario> -- \
      -e confluent_package_version=$VERSION
    ```

- When you are done, remove the containers:

    ```
    molecule destroy -s <scenario>
    ```

Run the full `molecule test` command again at the end to confirm the scenario passes from scratch.

## Every time you open a new terminal

Run these again before you use `molecule`:

```
cd ~/cp-ansible-dev/ansible_collections/confluent/platform
source ~/cp-ansible-dev/venv/bin/activate
export VERSION=8.4.0
export DOCKER_HOST=$(docker context inspect --format '{{.Endpoints.docker.Host}}')
```

On arm64 machines, also run `export ARCHITECTURE=arm64 ARCHITECTURE_SHORTHAND=aarch64`.

## Other scenarios

**External contributors:** you only need to run the sanity scenario above before you submit your pull request. The maintainers run all the other scenarios to make sure your change does not break existing functionality.

**Note:** Some scenarios cannot run outside Confluent. For example, the FIPS scenarios need a FIPS-enabled host. Other scenarios have similar limitations.

**Internal engineering team:** the local runs in this guide are only for basic sanity testing. Run the entire test suite in the internal CI pipeline to make sure your change works end to end.

## Creating and modifying scenarios

To add a scenario, copy an existing one that is close to what you need and change it. Put your checks in its `verify.yml`.

Describe what the scenario tests in the `###` comment lines at the top of its `molecule.yml`. Then regenerate [MOLECULE_SCENARIOS.md](MOLECULE_SCENARIOS.md) and include the result in your pull request:

```
cd docs
python3 molecule_doc.py
cd ..
```

More on Molecule scenarios: https://molecule.readthedocs.io/en/latest/getting-started.html#molecule-scenarios

## Troubleshooting

### `confluent_package_version is not set`

`VERSION` is empty in your terminal, or the `-e confluent_package_version=$VERSION` part is missing from the command. Run `export VERSION=<version>` and run the full command again.

### Molecule cannot connect to Docker

Molecule fails with `Error while fetching server API version` even though `docker` works in your terminal. `DOCKER_HOST` is not set in this terminal. Run the `DOCKER_HOST` export from step 4 and try again.

### `Credentials store error` while building images

Your Docker config (`~/.docker/config.json`) uses a credential helper that fails. Molecule calls every configured helper when it builds images, even for registries the scenario does not use.

Log in again with the tool behind the helper named in the error. For example, for `docker-credential-gcloud`, run:

```
gcloud auth login
```

Then run the scenario again.

### `Name or service not known` while downloading

The containers could not resolve a host name, for example `packages.confluent.io` or `s3-us-west-2.amazonaws.com`. This usually happens for a short time after your network changes, for example when a VPN connects or disconnects, you switch networks, or your machine wakes from sleep. Run the scenario again. If it keeps failing, restart Docker and check that your VPN or proxy allows these hosts.

### Containers fail to start systemd, or `Too many open files`

On Linux hosts, the default inotify limit is too low for many systemd containers. Raise it:

```
echo 'fs.inotify.max_user_instances=512' | sudo tee /etc/sysctl.d/99-cp-ansible-molecule.conf
sudo sysctl --system
```

### Containers are killed or the run hangs

Docker ran out of memory. Give Docker more memory (step 1).

Running out of memory does not always look like a memory error. A Kafka broker can be killed partway through the run, and a later task then fails with `Connection refused`, for example when it calls MDS on port 8090. To check, run `docker exec <container> systemctl status confluent-server` and look for `oom-kill`.

### Temporary directory errors

```
Failed to create temporary directory.In some cases, you may have been able to authenticate and did not have permissions on the target directory.
```

Add this to `molecule/<scenario>/molecule.yml`:

```
provisioner:
  config_options:
    defaults:
      remote_tmp: /tmp
```

Then destroy and run the scenario again.
