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
         backend_url: "http://nodered:1880"
         sso:
           groups: [homelab_admins]

2. `traefik_apps` puts the `sso` forward-auth middleware in front of that
   route. It defines the middleware from `traefik_sso_forward_auth_url`, which
   must be set for every host whose Traefik renders the app.
3. This role turns the same entry into an Authelia access rule: the app's
   fqdn, the group subjects, and the policy (`authelia_default_app_policy`,
   two-factor, unless the entry sets `policy`). `sso: true` admits any
   signed-in user.
4. Requests matching no rule get `authelia_access_control_default_policy`
   (deny).

Hosts that are not edge apps, such as a Traefik dashboard served from the
`traefik` role's labels, get their rules from
`authelia_access_control_extra_rules`, in Authelia's own format.

The portal needs its own edge route, without `sso`, at `authelia_fqdn`. Its
session cookie is set for `authelia_session_domain`, so every protected app
must be under that domain.

Direct ports
------------

Authelia protects host names, not ports. A request sent straight to an app's
published port skips it. So:

- **Apps with a login of their own** can keep their published port, as a way
  in when Authelia is down.
- **Apps with no login** should be published on loopback only (most roles
  have a `<role>_bind_ip` variable), with a `backend_url` that names the
  container on the Docker network Traefik shares with it, such as
  `http://nodered:1880`. Traefik then reaches them, and nothing else on the
  network does.

Passing the user on
-------------------

The middleware forwards `Remote-User`, `Remote-Groups`, `Remote-Email` and
`Remote-Name` to the app (`traefik_sso_auth_response_headers`). An app that
can trust a header signs the user in with no second login. Grafana does, with
the `iot_pipeline` role's auth proxy settings. Only trust these headers from
Traefik's address range, since anyone who reaches the app directly can send
them.

Apps that can't trust a header keep their own login behind Authelia. For one
that only needs a login to edit, like Wiki-Go, turn off its private mode and
publish it on loopback: Authelia then decides who reads.

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
one-time code to the email address on the user's LLDAP account. Without
`authelia_smtp_address`, the codes are appended to
`<authelia_config_dir>/notification.txt` on the host instead.

With SMTP set, Authelia checks that it can sign in to the server at startup,
and does not start if it can't. Every protected app then fails until that is
fixed, so check `docker logs authelia` after changing the SMTP password.

Example for Gmail, which needs an app password
(<https://myaccount.google.com/apppasswords>, with 2-Step Verification on):

    authelia_smtp_address: "submission://smtp.gmail.com:587"
    authelia_smtp_username: "someone@gmail.com"
    authelia_smtp_password: "{{ vault_authelia_smtp_password }}"
    authelia_smtp_sender: "Homelab SSO <someone@gmail.com>"

Users
-----

People are managed in LLDAP. Authelia keeps only their second factors, in its
own database, by username. So:

- **Deleting and recreating a user in LLDAP doesn't reset their second
  factor.** The new account with the same name gets the old one.
- **Users manage their own devices** at `https://<authelia_fqdn>/settings`.
- **To reset someone's second factor**, run on the host:

      docker exec authelia authelia storage user totp delete <user> --config /config/configuration.yml
      docker exec authelia authelia storage user webauthn delete <user> --all --config /config/configuration.yml

  `storage user totp generate <user>` creates a new TOTP secret from the
  command line, for when the portal's registration doesn't work.

Signing out
-----------

Apps behind Authelia have no sign-out of their own, or one that only ends
their own session. `https://<authelia_fqdn>/logout` ends the Authelia session,
which signs the user out of every protected app.

Sessions are kept in memory, so restarting the container signs everyone out.
Any change to the rendered configuration restarts it.

Troubleshooting
---------------

- **Registration shows no dialog, or nothing happens on clicking add.** No
  request reaches Authelia (`docker logs authelia` shows nothing). Try a
  private window, then clear the browser's site data for the domain.
- **Apple's Passwords app goes to "Add Verification Code" without saving.**
  It attaches codes to an existing password entry. Create the entry for
  `authelia_fqdn` first, then use Edit → Set Up Verification Code, and type
  the code it shows back into Authelia to finish.
- **No email arrives.** Check `docker logs authelia` for SMTP errors, and that
  the user's LLDAP account has their real address.

Secrets
-------

`authelia_jwt_secret`, `authelia_session_secret`,
`authelia_storage_encryption_key`, `authelia_ldap_password` and
`authelia_smtp_password` belong in the vault (see `defaults/main.yml`). Do not
change the storage encryption key once the database exists: Authelia can no
longer read it, and everyone has to register their second factor again.
