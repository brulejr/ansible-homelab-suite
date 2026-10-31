Authelia
========

Deploys [Authelia](https://www.authelia.com/) as a Docker Compose stack: a
single sign-on portal with two-factor authentication that Traefik consults,
through a forward-auth middleware, before letting a request through to an app.
Users and groups come from LLDAP (the `lldap` role).

How the pieces fit
------------------

1. An `edge_apps` entry sets `sso`:

       - name: nodered
         namespace: homelab
         fqdn: nodered.example.invalid
         backend_url: "http://{{ server_bind_ip }}:{{ app_port_nodered }}"
         sso:
           groups: [homelab_admins]

2. `traefik_apps` puts the `sso` forward-auth middleware in front of that
   route. It defines the middleware from `traefik_sso_forward_auth_url`, which
   must be set for every host whose Traefik renders the app.
3. This role turns the same entry into an Authelia access rule: the app's
   fqdn, the group subjects, and the policy (`authelia_default_app_policy`
   unless the entry sets `policy`). `sso: true` admits any signed-in user.
4. Requests matching no rule get `authelia_access_control_default_policy`
   (deny).

The portal needs its own edge route, without `sso`, at `authelia_fqdn`. Its
session cookie is set for `authelia_session_domain`, so every protected app
must be under that domain.

Apps keep their published ports, and a request sent straight to one bypasses
Traefik and Authelia. Only the hostnames are protected.

LDAP
----

Authelia binds to LLDAP as `authelia_ldap_user_id` (default `authelia`). Create
that account with `lldap_service_accounts`, using the same password as
`authelia_ldap_password`. In `lldap_password_manager` the portal's "reset
password" works; in `lldap_strict_readonly`, set
`authelia_password_reset_enabled: false`.

Notifications
-------------

Registering a TOTP app or a security key, and resetting a password, send a
one-time code. Without `authelia_smtp_address`, the codes are appended to
`<authelia_config_dir>/notification.txt` on the host.

Secrets
-------

`authelia_jwt_secret`, `authelia_session_secret`,
`authelia_storage_encryption_key` and `authelia_ldap_password` belong in the
vault (see `defaults/main.yml`). Do not change the storage encryption key once
the database exists: Authelia can no longer read it, and everyone has to
register their second factor again.

Sessions are kept in memory, so restarting the container signs everyone out.
