Linkwarden
==========

Deploys [Linkwarden](https://linkwarden.app/), a bookmark manager that keeps
an archived copy of each link (screenshot, PDF, readable view), with the
PostgreSQL database it needs, as a Docker Compose stack.

Database
--------

PostgreSQL runs in its own container, on the stack's private network only.
Its password, `linkwarden_db_password`, is mounted as a Compose secret, and
takes effect only when the data directory is first initialised; changing it
later doesn't change the database's. `linkwarden_db_image` is pinned to a
major release: PostgreSQL doesn't upgrade its files across majors by itself.

Linkwarden migrates the database each time it starts, so take a backup before
raising `linkwarden_image`.

Exposure
--------

| Service | Bound to | Port |
| --- | --- | --- |
| Web UI and API | `linkwarden_bind_ip` | `app_port_linkwarden` (8118) |

Put it on 127.0.0.1 and route Traefik to the container by name:

    linkwarden_bind_ip: 127.0.0.1

    edge_apps:
      - name: linkwarden
        fqdn: linkwarden.example.invalid
        backend_url: "http://linkwarden:3000"

`linkwarden_fqdn` must match the edge route's host name: sign-in redirects
are built from it.

Signing in through Authelia
---------------------------

Linkwarden can't take its user from a forward-auth header, but it can sign
in through Authelia's OIDC provider. Give Authelia a client (the `authelia`
role's `authelia_oidc_clients`) with the redirect URI
`https://<linkwarden_fqdn>/api/v1/auth/callback/authelia`, and Linkwarden the
same client:

    linkwarden_authelia_enabled: true
    linkwarden_authelia_client_secret: "{{ vault_linkwarden_oidc_client_secret }}"
    # Leave Authelia the only way in
    linkwarden_credentials_enabled: false
    linkwarden_registration_disabled: true

- Linkwarden reads the user's email and name from the ID token, so the
  client needs `id_token_claims: [email, email_verified, name,
  preferred_username]`.
- The client's `groups` decide who gets in. Leave `sso` off the edge route:
  a forward-auth middleware in front would also block the browser extension
  and the mobile app, which use access tokens.
- Accounts are created on first sign-in; the first one (user id 1) is the
  administrator. `linkwarden_new_sso_users_disabled` stops new ones.
- Linkwarden's server fetches `linkwarden_authelia_wellknown_url`, so that
  name must resolve to, and be reachable from, the container. The deploy
  checks this.
- With password sign-in off, Linkwarden can't be used while Authelia is down.

Not covered
-----------

- Meilisearch, which Linkwarden can use for faster, fuller search. Without
  it, Linkwarden searches its database.
- Backups. The database is under `linkwarden_db_dir` and the archives under
  `linkwarden_archive_dir`.

Example
-------

    linkwarden_bind_ip: 127.0.0.1
    linkwarden_nextauth_secret: "{{ vault_linkwarden_nextauth_secret }}"
    linkwarden_db_password: "{{ vault_linkwarden_db_password }}"
