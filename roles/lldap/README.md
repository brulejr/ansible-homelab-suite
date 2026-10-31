LLDAP
=====

Deploys [LLDAP](https://github.com/lldap/lldap), a lightweight LDAP server
with a web UI for managing users and groups, as a Docker Compose stack. It is
the user directory behind the `authelia` role.

The web UI is published on `server_bind_ip:app_port_lldap` for Traefik: add an
`edge_apps` entry for it. LDAP itself (port 3890) is not published; clients on
the Docker network reach it as `ldap://lldap:3890`.

Bootstrap
---------

People are managed in the web UI. The role creates only what applications
depend on, using LLDAP's bootstrap script:

- `lldap_groups`: groups, such as the ones Authelia's access rules name
- `lldap_service_accounts`: accounts that applications bind as, with their
  password reset to the inventory value

The script runs only when those lists change or a service account can no
longer log in (for example after the database was recreated). It never
deletes users, groups or memberships it does not know about; removing an
entry from the inventory leaves it in LLDAP.

Secrets
-------

`lldap_jwt_secret`, `lldap_key_seed` and `lldap_admin_password` belong in the
vault (see `defaults/main.yml`). The admin password is applied when the
database is created only. The bootstrap logs in with it, so if you change the
password in the web UI, change it in the vault as well.

Example
-------

    lldap_jwt_secret: "{{ vault_lldap_jwt_secret }}"
    lldap_key_seed: "{{ vault_lldap_key_seed }}"
    lldap_admin_password: "{{ vault_lldap_admin_password }}"
    lldap_groups:
      - homelab_admins
      - homelab_users
    lldap_service_accounts:
      - id: authelia
        email: authelia@example.invalid
        display_name: Authelia
        password: "{{ vault_authelia_ldap_password }}"
        groups: [lldap_password_manager]
