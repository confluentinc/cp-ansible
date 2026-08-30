# PR #2602 Review Comment Tracking

Local working doc (not part of the PR) tracking every review comment on
[cp-ansible#2602](https://github.com/confluentinc/cp-ansible/pull/2602) — what it raised,
whether/how it's addressed on this branch (`ANSIENG-5900-rootless-fixes-molecule`), and why.
Commit hashes below are on this branch, layered on top of `be5d74a34` (the commit both
reviewers were commenting against).

Status legend: ✅ Fixed · 💬 Answered (no code change needed) · ⚠️ Open

---

## 1. ishikaa-p's own review pass (2026-08-07, self-review notes)

All of these were raised and answered before this session segment (2026-08-10 replies,
commit `1df7d2549` and earlier). Listed for completeness.

| Comment | Status | Resolution |
|---|---|---|
| `rootless_start_service.yml` — recheck if we can use ansible native systemctl | ✅ | Switched to `ansible.builtin.systemd_service` (`scope: user`) instead of raw `systemctl --user` commands. |
| `rootless_bootstrap.yml` — check root version for this (authorized_keys copy) | ✅ | Confirmed needed: rootless has no `become`, so Ansible must SSH directly as `deployment_user` for the rest of the deploy; a fresh user has no `authorized_keys` without this step. |
| `rootless_bootstrap.yml` — check if we need this in one-time root setup (deployment_path creation) | ✅ | Confirmed needed: nothing else in the codebase creates `deployment_path`; the archive install would fail on a fresh host without it. |
| `rootless_bootstrap.yml` — check/remove `when: rootless_enable_linger` if not needed | ✅ | Kept: without linger, the user's systemd manager (and everything under it) is torn down the moment the SSH connection closes. Not optional in practice, hence the `default(true)`. |
| `rootless_bootstrap.yml` — check convention for lint errors | ✅ | Converted two flow-style YAML lists to block-style to match collection convention. |
| `kafka_broker/restart_and_wait.yml` — does rootless restart, can root+rootless combine? | ✅ | Added rootless restart branch to all 7 components' `restart_and_wait.yml` — this was a real bug (root-path restart never fired under rootless, so config changes weren't propagating). Kept as separate tasks (mechanism genuinely differs: system `systemd` + `daemon_reload` vs. `systemctl --user` + `XDG_RUNTIME_DIR` + unit-existence guard), both driven from the same file via mutually-exclusive `when:`. |
| `kafka_connect/defaults/main.yml:44` — why does root never need `JAVA_HOME` but `custom_java_path` does under rootless | 💬 | Root's `custom_java_path` install runs `alternatives` (privileged) to symlink `/usr/bin/java` → the custom JDK, so plain `java` on PATH resolves system-wide — no `JAVA_HOME` needed. That `alternatives` task is skipped under rootless (writes to `/usr/bin`, needs root), so there's no other way to point the JVM at a custom JDK — `JAVA_HOME` is the only mechanism left, hence `JAVA_HOME: "{{ custom_java_path | default('') }}"` in `*_service_environment_overrides`. |
| `rootless_prereqs.yml:9` — check for duplication (e.g. pip install) | ✅ | Checked: not duplicated. Deliberate two-tier fallback — tries the fully-rootless path first (`ensurepip --user` + `pip install --user PyYAML`), only falls back to pointing at the one-time root step if that's entirely unavailable. No overlap in what runs on a given host. |

---

## 2. rrbadiani — inline comments (2026-08-12, on commit `31957181`)

### 2a. Already fixed before this doc existed (commits `1df7d2549`–`65377ebc1`)

