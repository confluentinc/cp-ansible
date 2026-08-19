# Rootless (Non-Root) Deployment

Deploy Confluent Platform without broad root access. cp-ansible installs + configures + runs CP
entirely as an unprivileged user via **`systemd --user`** units; the only root needed is a
one-time host bootstrap (create the user, enable linger, optionally install a JDK).

Validated live on RHEL 9 (KRaft, single node), `rootless_enabled: true`, as the deploy user:

| Config | Result |
|---|---|
| plaintext (7 components) | ✅ failed=0, all `systemd --user` units active, produce/consume |
| mTLS (7 components) | ✅ failed=0, TLS produce/consume |
| RBAC over LDAP + mTLS | ✅ failed=0 (hands-off), MDS auth 200 / bad-pw 401 |

RBAC over an **external OAuth/OIDC IdP is 8.x-only** — not available on this (7.6.x) line.

---

## How it works

Two phases:

1. **One-time privileged bootstrap** (run once by an admin/sudo user): creates the deploy user +
   `authorized_keys`, the deployment directory, enables `systemd` linger, and optionally installs a
   JDK + openssl/rsync/unzip. Sites with no sudo do these steps out-of-band and skip this playbook.

2. **Rootless deploy** (as the unprivileged deploy user, `ansible_become: false`): downloads +
   unpacks the CP archive under `deployment_path`, generates config, generates and starts
   `systemd --user` units (`cp-<component>.service`, `Restart=on-failure`), and — for RBAC — drives
   the controller↔broker MDS bootstrap to convergence. No manual service start.

The `rootless_enabled: true` inventory flag turns on the `systemd --user` lifecycle, asserts
`installation_method: archive`, and **automatically skips the root-requiring steps** (the tasks tagged
`privileged,package,systemd,sysctl,health_check,logrotate`) — so no `--skip-tags` is needed on the
command line. (Those tags still exist, so `--skip-tags …` also works as an equivalent fallback.)

---

## 1. Inventory

Start from `docs/sample_inventories/non_root_deployment.yml`. Minimum:
```yaml
all:
  vars:
    ansible_user: cp-user
    ansible_become: false
    rootless_enabled: true
    deployment_user: cp-user
    deployment_group: cp-user
    deployment_path: /home/cp-user/cp-data
    installation_method: archive
    <component>_skip_restarts: true      # for each component
    # security (optional): ssl_enabled/self_signed/ssl_mutual_auth_enabled (mTLS);
    #                      rbac_enabled + mds_* + ldap.* (RBAC)
```
With `deployment_*` set, every user/group/log/data/ssl/cli/jmx/plugin path is derived automatically —
no ~60 per-component overrides.

## 2. One-time bootstrap (admin/root, once)

```bash
ansible-playbook -i <inventory> confluent.platform.rootless_bootstrap -e ansible_user=ec2-user
# add -e rootless_install_packages=true to install cert tools + python + Java
#   (openssl/rsync/unzip/python3-pip/python3-pyyaml; on Debian/Ubuntu also dbus-user-session — see below)
```
Creates `deployment_user` (+ authorized_keys so the same SSH key works), `deployment_path`, and runs
`loginctl enable-linger`. Idempotent.

