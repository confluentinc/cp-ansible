# Secure-by-default deployment (template)

A customer-facing template that deploys every Confluent Platform component on its **own host** with
rootless operation, mTLS, RBAC, secrets protection, log redaction and audit logs. It composes
existing cp-ansible features; it adds a pre-flight gate and a post-deploy verification, not new roles.

| File | Purpose |
|---|---|
| `docs/sample_inventories/secure_by_default.yml` | Hardened inventory template (fill in `<...>` values, vault the `vault_*` secrets) |
| `playbooks/secure_preflight.yml` | Fails before any change if the inventory is below the baseline |
| `playbooks/secure_all.yml` | preflight -> validate_hosts -> `all.yml` -> verify |
| `playbooks/secure_verify.yml` | Proves rootlessness (sudo grants, private group, ownership, no root processes/units) and key-file permissions |
| `playbooks/secure_network.yml` (+ `vars/`, `templates/`, `tasks/`) | Default-deny nftables policy per host from a flow matrix, host-local rollback timer, live allow/deny probes |

**Scope:** `kafka_controller`, `kafka_broker`, `schema_registry`, `kafka_connect`, `ksql`, `kafka_rest`,
`control_center_next_gen`. `kafka_connect_replicator` and `usm_agent` are **rejected** by the pre-flight (they
have no firewall flows and no verified hardening) rather than deployed without the baseline.

## What the pre-flight enforces

Every setting is checked on **every host** against that host's effective value (host/group overrides
included), and any failure aborts the whole run before the first change (`any_errors_fatal`).

| Control | Assertion |
|---|---|
| Isolation | One CP component per host; no two inventory entries share an `ansible_host` |
| Rootless | `rootless_enabled`, `installation_method: archive`, no `become`, non-root `deployment_user`, non-system path |
| mTLS | `ssl_enabled`, `ssl_mutual_auth_enabled`, `ssl_client_authentication: required`; every Kafka listener TLS **and** client certificates (SASL does not replace them); MDS TLS **and** `mds_ssl_client_authentication: required` for any `auth_mode`; each REST component's `<group>_authentication_type` is `mtls`; no `*_custom_properties` entry weakens `ssl.client.auth*`; bundled Prometheus/Alertmanager use TLS + mTLS |
| Certificates | CA-signed (`ssl_custom_certs` or provided keystores); the snakeoil CA is rejected |
| Passwords | No well-known keystore/truststore/CA/LDAP/MDS/Jolokia passwords, minimum 16 chars |
| RBAC | `rbac_enabled`, `auth_mode` not `none`, bounded `impersonation_super_users` |
| Secrets | `mask_secrets`; per component `*_secrets_protection_enabled` and `*_secrets_protection_encrypt_passwords` |
| Logging | Per component: log redactor on with rules and `*_custom_log4j2` true; audit logs shipped to a destination cluster over TLS |
| Deny by default | `allow.everyone.if.no.acl.found` not `true`; per component Jolokia off or authenticated |

Non-production escape hatches (each prints a warning): `secure_allow_self_signed`,
`secure_allow_shared_hosts`, `secure_allow_no_audit_logs`.

## Run order

```bash
# 1. One-time privileged bootstrap (admin/sudo) - creates cp-user, linger, optional packages.
#    ansible_become=true is required: the sample inventory sets ansible_become: false, which overrides the
#    playbook's own become and would leave a non-root admin unprivileged.
ansible-playbook -i inventory.yml confluent.platform.rootless_bootstrap -e ansible_user=<admin> -e ansible_become=true -e rootless_install_packages=true

# 2. Gate (no changes made)
ansible-playbook -i inventory.yml confluent.platform.secure_preflight --ask-vault-pass

# 3. Deploy as cp-user, then verify
ansible-playbook -i inventory.yml confluent.platform.secure_all --ask-vault-pass

# 4. Network boundaries (privileged; needs root, so it is not part of secure_all). Default-deny nftables
#    per host from the flow matrix in playbooks/vars/secure_network.yml, then live allow/deny probes.
#    Try -e secure_network_enforce=false first (log-only), then enforce.
ansible-playbook -i inventory.yml confluent.platform.secure_network -e ansible_user=<admin> \
  -e '{"secure_network_admin_cidrs":["<control-node-ip>/32"],"secure_network_ldap_hosts":["<ldap-ip>"]}'
```

