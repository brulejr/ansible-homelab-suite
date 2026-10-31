config_snapshot
===============

Commits snapshots of app data that is edited in the apps themselves (wiki
pages, flows, device configuration, UI-made automations) to git repositories
on the `forgejo` role's server, every night. Secret files are committed
encrypted with [age](https://age-encryption.org/), so the repositories can be
mirrored off the host.

It complements, rather than replaces, the inventory: content Ansible deploys
stays defined there. The snapshots are history and a backup for the rest.
Restoring from them is a manual step.

How it works
------------

A systemd timer (`config_snapshot_schedule`, 03:30 by default) runs
`snapshot.py` as root. For each repository in `config_snapshot_repos`, it:

1. mirrors each source directory into its `dest` in a working copy under
   `config_snapshot_work_dir`, leaving out `exclude` patterns and removing
   files that are gone;
2. writes files matching `secrets` as `<name>.age`, encrypted to every
   `config_snapshot_age_recipients`, instead of copying them. A secret is
   encrypted again only when its content or the recipients change;
3. writes a README naming the sources and how to decrypt;
4. commits whatever changed and pushes over SSH. A push that fails is retried
   by the next run.

The job pushes with its own SSH key, which the role registers on each
repository as a deploy key with write access, through Forgejo's API and the
`forgejo` role's admin token. Run the `forgejo` role first; it creates the
repositories. The deploy takes a snapshot at the end
(`config_snapshot_run_on_deploy`), which also checks the push works.

    sudo systemctl start config-snapshot.service    # snapshot now
    journalctl -u config-snapshot.service           # what the last runs did

Patterns
--------

A pattern matches the path relative to `src` (`.storage/auth`), or with no
`/` in it, a name at any depth (`*.log`). A directory that matches takes
everything under it. Patterns are `fnmatch` globs, in which `*` also matches
`/`.

Secrets
-------

The host holds only the recipients' public keys, so it can encrypt but never
decrypt. Generate a key pair somewhere safe and keep the identity (private
key) where you keep other secrets, such as the vault:

    age-keygen -o snapshot-identity.txt

To restore a file:

    age -d -i snapshot-identity.txt path/to/file.age > path/to/file

Losing every identity makes the encrypted files unreadable. Adding or removing
a recipient encrypts every secret again on the next run.

Example
-------

    config_snapshot_git_owner: homelab
    config_snapshot_age_recipients:
      - age1qyqszqgpqyqszqgpqyqszqgpqyqszqgpqyqszqgpqyqszqgpqyqs3290gq
    config_snapshot_repos:
      - name: config
        sources:
          - src: "{{ data_dir }}/nodered"
            dest: nodered
            exclude: [node_modules, .npm, "*.backup", .sessions.json]
            secrets: [flows_cred.json, .config.runtime.json]
