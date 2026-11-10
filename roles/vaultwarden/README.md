Vaultwarden
===========

Deploys [Vaultwarden](https://github.com/dani-garcia/vaultwarden), a
Bitwarden-compatible password manager server, as a Docker Compose stack. The
Bitwarden apps, browser extensions and web vault all work with it.

Settings, secrets among them, go in `vaultwarden.env` in the app directory,
readable by root only. The data directory (`vaultwarden_data_dir`, mode 0700)
holds everything else.

Exposure
--------

| Service | Bound to | Port |
| --- | --- | --- |
| Web vault, API and live sync | `vaultwarden_bind_ip` | `app_port_vaultwarden` (8109) |

Put it on 127.0.0.1 and route Traefik to the container by name:

    vaultwarden_bind_ip: 127.0.0.1
    vaultwarden_domain: "https://vaultwarden.example.invalid"

    edge_apps:
      - name: vaultwarden
        fqdn: vaultwarden.example.invalid
        backend_url: "http://vaultwarden:80"

`vaultwarden_domain` must be the edge route's URL. Leave `sso` (forward-auth)
off the route: the apps and extensions call the API directly and can't sign in
through a portal.

Admin page
----------

`/admin` is off until `vaultwarden_admin_token` is set to an Argon2 PHC
string, which the validation checks:

    docker run --rm -it vaultwarden/server /vaultwarden hash

Settings saved there are written to `config.json` in the data directory and
override the environment from then on. `vaultwarden_admin_config_disabled`
makes them read-only, leaving this role in charge.

Signing in through Authelia
---------------------------

Vaultwarden can sign people in through an OIDC provider. Give Authelia a
client (the `authelia` role's `authelia_oidc_clients`) with the redirect URI
`<vaultwarden_domain>/identity/connect/oidc-signin`, and Vaultwarden the same
client:

    vaultwarden_sso_enabled: true
    vaultwarden_sso_authority: "https://auth.example.invalid"
    vaultwarden_sso_client_secret: "{{ vault_vaultwarden_oidc_client_secret }}"

- **The master password stays.** SSO replaces the email and password step;
  the vault is still unlocked with the master password, which never leaves
  the client. `vaultwarden_sso_only` turns off the password step.
- `vaultwarden_sso_authority` must match the provider's `issuer` exactly.
  Vaultwarden fetches its discovery document, so the name must resolve to,
  and be reachable from, the container. The deploy checks this.
- The client needs `id_token_claims: [email, email_verified, name,
  preferred_username]`. Vaultwarden refuses a sign-in whose email isn't
  verified.
- With `vaultwarden_sso_signups_match_email`, a first SSO sign-in is linked to
  the existing account with the same email. With sign-ups off, someone with
  no account must be invited first.
- `vaultwarden_sso_auth_only_not_session` (on) asks the provider only at
  sign-in; Vaultwarden keeps the session. The client then needs no
  `offline_access` scope or refresh token, and people already signed in carry
  on while the provider is down.
- The client's `groups` decide who may use SSO. Anyone with an account can
  still sign in with their email and master password unless SSO is the only
  way in.

Backups
-------

Everything is under `vaultwarden_data_dir`: `db.sqlite3` (copy it with
SQLite's backup API while Vaultwarden runs), `rsa_key.pem`, `attachments/`,
`sends/` and `config.json`. `icon_cache/` and `tmp/` can be left out. Vault
items are encrypted by the clients, but the database also holds password
hashes, 2FA secrets and the admin page's settings, so keep copies encrypted.

Example
-------

    vaultwarden_image: "vaultwarden/server:1.37.5"
    vaultwarden_bind_ip: 127.0.0.1
    vaultwarden_domain: "https://vaultwarden.example.invalid"
    vaultwarden_admin_token: "{{ vault_vaultwarden_admin_token }}"
    vaultwarden_smtp_host: smtp.example.invalid
    vaultwarden_smtp_from: vaultwarden@example.invalid
    vaultwarden_smtp_username: vaultwarden@example.invalid
    vaultwarden_smtp_password: "{{ vault_vaultwarden_smtp_password }}"