## How the network policy behaves

- **Ports come from each destination host's own variables**, so a per-group override such as
  `kafka_connect_rest_port: 18083` is honoured by the destination's ingress rule, every source's egress
  rule and the probes. With `--limit`, peers outside the limit fall back to this host's values; run without
  `--limit` to honour per-host overrides on unselected peers.
- **Flows include same-group peers** where they talk to each other (Schema Registry leader forwarding,
  Connect worker forwarding, ksqlDB pull-query routing, controller quorum, inter-broker), and controllers on
  the inter-broker listener (used for their RBAC metadata bootstrap). With a single Kafka listener the
  replication port is the `internal` listener.
- **SSH** is allowed from `secure_network_admin_cidrs` on the host's `ansible_port`.
- **Audit logs:** egress is opened to the `audit_logs_destination_bootstrap_servers` addresses only. Clients
  then connect to every advertised broker of that cluster, so add them all via `secure_network_extra_egress`.
- **Rollback:** before loading, a host-local `systemd-run` timer (default 600 s) is armed that restores the
  previous ruleset and persisted file (or disables the unit on a first install). It is cancelled only after a
  **fresh** administrative connection succeeds, so it recovers from a lockout the Ansible connection cannot.
- **Probes** use the same addresses and per-destination ports the rules were generated from. Probes whose port
  is also covered by a custom `secure_network_extra_ingress/extra_egress` rule are skipped, since the
  group-based expectation no longer holds for them.

## Prerequisites learned from test deployments

- **Target hosts: Python >= 3.10** (cp-ansible asserts this). RHEL/UBI 9 default to Python 3.9, so install
  `python3.12` (+ `python3.12-pyyaml`) and set `ansible_python_interpreter: /usr/bin/python3.12`.
  Ubuntu 24.04 already ships a new enough Python 3.
- **Control node:** `bcrypt` Python package (C3 password hashing runs locally), ansible-core 2.16/2.17.
- **Custom certificates:** keys must be **unencrypted** PEM. cp-ansible's key/cert match check
  (`roles/common/tasks/config_validations.yml`) pipes the key to `openssl pkey` with no passphrase, so a
  password-protected key fails with a misleading "key does not match certificate" error. `ssl_key_password`
  is still applied when cp-ansible builds the keystores.
- **Archive version:** the sample's `confluent_package_version: 8.4.0` is not published on
  `packages.confluent.io` (404); use a released version (8.3.0 was used in testing).
- **LDAP:** the `mds` bind account needs read/search on the `ou=rbac` tree, or the broker never opens
  its listeners (it logs "LDAP search failed" and keeps retrying).
- **Network policy vs. LDAP:** brokers/controllers need egress to the LDAP server; pass
  `secure_network_ldap_hosts`. Run `secure_all` before `secure_network`.
- **Re-running `secure_all` after the policy is enforced:** the policy blocks egress to the package
  repository, so `validate_hosts` fails its connectivity check (`packages.confluent.io` timeout) and every
  host is aborted. Either point `confluent_common_repository_baseurl` at an internal mirror and allow it with
  `secure_network_extra_egress`, re-apply `secure_network` with `secure_network_allow_package_egress=true`
  for the maintenance window, or pass `--skip-tags validate_internet_access` when no download is needed
  (the archive is already installed).

## Known limits - read before shipping to customers

