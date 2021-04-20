# Unprivileged Installation

## 1 - Constraints

The goal of this project is to install the Confluent platform under the following constraints:
1. The user installing the software should not be privileged.
2. The user installing the software should not have SSH access to the target hosts.
3. The user/service accounts running the services should not be privileged.
4. The files and folders of the platform should not be installed in system paths.
5. The installation should be as automated as possible.

From these constraints, we chose to:
- Use `cp-ansible` with the necessary modifications (to respond to constraint #5 and try to avoid re-inventing the wheel as much as possible).
- Use the `archive` option of `cp-ansible`, which means extracting the software from the tarball.
- Execute `cp-ansible` locally on the target hosts, with options limiting it to the service that needs to be installed and of course the local target host. This responds to constraints #1 and #2. Even though, by running `cp-ansible` host by host, we do not fully use the automated and remote capabilities of `ansible`, we still benefit from the ability to version a centralised copy of the code/settings and pull them easily on the target before installation (see pre-requisites).
- Have the admin create users, groups and paths prior to running the installation. This is the only time privileges are needed and typically this would be the role of the system administrator to provide VMs or systems with these resources already installed. We developed a few tools to help with this part.


## 2 - Pre-requisites on the target hosts

Prior to running `cp-ansible`, the following resources must be created on the system by the system administrator or the team preparing the base VMs.

### 2.1 - Packages
The following software is necessary on the target host:
- git
- python3 (3.5 or higher)
- ansible (2.9 or higher)
- java (version 8 or 11 as required by the Confluent platform, see https://docs.confluent.io/platform/current/installation/versions-interoperability.html#java)
- unzip
- openssl

### 2.2 - Users and Paths

These resources (users, groups, folders) are not privileged.

--> Replace `acme` below with the appropriate client name or the name of your project.

**Users and Groups**
To make sure that the installation process is using our custom options, instead of the default from `cp-ansible`, we are using the following names for the users and groups.
- All service account users are members of the `confluent` group.
- The user running the installation is `acme-install`
- The service accounts running the Confluent components are:
  - `acme-kafka` for zookeepers and brokers
  - `acme-schema-registry` for Schema Registry
  - `acme-connect` for Connect
  - `acme-connect-replicator` for Replicator
  - `acme-ksql` for ksqlDB
  - `acme-rest` for REST Proxy
  - `acme-control-center` for Control Center

To create groups and users, ON RHEL, run:

```
$ sudo groupadd confluent

$ sudo useradd --gid confluent --create-home --home-dir /home/acme-kafka acme-kafka
# repeat for all service accounts
```

**Installation User Settings**

You might have to adjust the `sudo` settings of your current user to allow it to run as the `ansible_become_user`.
```
ec2-user		ALL = /usr/bin/su - acme-install
```

**Application Files and Folders**
These folders and empty files needs to be created before running the install. We create empty files because the installation process will not be able to change their ownership and group.

Notable paths:

- `/usr/local/confluent` as the base folder for everything (another typical choice is `/opt/confluent`)
- settings and component properties will go under: `/usr/local/confluent/etc/`
- `systemd` configuration files under: `/usr/local/confluent/lib/systemd/`
- application log files under: `/usr/local/confluent/log`
- data directories: `/usr/local/confluent/zookeeper/data/` and `/usr/local/confluent/kafka/data/`

To automate the create of the files and folders, a script is provided (`unprivileged_create_files.sh`) and it takes its input from `unprivileged_preliminary_files.txt`.

Update `unprivileged_preliminary_files.txt` to match the desired paths, group and account names, then run:

```
$ ./unprivileged_create_files.sh ./unprivileged_preliminary_files.txt
```

Setting the same values for the paths in the `ansible` inventory file is also necessary.

### 2.3 - SystemD Setup

**systemd user-mode configuration**

To enable `systemd` to run in user-mode, there are 4 steps:

(1) A few file must be added to the system:

- `/etc/systemd/user/dbus.socket`
- `/etc/systemd/user/dbus.service`
- `/etc/systemd/system/user@.service.d/`
- `/etc/systemd/system/user@.service.d/dbus.conf`

Contents of the files:

```
$ cat /etc/systemd/user/dbus.socket
[Unit]
Description=D-Bus Message Bus Socket
Before=sockets.target

[Socket]
ListenStream=%t/dbus/user_bus_socket

[Install]
WantedBy=default.target

$ cat /etc/systemd/user/dbus.service
[Unit]
Description=D-Bus Message Bus
Requires=dbus.socket

[Service]
ExecStart=/usr/bin/dbus-daemon --session --address=systemd: --nofork --nopidfile --systemd-activation
ExecReload=/usr/bin/dbus-send --print-reply --session --type=method_call --dest=org.freedesktop.DBus / org.freedesktop.DBus.ReloadConfig

$ sudo mkdir /etc/systemd/system/user@.service.d/

$ cat /etc/systemd/system/user@.service.d/dbus.conf
[Service]
Environment=DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/%I/dbus/user_bus_socket
```

(2) Enable user-mode with:

```
$ sudo systemctl --global enable dbus.socket

Created symlink /etc/systemd/user/default.target.wants/dbus.socket → /etc/systemd/user/dbus.socket.
```

(3) Session life-time

For systemd to work in user-mode, the executing user must have its own instance of dbus started (it's a systemd requirement). The user dbus process is normally started during normal login but for services such as Confluent components, the dbus session must started at boot-time and not end if interactive sessions are closed.

To do so, for each service account, run: `sudo loginctl enable-linger <user>`

(4) At last, an environment variable named `XDG_RUNTIME_DIR` must be set in the environment of the process that will run `systemd --user` commands:

`XDG_RUNTIME_DIR=/run/user/$(id -u) `


If you get the 'Failed to connect to bus: no such file or directory' error, then it's because either dbus is not properly setup for user-mode operations, or you do not have the required envvar.

## 3 - cp-ansible Configuration

Once, the target system has been prepared with the proper group, users, files, folders and systemd settings, you can run `ansible`.

This section describes the variables to **set inside your inventory file**. You can find an example of this inventory in: `sample_inventories/unprivileged.yml`.

```
---
all:
  vars:
    ansible_connection: local                                                (1)
    ansible_user: ec2-user
    ansible_become: true
    ansible_become_user: acme-kafka                                          (2)

    # required for unprivileged installation
    privileged_install: false                                                (3)
    systemd_mode: user                                                       (4)

    confluent_archive_file_source: /home/ec2-user/confluent-6.1.1.tar.gz
    confluent_archive_file_remote: false                                     (5)

    installation_method: archive                                             (6)
    # when installation_method = archive, archive_destination_path defaults to: /opt/confluent
    # override if you wish to place the files somewhere else
    archive_destination_path: /usr/local/confluent                           (7)
    # when installation_method = archive,
    # binary_base_path = archive_destination_path + version, for example: /opt/confluent-5.5.3

    # by default, these would go to /var/log/
    # for example zookeeper_log_dir would use zookeeper_default_log_dir (= /var/log/kafka)
    # so they need to be overridden when wanting to install to user paths
    zookeeper_log_dir: "{{binary_base_path}}/log/zookeeper"                  (8)
    kafka_broker_log_dir: "{{binary_base_path}}/log/kafka"
    schema_registry_log_dir: "{{binary_base_path}}/log/schema_registry"
    kafka_rest_log_dir: "{{binary_base_path}}/log/rest"
    kafka_connect_log_dir: "{{binary_base_path}}/log/connect"
    kafka_connect_replicator_log_dir: "{{binary_base_path}}/log/connect_replicator"
    ksql_log_dir: "{{binary_base_path}}/log/ksql"
    control_center_log_dir: "{{binary_base_path}}/log/control_center"

    kafka_connect_jmxexporter_config_path: "{{archive_destination_path}}/prometheus/kafka_connect.yml"

    # disable and ensure that they are on the system before running the install
    install_java: false                                                      (9)
    install_openssl_unzip: false

    zookeeper_service_environment_overrides:                                (10)
      JAVA_HOME: /usr/local/confluent/java    
```

1. Because of our constraints, we have to use the `local` install
2. The user we become is unprivileged
3. `privileged_install: true` is the main switch for disabling the privileged calls from `cp-ansible`
4. `systemd_mode: user` is the switch for installing the services in systemd user-mode
5. The archive file settings allow `cp-ansible` to find the tarball
6. `archive` installation is the only choice to control where the files will go
7. `archive_destination_path` is the main setting to control where the files will be installed
8. We have to override the `*_log_dir` settings to control where the application logs go
9. A few package installs need to be disabled too. The components will still need those software packages so they need to be installed beforehand.
10. These overrides provide the location of `java` to the components.