**Java:** the bootstrap honors the collection's normal Java model — it installs Java only when
`install_java` is true (i.e. `custom_java_path` is not set), using `{redhat,ubuntu,debian}_java_package_name`
(default the full **java-17** JDK — CP 7.6 also supports Java 11; override e.g. to `java-11-openjdk`). To
bring your own JDK (any version/distribution — OpenJDK/Zulu/Temurin/Oracle), set **`custom_java_path`** and
the bootstrap skips the Java install (it's wired into `JAVA_HOME` for every component by the deploy).

**Debian/Ubuntu:** the deploy user's `systemd --user` manager (`user@<uid>`) needs a per-user D-Bus,
provided by the **`dbus-user-session`** package. The bootstrap installs it (with
`rootless_install_packages=true`); without it `systemctl --user` fails with "Failed to connect to bus".
RHEL ships this with systemd — nothing extra needed.

**Control node (once):** Ansible ≥ 2.16; `pip install --user bcrypt` (only for RBAC — hashes MDS creds locally).

If you have no sudo at all, do the equivalent by hand out-of-band:
```bash
sudo useradd -m -g <group> <user>; install authorized_keys; mkdir deployment_path (chown user)
sudo loginctl enable-linger <user>
# Java: install a supported JDK (CP 7.6 = Java 17 or 11; full JDK, not JRE) e.g.
#   `sudo dnf install java-17-openjdk` / `sudo apt-get install openjdk-17-jdk`, OR unpack any JDK tarball
#   (OpenJDK/Zulu/Temurin/Oracle) and set custom_java_path
# cert tools + python: dnf/apt install openssl rsync unzip python3-pip python3-pyyaml(RHEL)/python3-yaml(Deb)
# Debian/Ubuntu only: sudo apt-get install -y dbus-user-session   (per-user D-Bus for systemd --user)
```

## 3. Rootless deploy (as the deploy user, no root)

```bash
ansible-playbook -i <inventory> confluent.platform.all
```
With `rootless_enabled: true` set in the inventory, the root-requiring tasks skip themselves — no
`--skip-tags` required. The playbook generates the units and starts them (`systemctl --user enable --now cp-<component>`),
in dependency order (controller → broker → SR → Connect → ksqlDB → REST → C3). For RBAC it
co-restarts controller+broker until MDS `:8090` is live, then creates role bindings — hands-off.

## 4. Manage / verify (as the deploy user)

```bash
export XDG_RUNTIME_DIR=/run/user/$(id -u)
systemctl --user status 'cp-*'                 # all active; enabled = start on boot (linger)
systemctl --user restart cp-kafka_broker       # crash-recovery is automatic (Restart=on-failure)
journalctl --user -u cp-kafka_broker           # logs
# produce/consume; RBAC: curl -sk -u mds:password https://<host>:8090/security/1.0/authenticate → 200
```

## 5. Proving it's actually rootless

Creating `deployment_user` (step 2) doesn't by itself prove the *deploy* (step 3) never escalates —
that admin account still has sudo. Confirm the deploy user genuinely can't escalate, and that
nothing did, with checks like these:

**Before the run** — the deploy user has no path to root:
```bash
sudo -u <deployment_user> sudo -n true; echo $?   # non-zero = no passwordless sudo
```
If you're provisioning `deployment_user` yourself (the no-sudo path in step 2), give it its own
account with **no** entry in `wheel`/`sudo`/any sudoers file — don't just reuse a cloud image's
default admin account (e.g. `ec2-user`), which usually has passwordless sudo and so proves
nothing about rootlessness.

**After the run** — nothing escalated:
```bash
find <deployment_path> -not -user <deployment_user>   # no root-owned files - empty output
ps -eo user,cmd | awk '$1 == "root"' | grep -i 'kafka\|confluent'  # no root-owned CP process
systemctl list-units 'cp-*' --no-legend                # system-scope - empty, none exist
systemctl --user list-units 'cp-*' --no-legend         # user-scope - the real running units
```
A task that's missing its `when: not (rootless_enabled|bool)` guard on `become: true` fails loudly
here (`sudo: a password is required`) instead of silently succeeding, precisely because the deploy
user has nothing to escalate to - so a clean run through these checks is a real proof of
rootlessness, not just an absence of errors.

---

## Per-config notes

- **mTLS**: set `ssl_enabled`/`self_signed`/`ssl_mutual_auth_enabled`/`ssl_client_authentication`. Self-signed
  CA is generated on the control node; keystores land under `{{ deployment_path }}/ssl`. openssl/rsync must
  be present (bootstrap `rootless_install_packages=true`, or pre-installed).
- **RBAC over LDAP**: stand up the LDAP backend (e.g. 389-DS: suffix `dc=example,dc=com`, `ou=rbac`, bind
  `cn=mds`, component principals, and the `mds` read/search ACI on `ou=rbac`). The controller↔broker MDS
  bootstrap converges automatically (`rootless_rbac_bootstrap_attempts`, default 10). No manual start.
- **FIPS**: not fully rootless — OS FIPS mode (`update-crypto-policies --set FIPS`) is a root, out-of-band step.

## JVM env with systemd --user
The generated `cp-<component>.service` uses `EnvironmentFile=<deployment_path>/rootless-bin/<component>.env`,
which carries the same `KAFKA_OPTS`/`KAFKA_HEAP_OPTS`/`KAFKA_LOG4J_OPTS`/`JAVA_HOME` the systemd
`override.conf` would have — so nothing is dropped on start (no manual `export` needed).

## Scope / notes
- Single-node validated; multi-node needs per-host supervision (future work).
- `custom_java_path` (tarball JDK) is wired into `JAVA_HOME` for every component, so a user-supplied JDK
  works without the root `/usr/bin/java` symlink.
- Prereqs auto-handled by the deploy: target-side PyYAML (`pip --user`).