- **Tested in containers, not on real hosts.** Test rig: 7 privileged systemd containers on one Docker
  network (one component each) plus an OpenLDAP container, driven over Ansible's docker connection,
  ansible-core 2.17, CP 8.3.0, one controller and one broker.
  - **Ubuntu 24.04 (minimal `ubuntu:24.04` base): PASSED.** bootstrap -> `secure_all` (preflight, deploy,
    `secure_verify`) -> `secure_network`. All 7 components deployed rootless with mTLS, RBAC over LDAP,
    secrets protection, log redactor. nftables policy applied on all hosts: 25 allow and 41 deny probes
    passed, spot checks confirmed (REST->Connect blocked, REST->broker open, C3->LDAP blocked), and MDS
    authentication returned 200 with a client cert + LDAP user and failed at TLS without a cert.
  - **RHEL 9.8 (`ubi9/ubi-minimal`, microdnf only, no dnf): PASSED**, identical results (25 allow / 41 deny
    probes, REST->Connect blocked, MDS 200 with cert and TLS failure without). Needed Python 3.12 (see below).
  - **Ubuntu 22.04, RHEL 8 (`ubi8/ubi-minimal`), RHEL 10 (`ubi10/ubi-minimal`): PASSED**, same flow, each with
    25 allow / 41 deny probes under an enforcing policy. Ubuntu 22.04 first failed the network phase: its
    older nft cannot resolve `ipv6-icmp` by name on a minimal image; the template now uses numeric protocol
    numbers (1, 58). RHEL 8 needs `python3.12`; RHEL 10 uses Java 21 and its default Python 3.12.
  - Not covered by the test: multi-broker/controller clusters, ldaps, audit-log shipping to a separate
    cluster, Ubuntu 20.04, real (non-container) hosts, SELinux enforcing, the hosts' real boot-time
    ordering of the firewall unit.

### Minimal base images

The playbooks deploy onto whatever hosts the inventory names, so the OS image is chosen when hosts are
provisioned, not at deploy time; there is one playbook set for both OS families. For container/VM images use
the minimal variants (`ubuntu` base image, `ubi9/ubi-minimal`). Minimal-image notes:
- Newest Ubuntu accepted by `validate_hosts` is 24.04 (it accepts 20/22/24); do not pick 26.04 without
  extending that list.
- `ubi-minimal` has `microdnf` but no dnf Python bindings, so Ansible's `package` module cannot install
  anything. Bake `nftables`, a JDK, `python3.12`, `openssl`, `rsync`, `unzip` and `systemd` into the image.
- UBI 10 has no Java 17 (Java 21 only).
- On ansible-core 2.19 the existing `variables` role fails on `kafka_broker_listeners` (`combine` filter);
  use 2.16/2.17 until that is fixed upstream in this repo.
- Rootless mode runs **all components under one `deployment_user`**. Host isolation is what separates
  components; there is no per-component OS user on a host.

## What the existing users + systemd model gives you (code review, not tested on hosts)

- **Root-managed mode - weak to moderate.** Separate users (`cp-kafka`, `cp-schema-registry`, ...) with a
  nologin shell, but all share group `confluent`; keystores/keys are mode 640 (readable by every
  component on the host), logs 770. No systemd hardening directives exist (only `LimitNOFILE` on some).
- **Rootless mode - weak.** One shared user, units have no hardening, env files (may hold secrets) are 0640.
  It contains the blast radius from root, not between components.
- Hence host-per-component isolation is the real boundary in this template. Closing the gaps (unit
  hardening such as `NoNewPrivileges`/`ProtectSystem`/`PrivateTmp`, per-component groups, 0600 keys,
  750 logs) is future work in the roles and is not done here.
- `ROOTLESS_DEPLOYMENT_STEPS.md` states rootless was validated single-node only and lists
  multi-node as future work; this template's multi-host layout depends on that being sound.
- FIPS is incompatible with rootless (needs root OS changes); the pre-flight rejects the combination.
- `ssl_custom_certs` per-host file naming and LDAP schema values must be adapted to the customer PKI/directory.
- Ansible Vault protects secrets at rest on the control node only.