| # | File:line | Comment | Status | Fixed by |
|---|---|---|---|---|
| 1 | `roles/kerberos/tasks/main.yml:21` | "how kerberos work if rootless setup is enabled?" | ✅ | `3c4c3d40f` — Kerberos was entirely broken under rootless (`/etc/krb5.conf` hardcoded, keytab copy unconditionally skipped). Made 13 keytab/config-path variables `deployment_path`-aware; removed the rootless skip guards on keytab tasks. |
| 2 | `roles/common/tasks/main.yml:63` | "why run it when not doing rootless setup?" | ✅ | `1df7d2549` — the prereq-bootstrap task was guarded on `deployment_path\|length>0` instead of `rootless_enabled\|bool`, so it could fire on a root deploy that merely customized `deployment_path`. Aligned the guard with the adjacent assert. |
| 3 | `roles/common/templates/rootless.service.j2:12` | "missing out on [service/unit/env] overrides?" | ✅ | `65377ebc1` — the `[Service]` section override surface (`*_service_overrides`, e.g. `LimitNOFILE`) was genuinely missing from the rootless unit template (root's `override.conf.j2` renders 3 override dicts; rootless only covered 2). Added the missing loop, wired `rootless_service_overrides` through all 7 components. Live-verified: a custom `LimitNOFILE` now renders and is active via `systemctl --user show`. |
| 4 | `roles/common/tasks/rootless_lifecycle.yml:27` | "won't [notify restart on secrets-protection change] break now?" | ✅ | `1df7d2549` — added `notify: "{{ rootless_restart_handler }}"` to the EnvironmentFile/unit-generation tasks, threaded a per-component handler name through all 7 components. Live-verified: a `custom_java_path` change (flows into `JAVA_HOME`) produces a new PID and later `ActiveEnterTimestamp` — a genuine restart, not just a rewritten file. |
| 5 | `docs/sample_inventories/non_root_deployment.yml:27` / `roles/variables/defaults/main.yml:327` | "have we asserted `deployment_path` must be defined if rootless?" | 💬 | Already existed — `roles/common/tasks/main.yml`'s "Verify rootless prerequisites" assert checks `installation_method == "archive"` and `deployment_path\|length > 0` when `rootless_enabled`. |
| 6 | `roles/variables/defaults/main.yml:327` | "what if someone has defined `ssl_file_dir`, will it fail their rootless setup?" | ✅ | `32ae0669b` (Fix 5) — added an early writability assert for `deployment_path` and `ssl_file_dir` under rootless, with a clear fail message pointing at `rootless_bootstrap`, instead of a confusing permission-denied failure deep in the deploy. Live-verified both the happy path (no false positive when `ssl_file_dir` doesn't exist yet) and the failure path (a root-owned override is caught immediately). |
| 6a | `r3765175685` follow-up | "should the deployment_path/ssl_file_dir writability check move into `config_validations.yml`? what about deployment_user/deployment_group assertion?" | ✅/❌ | **Move: declined, deliberately.** `config_validations.yml` is included at `common/tasks/main.yml:139` - *after* `rootless_prereqs.yml` runs (line 62) and *after* RedHat/Ubuntu/Debian repo+Java setup (lines 127-137), and gated `when: validate_hosts\|bool`. Moving the writability checks there would delay them past exactly what they're designed to fail-fast before, and would make a critical permission check silently skippable via `validate_hosts: false` - neither true today. The zookeeper+rootless check living there doesn't have this problem (pure group-membership check, no ordering dependency) - not the same category despite surface similarity. **`deployment_user`/`deployment_group`: real gap, fixed - then collaterally reverted, then re-fixed.** Added both to the existing "Verify rootless prerequisites" assert (`common/tasks/main.yml:49-60`). Worth noting why this matters beyond a bare missing-assert: `deployment_group`'s only fallback anywhere in the *deploy* path is `else 'confluent'` (every `*_default_group` in `roles/variables/vars/main.yml`) - never `deployment_user`. `rootless_bootstrap.yml` has its own local convenience fallback (`deployment_group \| default(deployment_user)`), scoped only to bootstrap's own play. So a user who sets `deployment_user` alone and assumes `deployment_group` follows it would get a working bootstrap but a broken deploy - ownership tasks would target group `confluent`, which doesn't exist on a rootless host. **This fix was later found missing from the codebase** - collateral damage from an unrelated `git checkout` on this same file (reverting an abandoned, separate feature). Caught live while setting up the Kerberos-rootless EC2 test (task #25): re-added in `89f58f7d4`, confirmed every sample inventory and all 3 rootless molecule scenarios already set both vars explicitly, so nothing regresses. |
| 7 | `playbooks/rootless_bootstrap.yml:176` | "i think we removed this right?" (`rootless_deploy.sh` reference) | ✅ | `1df7d2549` — that script never existed anywhere in repo history (confirmed via `git log --all --diff-filter=A`). Fixed the bootstrap summary to reference the actual next step, `confluent.platform.all`. |
| 8 | `roles/variables/defaults/main.yml:140` | "let regen vars md file" | ✅ | `1df7d2549` — regenerated `docs/VARIABLES.md`. Hit a separate pre-existing crash in `docs/doc.py` on multi-line `### ` comments; fixed by shortening the 3 offending comments to single lines (per explicit instruction: fix the source, not the parser). |
| 9 | `roles/common/tasks/debian.yml:92,100` | "shouldn't these have a `not rootless_enabled` flag?" (×2) | 💬 | Checked: not needed. These tasks are guarded `installation_method == "package"`, and the "Verify rootless prerequisites" assert already fails the whole play if `rootless_enabled` and `installation_method != archive` — so that combination can never reach these tasks. Logically impossible, no fix needed. |
| 10 | `ROOTLESS_DEPLOYMENT_STEPS.md:15` | "why?" (OAuth/OIDC is 8.x-only) | 💬 | Factual: RBAC over external OAuth/OIDC requires an 8.x-only MDS feature not backported to this 7.6.x line. No code change. |

### 2b. Fixed in this session, on top of the above

| # | File:line | Comment | Status | Fixed by |
|---|---|---|---|---|
| 11 | `roles/ksql/tasks/restart_and_wait.yml:18` | "zk and replicator doesn't have this" | ✅ (replicator) / 💬 (zk, deliberately not supported) | `65377ebc1` gave `kafka_connect_replicator` full rootless lifecycle wiring (start/restart/log_dir/keytab/pem-path fixes — see §3 below for the bugs the live test caught). Zookeeper: **explicit product decision, confirmed with the user** — not supporting it under rootless (KRaft supersedes it). Replaced its scattered, half-finished `rootless_enabled` guards with a single fail-fast assert in `config_validations.yml` (`62945bf52`), and reverted the now-dead guards back to base state in the same commit. |
| 12 | `roles/ksql/tasks/restart_and_wait.yml:18` | "and also start maybe" | ✅ | Same fix — replicator now has a rootless *start* path too (`rootless_start_service.yml`), not just restart. |
| 13 | `roles/ksql/tasks/restart_and_wait.yml:18` (same comment recurs at `r3765934448` on `roles/ksql/tasks/restart_and_wait.yml`) | "why not use [a single systemd_service task with ternary name/scope] to avoid missing start/restart at places?" | ⚠️ | **Not adopted, but not because it's technically infeasible - corrected from an earlier overstatement.** Today's `restart_and_wait.yml` is 3 tasks: traditional restart (`not rootless`), a stat-check for the rootless unit's existence, then the rootless restart (`rootless and unit.stat.exists`). The reviewer's proposed ternary (`name`/`scope`/`daemon_reload` all toggled on `rootless_enabled`) correctly collapses tasks 1 and 3 into one - checked `ansible.builtin.systemd_service`'s `daemon_reload` default (`false`) and confirmed the ternary reproduces today's behavior in both branches exactly. The stat-check task would still be needed separately. **The real reason not to adopt it now is blast radius, not mechanism**: this identical 3-task pattern repeats across all 9 components' `restart_and_wait.yml` (and the analogous `start` logic), so unifying it is a genuine cross-cutting refactor that deserves its own dedicated verification pass - re-testing every component's restart/start path under both root and rootless - not something to fold into this already-large PR. Worth doing as an explicit follow-up. |
| 14 | `docs/sample_inventories/non_root_deployment.yml:28` | "how are we testing any working cluster on upgrade won't get their data/config dirs changed?" | ✅ | Every derived variable's ternary has the form `(deployment_path-based) if deployment_path\|length>0 else (today's exact literal)`. `deployment_path` defaults to empty string. So for any existing cluster that never sets `deployment_path` (the entire installed base, since this variable is new in this PR), every single derived path resolves to the *exact same literal* it always has — byte-for-byte, not just "similar." Upgrading cp-ansible version alone cannot change a path for an existing non-rootless cluster. Task #42's root brownfield *redeploy* test (same post-PR code twice) confirmed the deployed paths are the traditional root ones. **Now closed with a real pre-PR→post-PR upgrade test**, not just a same-code redeploy: `upgrade_safety_evidence/` (`f61774c43`) - a static audit cross-checking all 47 changed path variables' root-resolved values via real Jinja evaluation and the doc generator independently (47/47 unchanged, zero omissions found in a repo-wide grep sweep including every template), plus a live 3-node ZK-based cluster deployed with the actual pre-PR `v7.6.12` code, produced real data, then upgraded in-place to this PR's HEAD code with the *same unmodified inventory* - byte-identical inodes/mtimes on the data files before and after, identical rendered `log.dirs`/`dataDir`/`data.dir`/`state.dir` values, message checksum match, cluster fully functional post-upgrade. See `upgrade_safety_evidence/A1_SUMMARY.md`–`A3_SUMMARY.md` and `B_SUMMARY.md`. |
| 15 | `docs/sample_inventories/non_root_deployment.yml:28` (reply to #14, `r3764845257`) | "there may be some cases where simple upgrade of cp ansible version can cause a few paths to change and thus break running clusters" | ✅ | Same answer as #14, now with real upgrade-test backing (`upgrade_safety_evidence/`) rather than just a same-code redeploy - the pattern is upgrade-safe by construction (ternary defaults to today's exact literal when `deployment_path` is unset), *and* a live pre-PR-code→post-PR-code upgrade on a real cluster with real data confirms it holds in practice, not just in code review. Not disputing the general *category* of upgrade risk — just that this specific PR's new variables don't create it, because nothing pre-existing can already be pointing at a `deployment_path`-derived path. |
| 16 | `docs/sample_inventories/non_root_deployment.yml:28` | "how to sanitize this `deployment_path` for trailing slashes" | ✅ | Fixed (`1f4410e63`, Fix 9). Added `deployment_path_final` in `roles/variables/vars/main.yml` using the exact same `regex_replace('\/$', '')` idiom as `ssl_file_dir_final`, switched all 45 `deployment_path ~ '/...'` constructions plus the two direct usages in `common/tasks/main.yml` to use it. Verified byte-for-byte unchanged for the no-trailing-slash and empty-default cases via direct Jinja2 render, fixed for the trailing-slash case. |
| 17 | `docs/sample_inventories/non_root_deployment.yml:27` | "the path `/cp-data` would need permissions, this inventory isn't correct — try it on a real cluster" | ✅ | Correct as designed, not a bug: `/cp-data` (root-level) is created and chowned to `deployment_user` by the *privileged one-time bootstrap* (`rootless_bootstrap.yml`'s "Create deployment base directory" task), which is exactly why that two-phase flow exists — the sample inventory assumes bootstrap ran first, matching `ROOTLESS_DEPLOYMENT_STEPS.md`'s documented order. **Now independently re-verified against this *exact* file end-to-end on a real cluster** (task #37) - ran the literal committed file (only host groups appended, no existing line touched), bootstrap then deploy, `failed=0`, all 7 units active, everything under `/cp-data` owned by `cp-user`. Separately confirmed that *later* tasks under `/cp-data` carry no privilege at all (zero play-level `become: true` outside `rootless_bootstrap.yml`; the 4 remaining hardcoded task-level `become: true` are all pre-existing, guarded `not (rootless_enabled\|bool)`, and unrelated to `deployment_path`) - they run as the plain `deployment_user`, relying purely on the ownership bootstrap already established. Log: `sample_inventory_test_logs/nonroot_plain_0{1,2,3}_*.log`. |
| 18 | `ROOTLESS_DEPLOYMENT_STEPS.md:123` | "if we are not supporting FIPS do we fail fast?" | ✅ | Originally answered 💬 (the pre-existing generic `sysctl crypto.fips_enabled` assert incidentally catches it). On follow-up, this was correctly pushed back on: that check's failure message ("please enable fips on your Remote Host") is misleading for a `deploy_user` with no sudo, and it doesn't explain *why* - `fips-redhat.yml`'s two FIPS-enablement tasks (`update-crypto-policies --set FIPS`, JVM `java.security` tweak) both require root and are already correctly skipped `when: not rootless_enabled`, but nothing replaces them in `rootless_bootstrap.yml` the way Java/cert-tools are replaced - so the combination can never succeed, not just when misconfigured. Added an explicit "Fail fast - rootless does not support FIPS" assert in `config_validations.yml` (`95f079b0b`, message shortened in `17230b746`), mirroring the existing zookeeper-under-rootless unsupported-combination pattern right above it. Confirmed no existing rootless sample inventory or molecule scenario sets `fips_enabled`, so nothing regresses. |
| 19 | Issue comment, 2026-08-19T09:12:39Z | Three points: (a) rename `deployment_path`/`deployment_user`/`deployment_group` to reduce accidental-collision risk with an existing customer inventory that happens to already define those names; (b) sample inventory's `deployment_path: /cp-data` needs root-owned bootstrap - use a path under the deploy user's own home instead so bootstrap doesn't need to create it; (c) turn the manual "proving it's rootless" doc section into an automated `sudo -n true` probe + assert. | ✅ | **(b)** Changed all 3 sample inventories (`non_root_deployment.yml`, `non_root_deployment_rbac_ldap.yml`, `non_root_deployment_rbac_oauth.yml`) from `/cp-data` to `/home/cp-user/cp-data`, matching `ROOTLESS_DEPLOYMENT_STEPS.md`'s inventory snippet which already used the home-directory form. **(c)** Added "Check for non-interactive sudo escalation (rootless)" (`sudo -n true`, `failed_when: false`) + "Warn if deploy user has non-interactive sudo (rootless)" to `roles/common/tasks/main.yml`, gated `rootless_enabled\|bool`. Deliberately a **warning** (`debug`), not a hard `assert`/`fail`: passwordless sudo doesn't break a rootless deploy (nothing in this codebase ever invokes it), so failing the run over it would be enforcing a security *posture* choice that's outside cp-ansible's control and could break existing deployments where the account has sudo for unrelated reasons - the warning still gives the operator the automated signal they asked for. **(a)** PR author confirmed scope: rename `deployment_path` only, leave `deployment_user`/`deployment_group` as-is (their fallback behavior differs across bootstrap vs. deploy in ways that make a blanket rename riskier, and they don't share the same "already a common existing-inventory name" collision concern as a generic `deployment_path`). Renamed to `rootless_deployment_path` (`18ce0c3c8`) across all 18 affected files (`roles/`, `playbooks/rootless_bootstrap.yml`, `docs/`, all 3 molecule scenarios, `ROOTLESS_DEPLOYMENT_STEPS.md`) - mechanical only, no behavior change, verified via direct Jinja rendering of the empty/set/trailing-slash ternary cases, `docs/VARIABLES.md` regenerated via `doc.py`, and both static sanity checks still green. |
| 20 | `roles/common/templates/rootless.service.j2:13` (`r3811624498`) | "why are we changing the format, earlier we kept it all in a single file" (root's `override.conf.j2` inlines unit/service/`Environment=` overrides in one file; rootless splits into `rootless.service.j2` + a separate `EnvironmentFile=`) | 💬 | Root's mechanism is a systemd **drop-in override** layered on a base unit - for `installation_method: package` the RPM/DEB installs it; for `installation_method: archive` (root), `roles/kafka_broker/tasks/main.yml:151-163` (mirrored in all 9 components) copies a pre-built unit out of the tarball's own `lib/systemd/system/` to `{{systemd_base_dir}}` (hardcoded `/usr/lib/systemd/system`, not `deployment_path`-aware) - either way cp-ansible only ever templates the override half. That task is explicitly `when: not (rootless_enabled\|bool)` because reusing that shipped unit for rootless isn't viable, confirmed against a real one pulled from a live cluster's support bundle (`confluent-kcontroller.service`): `User=cp-kafka`/`Group=confluent` don't apply under `systemd --user` (a user manager can't switch UID away from the invoking user), `ExecStart=/usr/bin/kafka-server-start /etc/kafka/server.properties` is hardcoded to the fixed package path while rootless's `deployment_path` is arbitrary per inventory, and `WantedBy=multi-user.target` isn't a valid `--user`-scope target. Every substantive line would need overriding on every rootless deploy anyway, so there's no "thin override on a working base" to reuse - `rootless.service.j2` writes a correct unit directly instead of copying-then-rewriting an incompatible one. Also ruled out two other candidate reasons for the split itself: `daemon_reload` in `rootless_lifecycle.yml` runs unconditionally regardless of which file changed (not a reload-avoidance optimization today), and root's `override.conf.j2` is written with the identical `mode: '640'` as rootless's `.env` file, so stricter-permissions-for-secrets isn't the differentiator either. |

### 2c. General PR comments

| Comment | Status | Resolution |
|---|---|---|
| "are we taking up replicator fixes or skipping it?" (2026-08-12, issue comment) | ✅ | Taken up. `kafka_connect_replicator` now has full rootless support (`65377ebc1`) and molecule CI coverage (`a4537e947`, pending final CI confirmation — see §5). |

---

## 3. Bugs the live-verification process itself caught (not directly requested by a comment, but found while addressing one)

These are additive findings surfaced by *doing* the work above, not separate review comments —
listed because they materially changed what "addressed" means for some of the items above.

- **`rootless.service.j2` / `rootless_component.env.j2`**: `default({})` doesn't substitute for
  an explicit YAML `null` (only for genuinely undefined vars), and every component's
  `*_service_unit_overrides` default is a bare key (parses as `None`). This was already-pushed,
  broken code affecting every rootless deploy — hotfixed with `default({}, true)`
  (`1df7d2549`), and the same latent gap fixed in the env-override template too (`62945bf52`).
- **`kafka_connect_replicator`-specific bugs found via the live EC2 test for §2b/#11**:
  - `kafka_connect_replicator_log_dir` was hardcoded to `/var/log/confluent/...`, never made
    `deployment_path`-aware unlike the other 8 components — immediate `Permission denied` on a
    real rootless host.
  - `rootless_service_exec` couldn't reuse the usual `*_service_overrides.ExecStart` pattern —
    replicator has no `ExecStart` key there (unlike the other 7); its start command is
    hardcoded directly in its own `.service.j2` template. Had to mirror that command instead.
  - `kafka_connect_replicator_kerberos_keytab_path` (embedded in JVM args) was a **separate**
    hardcoded var from `kafka_connect_replicator_keytab_path` (the actual copy destination) —
    under rootless these would silently diverge, so Kerberos auth would fail at runtime even
    though the keytab copy succeeded. Fixed by making the kerberos-args var reference the
    copy-destination var directly (same fix applied to consumer/producer variants).
  - RBAC pem paths (`_rbac_enabled_public_pem_path`, `_consumer_...`) were hardcoded to
    `/var/ssl/private/...`; made `deployment_path`-aware, plus fixed their directory-creation
    tasks (ownership was root:root while the file inside was `cp-kafka-connect-replicator:confluent`).
  All fixed in `65377ebc1`, live-verified end-to-end on EC2 (unit active, `ExecStart` resolved
  against `deployment_path`, REST health check on 8083 returns 200, logs under `deployment_path`,
  restart-on-config-change fires correctly).
- **Molecule test bugs found while implementing §2b's molecule fixes** (`62945bf52`–`a4537e947`):
  - `side_effect.yml` and a new `verify.yml` play used `gather_facts: false` but referenced
    `ansible_user_uid` / `ansible_env.HOME` — undefined without gathering facts, causing a
    uniform failure across all 3 scenarios (`2fbae5395`).
  - A `verify.yml` assert wrote `"'{{' not in env_content"` directly in `assert.that:` —
    Ansible templates that string, so the literal `{{` gets parsed as a new Jinja expression.
    Fixed by building the marker via `'{' * 2` in `vars:` instead (`5a3d00439`). This was the
    bug blocking CI green even after the two `rootless_bootstrap.yml` fixes below landed.
- **Two real bugs in `playbooks/rootless_bootstrap.yml` found via direct `molecule converge`
  debugging on an EC2 instance with the pinned toolchain** (after CI failed with no artifact
  access to see why) — **these are the same bugs rrbadiani's long-form follow-up comment
  (2026-08-12T11:53:57Z, see §4) had already independently identified from reading the diff**:
  1. Task ordering: "Enable systemd linger" ran *before* the Debian/Ubuntu task that installs
     `dbus-user-session`. `loginctl` needs D-Bus already present, so this deterministically
     failed on Debian/Ubuntu with `rootless_install_packages: true`. Reordered.
  2. `deployment_group`, `rootless_enable_linger`, `rootless_install_packages`,
     `rootless_bootstrap_authorized_keys_src` were set as play-level `vars:`, which outranks
     *every* inventory-sourced variable in Ansible's precedence order — inventory overrides
     were silently ignored, only `-e` on the CLI worked. Replaced with `set_fact` + `default()`.
  Both fixed in `831ee044f`, confirmed working in CI (debian10 got past bootstrap+converge for
  the first time after this), **and independently re-verified on a real (non-container) EC2
  host**: `rootless_install_packages: true` and a distinct `deployment_group` set via inventory
  now correctly take effect; full deploy succeeds; every file under `deployment_path` carries
  the right group ownership; both systemd units active.

---

## 4. rrbadiani's long-form follow-up (2026-08-12T11:53:57Z, PR issue comment)

This comment is larger than what's captured in inline comments and wasn't fully worked through
until this doc. Broken out point by point:

| Point | Status | Resolution |
|---|---|---|
| CI is red on this head, unrelated to rootless checks | 💬 | Was true at the time; superseded — CI is now green for all 3 rootless scenarios after the fixes in §3 (last confirmed run: commit `5a3d00439`, `FAILED_SCENARIOS_CNT=0`). |
| `be5d74a3`: health checks un-gated for 7 components + install-pattern path changed, unclear if re-run | 💬 | The commit's own message already documents live EC2 validation (serial/parallel routing on a live 3-node cluster; RBAC cold bootstrap co-located and separate-host, `failed=0` both; full 7-component deploy with every health check passing). The "unclear if re-run" part is now moot — molecule CI (which exercises this code path) has been re-run repeatedly since and passes. |
| `be5d74a3`: RBAC cold-bootstrap controller↔broker circularity mechanism was removed, now depends solely on `Restart=on-failure` + `wait_for` | ✅ | **Fully re-verified, including the RBAC-specific angle.** Tasks #40-43 confirmed the general serial/parallel mechanism (no `rbac_enabled`). This session's dedicated follow-up (task #47) closed the remaining gap: a genuine 3-node combined `kafka_controller`+`kafka_broker` (KRaft) greenfield cold-bootstrap with `rbac_enabled: true` (LDAP-backed MDS, `ssl_enabled: false`) and `deployment_strategy: rolling` set. Note: a greenfield deploy's `install_pattern` always resolves to parallel regardless of `deployment_strategy` (`service_state != 'running'` short-circuits the check - serial only actually activates on a brownfield redeploy, confirmed by tasks #41-42) - so this verified that *setting* `deployment_strategy: rolling` doesn't itself break an RBAC greenfield bootstrap, alongside the RBAC circularity question. Result: `failed=0` on all 3 nodes (survived one transient EC2-network blip mid-run, unrelated, resumed cleanly on retry - idempotent); `kafka-metadata-quorum describe --replication` shows a healthy quorum (1 Leader + 2 Followers + 3 Observers, zero lag on all 6); all 6 systemd units (`cp-kafka_broker`/`cp-kafka_controller` × 3) active; MDS REST API returns real role data over plain HTTP; everything under `/cp-data` owned by `cp-user` on all 3 nodes. No circularity issue found. |
| `rootless_bootstrap.yml:28-30` — play vars outrank inventory | ✅ | Same bug as §3's bootstrap fix #2 — **rrbadiani found this independently from reading the diff, before I found it via hands-on debugging.** Fixed in `831ee044f`. |
| Both molecule scenarios set `rootless_install_packages: true` in group_vars where it had no effect; neither Dockerfile installs `dbus-user-session` | ✅ | Direct consequence of the above — fixed by the same commit. The Dockerfiles don't need to install it themselves; that's the point of `rootless_install_packages: true` exercising `rootless_bootstrap.yml`'s own apt-install task, which now actually fires. |
| `deployment_group: "{{ deployment_user }}"` overrides an inventory-set group during bootstrap while deploy phase uses inventory value | ✅ | Same fix (`831ee044f`) — confirmed live on a real EC2 host: `cp-user`'s primary group is now correctly the inventory-set value throughout bootstrap *and* deploy, not silently reset to `deployment_user`. |
| `rootless_bootstrap.yml:34` — `authorized_keys_src` built as `/home/{{ ansible_user }}`, wrong for `root` (`/root`); silent `stat.exists` skip surfaces later as unrelated `Permission denied (publickey)` | ✅ | Fixed (`a34c4f7be`) — added a `root`-specific branch. Verified the resolved path is `/root/.ssh/authorized_keys` for `ansible_user=root` and unchanged (`/home/<user>/...`) for any other admin user. |
| `rbac_setup.yml:47`, `secrets_protection.yml:40` — both skip creating `ssl_file_dir_final` under rootless; masked by `ssl_enabled` creating it as a side effect; not the case for `rbac_enabled` + `ssl_enabled: false`, or secrets protection alone | ✅ | Fixed (`a34c4f7be`) — removed the `when: not (rootless_enabled\|bool)` guard on both. Under rootless, `ssl_file_dir_final` resolves under `deployment_path` (already writable), so creating it needs no privilege regardless of deploy mode. **Live re-verification of the specific `rbac_enabled` + `ssl_enabled: false` combination is still pending** (blocked mid-session on an expired AWS SSO token) — logic reasoning and the parallel `deployment_path`-writability precedent are solid, but not yet proven end-to-end for this exact combination. |
| "Nothing in this PR shows how to verify a VM deploy didn't use root" — `ansible_become: false` is a variable; task-level `become: true` outranks it; several tasks in `common/tasks/{redhat,debian}.yml` set it inline | ✅ | Checked the specific instances: all 3 inline `become: true` literals (in `redhat.yml`, `debian.yml`, `ubuntu.yml`'s pip-install tasks) are already guarded `when: not (rootless_enabled\|bool)`, so they don't fire under rootless — not a live bug. The broader methodological point is now also addressed: added `.semaphore/rootless_become_check.py` (`f0e1c0402`), a systematic static check flagging any task carrying a literal `become: true` not guarded by `rootless_enabled`. Running it against the tree surfaced one genuine pre-existing violation (`collect_support_bundle.yml`'s 7 unconditional `become: true` tasks), fixed in the same commit. |
| Docs don't cover: creating a deploy user with **no** sudoers entry (distinct from bootstrap's `cp-user`), confirming escalation is unavailable before the run, or what to check after | ✅ | **Addressed** (`10cc24827`). Added a "Proving it's actually rootless" section to `ROOTLESS_DEPLOYMENT_STEPS.md` covering all three: a dedicated no-sudoers deploy account, `sudo -u <user> sudo -n true` as the pre-run check, and post-run checks for root-owned files/processes/system-scope units. |
| No EC2 inventories committed — 3 molecule scenarios, 0 sample inventories for the equivalent RBAC-LDAP / RBAC-OAuth real-VM cases; EC2 runs referenced in the PR description aren't reproducible/reviewable | ✅ | **Addressed, not yet committed pending review.** Added `docs/sample_inventories/non_root_deployment_rbac_ldap.yml` and `non_root_deployment_rbac_oauth.yml` (placeholder-based, matching the existing `non_root_deployment.yml` convention). Both live-tested end-to-end on real EC2 (not molecule): a real standalone LDAP server (via the collection's own vendored `confluent.test.ldap` role) and a real Keycloak instance (via `confluent.test.oauth`) - not stubs. Verified: full 7-component rootless deploy `failed=0` for both; real LDAP bind auth against MDS (correct password → JWT, wrong password → 401) for `mds` and a component account; OAuth client-credentials flow against the real Keycloak realm returns a real access token; every OIDC/issuer/jwks/client config value in the broker's rendered `server.properties` traces back to the real Keycloak realm, not a placeholder; every file under `deployment_path` owned by `cp-user`, not root; all 7 systemd units active. The actual test runs used hand-built concrete inventories, not the committed sample files by hand - diffed both afterward to confirm they're identical modulo placeholder substitution (documented in `VERIFICATION_STEPS.md`). One honest caveat: the sample's `sso_*` URLs use `https://`, but what was tested end-to-end used `http://` (the throwaway Keycloak instance never got a working HTTPS listener) - the config path is a straight string pass-through so this shouldn't matter, but HTTPS itself and `sso_idp_cert_path` weren't specifically exercised. Full reproducible steps + exact commands in `sample_inventory_test_logs/VERIFICATION_STEPS.md`, raw logs alongside it. |
| Molecule scenario findings (deployment_group, privileged containers, loginctl-linger, side_effect, verify content, idempotence, CI-matrix wiring) | ✅ (mostly) | See §2b's detailed breakdown and §3. Idempotence explicitly flagged as a shared-config, project-wide concern out of scope for this PR; CI-matrix wiring confirmed as a post-merge operational step (see §5), not a code fix. |

---

## 5. Still open / not addressed in this pass

1. ~~`deployment_path` trailing-slash sanitization~~ (comment #16) — **done** (`1f4410e63`).
   Added `deployment_path_final` in `roles/variables/vars/main.yml` (same `regex_replace`
   idiom as `ssl_file_dir_final`), switched all 45 `deployment_path ~ '/...'` constructions
   plus the two direct `path:` usages in `common/tasks/main.yml` to use it;
   `rootless_bootstrap.yml` normalizes inline via its own `set_fact` block (standalone
   playbook, no access to the role-scoped var). Verified byte-for-byte unchanged for the
   empty-default and no-trailing-slash cases, and fixed for the trailing-slash case, via
   direct Jinja2 render (same templating engine Ansible uses).
2. ~~Live end-to-end test of the *actual* `docs/sample_inventories/non_root_deployment.yml`
   file~~ — **done**. Ran the literal committed file (only host groups for a single co-located
   `testhost` appended, no existing line touched) end-to-end on a fresh EC2 instance:
   `rootless_bootstrap` then `confluent.platform.all`, `failed=0` (261 tasks), all 7 systemd
   --user units active, everything under `/cp-data` owned by `cp-user`. Two stale/hung SSH
   connections hit mid-run (no `ServerAliveInterval` set) required killing + retrying with
   keepalives added - not a code issue, a test-harness gap on my end. Logs:
   `sample_inventory_test_logs/nonroot_plain_0{1,2,3}_*.log`.
3. ~~RBAC cold-bootstrap circularity for a multi-broker serial topology~~ — **independently
   re-verified, with a real finding**. Built a 4-node rootless topology (3 nodes each running
   combined `kafka_controller`+`kafka_broker` in KRaft mode, 1 node for
   `schema_registry`/`kafka_connect`/`kafka_rest`/`ksql`/`control_center`) from
   `non_root_deployment.yml`'s base vars. **Greenfield** cold-bootstrap: `failed=0` across all
   4 hosts, `kafka-metadata-quorum describe --replication` shows a healthy Leader + 2 Followers
   with matching offsets, zero lag, no `-1` anywhere - the multi-broker circularity concern is
   not an issue. Two infra-only hiccups along the way (AWS hairpin-NAT: `/etc/hosts` must map
   each node's *own* hostname to its private IP, not public - a public-IP self-connect timed
   out the quorum bootstrap the first time; and one transient SSH "no route to host" blip),
   neither a code bug. **Brownfield** re-deploy (changed `kafka_broker_custom_properties:
   {log.retention.hours: 200}`, re-ran `confluent.platform.all`): config landed correctly,
   quorum stayed healthy post-redeploy, `failed=0` - but the restart handler dispatch
   (`RUNNING HANDLER [confluent.platform.kafka_broker : Restart Kafka (rootless, systemd
   --user)]`) shows **node1, node2, node3 all restarting in the same handler invocation** -
   Ansible's default parallel dispatch, not one-at-a-time.
   **Root-caused, not a bug**: `install_pattern` (`playbooks/kafka_broker.yml`'s "Determine
   Installation Pattern" task) is `"parallel" if service_state != 'running' or
   kafka_broker_deployment_strategy == 'parallel' else "serial"` - an `or` of two independent
   gates. `kafka_broker_deployment_strategy` inherits `deployment_strategy`, which **defaults
   to `parallel`** (`roles/variables/defaults/main.yml:2430`, documented in
   `docs/VARIABLES.md`). Since gate 2 alone is `true` by default, gate 1 (`service_state`,
   the thing `be5d74a34` added rootless support for) never gets a chance to matter - serial
   restart is opt-in (`deployment_strategy: serial`) for root and rootless alike, always was;
   no existing molecule scenario sets it either. **Confirmed empirically on root too**: built
   a separate, fresh 3-node ROOT (non-rootless, `installation_method: package`) KRaft cluster
   with `deployment_strategy` deliberately left unset. Greenfield `failed=0`; brownfield
   redeploy (same `log.retention.hours` change) shows the identical pattern - single handler
   invocation (`included: ... for rnode1, rnode2, rnode3`), all 3 `changed` together, config
   landed, `failed=0`. So `be5d74a34`'s fix is doing exactly its job (root and rootless are
   now symmetric here).
   **Closed the loop**: re-ran the rootless 4-node cluster brownfield with
   `deployment_strategy: rolling` explicitly set (fresh cluster, same `log.retention.hours`
   change). Confirmed genuine one-host-at-a-time behavior this time: `PLAY [Kafka Broker
   Parallel Provisioning]` → `skipping: no hosts matched` (correctly empty), and `PLAY
   [Kafka Broker Serial Provisioning]` ran as **three separate play executions**, one per
   host (node1, then node2, then node3) - structurally impossible under parallel dispatch,
   where all hosts appear together under one play/handler block (as seen in every
   non-rolling test above). Same pattern held for `kafka_controller`. `failed=0` across all
   4 hosts, config landed (`log.retention.hours=250`). **`be5d74a34`'s rootless
   service-state fix is fully confirmed working as intended** - serial/rolling restart
   behaves correctly under rootless when explicitly requested, matching root. Logs:
   `sample_inventory_test_logs/multinode_serial_0{1..5}_*.log`,
   `sample_inventory_test_logs/root_serial_0{1,2}_*.log`,
   `sample_inventory_test_logs/rootless_rolling_0{0,1,2}_*.log`.

   **Bonus finding from this investigation, reverted for now** (unrelated to serial/parallel,
   found via a background code-audit while these tests ran): `roles/common/tasks/collect_support_bundle.yml`
   has 7 tasks with unconditional `become: true` (`support_bundle.yml`'s diagnostic-fetch
   path) that would break under rootless - no sudo access exists there by design. Had fixed
   by changing each to `become: "{{ not (rootless_enabled | bool) }}"`, syntax-checked clean -
   but reverted (`git checkout`) per explicit instruction to leave this out of the current
   change set for now. Real gap, still open, just not part of this pass.

   **Second bonus finding**: `roles/zookeeper/tasks/main.yml`'s "Validate Package
   Availability Before Removing Old Packages" task (added in `226a59424` for ANSIENG-5782)
   was entirely deleted in `65377ebc1` (an earlier commit on this branch) - not just its
   `not (rootless_enabled|bool)` guard, unlike every sibling task in that same diff, which
   only had the guard stripped. `kafka_broker`/`kafka_controller` still have this task
   intact. Looks like an accidental over-deletion rather than a deliberate choice (the
   commit's stated rationale only justifies removing the guard, and that guard was already
   redundant here anyway - `installation_method == "package"` can't co-occur with
   `rootless_enabled` regardless). Restored for zookeeper with the modernized single-condition
   guard (matching the sibling task right below it in the same file). Syntax-checked; not
   yet live-tested.
4. ~~`rbac_enabled: true` + `ssl_enabled: false` live re-verification~~ — **done**. Code fixed
   (`a34c4f7be`); AWS SSO access restored, re-run live on a fresh Rocky8 host (RHEL9 lacks
   `openldap-servers`, same reason the earlier RBAC/LDAP test used Rocky8/CentOS8) with a
   real standalone LDAP server (vendored `confluent.test.ldap` role, single `mds` bind
   account) and a co-located rootless `kafka_broker`+`kafka_controller` (KRaft). First attempt
   failed on an unrelated, expected fail-fast ("Fail if No Authentication is set") - RBAC
   needs *some* client-auth mechanism even with `ssl_enabled: false`; fixed the test inventory
   by adding `sasl_protocol: plain` (not a code issue). Second attempt: `failed=0`. Confirmed
   `ssl_file_dir_final` (`/cp-data/ssl/`) exists and is owned by `cp-user`, containing MDS's
   `public.pem`/`tokenKeypair.pem` - proving the fix works in exactly the untested combination.
   MDS's own REST API returns real role/access-policy data over plain HTTP
   (`curl http://<host>:8090/security/1.0/roles`), confirming LDAP-backed MDS came up
   correctly with no SSL. Both systemd units active; everything under `/cp-data` owned by
   `cp-user`.
5. ~~kafka_connect_replicator molecule CI run~~ — **root-caused and fixed** (`1f4410e63`).
   Re-ran via a fresh on-demand Semaphore job (converge+verify, `DESTROY_INFRA=False`,
   `MIN_ALIVE_DURATION=10h`) against real CI infra (ansible 10.7.0/ansible-core 2.17) to get
   a clean signal - local debug-host repro attempts had been contaminated first by a
   cgroups-v2/systemd-241 Docker incompatibility, then by a stale local ansible-core 2.13 pin
   missing `ansible.builtin.systemd_service`. On real CI: `rootless-rbac-ldap-rhel9` and
   `rootless-oauth-ubuntu2004` passed cleanly; `rootless-plain-debian10` failed at
   `confluent.platform.ssl : Import the CA cert into the Keystore` for
   `kafka-connect-replicator1` with `no_log`-masked output. Root cause:
   `kafka_connect_replicator_{keystore,truststore}_storepass` default to `""`, and every
   *other* `kafka_connect_replicator` molecule scenario already overrides them explicitly -
   the new rootless scenario didn't, so the empty password triggered a keytool
   shell-argument-shift bug (confirmed by replaying the exact `keytool` commands in the live
   container: an empty `-deststorepass`/`-destkeypass` pair collapses so the literal string
   `-destkeypass` becomes the real password, and a lone trailing `-storepass` with nothing
   after it hard-fails with "Command option -storepass needs an argument"). Fixed by setting
   `kafka_connect_replicator_truststore_storepass`/`keystore_storepass` explicitly in
   `molecule/rootless-plain-debian10/molecule.yml`'s group_vars, matching every other
   scenario's convention (deliberately *not* touching the role default in
   `roles/variables/defaults/main.yml`, to keep blast radius scoped to this scenario).
   Verified end-to-end on real CI infra after clearing stale cert files from the earlier
   failed attempts: `failed=0` across all 8 hosts, including `kafka-connect-replicator1`'s
   REST health check on port 8083.
6. ~~Systematic static check for un-guarded `become: true` under rootless~~ — **done**
   (`f0e1c0402`). Added `.semaphore/rootless_become_check.py` (mirroring the existing
   `rootless_privileged_tag_check.py` pattern), scanning `roles/*/tasks/*.yml` for a
   literal `become: true`/`yes` whose own or inherited `when:` never mentions
   `rootless_enabled`; wired into `sanity_tests.sh`. 13 unit tests plus the real-tree
   check, all passing. Running it against the actual tree surfaced one genuine,
   already-known violation: `collect_support_bundle.yml`'s 7 unconditional `become: true`
   tasks (the bonus finding from §5's task #40-43 investigation, previously reverted
   pending scope) - fixed now too, since otherwise this new check would land already red.
7. ~~No sudoers-free deploy-user setup / pre-run escalation check / post-run root-artifact
   check documented~~ — **done** (`10cc24827`). Added a "Proving it's actually rootless"
   section to `ROOTLESS_DEPLOYMENT_STEPS.md` covering all three: a dedicated no-sudoers
   deploy account distinct from bootstrap's admin, `sudo -u <user> sudo -n true` as the
   pre-run escalation check, and post-run checks for root-owned files/processes/system-scope
   units.
8. ~~No committed EC2 sample inventories for RBAC-LDAP / RBAC-OAuth real-VM cases~~ —
   **done**, see §2b/#17's updated row. Files created, live-verified, and committed
   (`a2725de87`).
9. **CI-matrix wiring for the 3 rootless scenarios post-merge** — confirmed this is not a
   code-side fix: `cp-ansible-tools`' scheduled `all-branch-tests` pipeline carries its
   `SCENARIO` list forward via a per-branch Semaphore artifact (`kr-<branch>-variables.sh`),
   not any file in this repo. The 3 scenarios won't automatically join the recurring matrix on
   merge — that requires an explicit on-demand run against the target branch (e.g. `7.6.x`)
   post-merge to seed it. Operational follow-up, not a PR blocker.
10. **PR description's "full `molecule test` lifecycle" claim** — should be softened; idempotence
    is deliberately disabled in the shared `.config/molecule/config.yml` (project-wide, not
    this PR's choice).
11. **Resolved - ZK/migration coverage restored on the 3 converted-to-rootless scenarios.**
    Per review feedback, rootless coverage was added to 3 *existing* scenarios in place
    (`archive-plain-debian10`, `rbac-mtls-provided-ubuntu`, `kerberos-rhel` - swapped in for
    `rbac-plain-provided-debian9`, which needs `secrets_protection_enabled` and rootless has no
    master-key recovery path for that yet) instead of keeping a separate, always-growing set of
    dedicated `rootless-*`-only scenarios (those 3 dedicated scenarios were deleted once their
    coverage was folded in here). Originally (first pass) this required hardcoding each to
    `kafka_controller` (KRaft) and dropping their original ZK toggle
    (`${KRAFT_CONTROLLER:-zookeeper}`) and `_migration` groups, since ZK had zero rootless
    support at the time. ANSIENG-5923 added rootless ZooKeeper support, closing that gap - the
    ZK toggle has now been restored in all 3 scenarios, so each covers both ZK (default) and
    KRaft (`--env-file molecule/kraft.yml`) again. `_migration`/ZK<->KRaft migration-group
    coverage remains dropped under rootless - that's a distinct, still out-of-scope concern
    (migration testing was never exercised against `rootless_enabled` and stays that way).
