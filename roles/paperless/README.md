paperless
=========

Deploys [Paperless-ngx](https://docs.paperless-ngx.com/), a document manager
that OCRs, tags and indexes scanned documents, as one Docker Compose stack:
the web server, PostgreSQL, Valkey (its Redis-compatible task broker) and,
optionally, Apache Tika and Gotenberg. The compose file is adapted from the
repository's `docker/compose/docker-compose.postgres(-tika).yml`.

Signing in through OIDC
-----------------------

With `paperless_oidc_enabled`, Paperless is a client of an OpenID Connect
provider, through django-allauth, and the username and password form is off.
For Authelia, give it a client (the authelia role's `authelia_oidc_clients`)
with the `groups` scope and Paperless's callback:

    authelia_oidc_clients:
      - id: paperless
        name: Paperless
        secret: "{{ vault_paperless_oidc_client_secret }}"
        redirect_uris:
          - "https://paperless.example.invalid/accounts/oidc/authelia/login/callback/"
        scopes: [openid, email, profile, groups]
        groups: [homelab_admins, homelab_users]

The callback's `authelia` is `paperless_oidc_provider_id`. The client's
`groups` decide who gets in at all. Within Paperless:

| Setting | Decides |
| --- | --- |
| `paperless_oidc_superuser_group` | who is a superuser; checked on every sign-in, so leaving the group takes it away |
| `paperless_oidc_sync_groups` | puts each person in the Paperless groups named like their provider groups, and takes them out of every other Paperless group |
| `paperless_oidc_redirect_to_sso` | sends the sign-in page straight to the provider |
| `paperless_logout_redirect_url` | where Sign out goes afterwards, e.g. Authelia's `https://<authelia_fqdn>/logout` |

An account is created on first sign-in, named after the provider's
`preferred_username`. A new account that isn't a superuser has no
permissions. Give them through a Paperless group named like a provider group
(for example `homelab_users`), made under *Users & Groups*, and group sync
puts people in it.

The route must not use forward-auth: the mobile apps and scripts reach the
API with a token (*My Profile → API Auth Token*), which forward-auth would
refuse. SSO accounts have no Paperless password.

Without OIDC, the form is on, and the first superuser is made with
`docker exec -it paperless createsuperuser`.

Secrets
-------

Every secret is written to a file in `paperless_secrets_dir` (directory
0700) and mounted as a Compose secret, which Paperless reads through its
`*_FILE` variables:

| Variable | Used by | Generate with |
| --- | --- | --- |
| `paperless_secret_key` | Paperless sessions and tokens | `python3 -c 'import secrets; print(secrets.token_urlsafe(64))'` |
| `paperless_db_password` | PostgreSQL, Paperless | `python3 -c 'import secrets; print(secrets.token_urlsafe(24))'` |
| `paperless_oidc_client_secret` | the OIDC client, in the provider settings file | `openssl rand -hex 32` |

Changing the secret key signs everyone out. The database password is
applied only when PostgreSQL's data directory is created; to change it later,
change it in the database too:

    docker exec -it paperless-db psql -U paperless -c "ALTER ROLE paperless PASSWORD '...'"

Exposure
--------

Only the web server publishes a port, `paperless_bind_ip` (the host's
address by default; set 127.0.0.1 behind Traefik) on `app_port_paperless`.
It joins the shared Docker network, and Traefik reaches it as
`http://paperless:8000`. Paperless accepts requests for `paperless_fqdn` only,
and trusts `X-Forwarded-Proto`, so don't publish the port anywhere Traefik
isn't the only way in.

Data
----

Bind mounts under `paperless_root_dir`:

| Directory | Holds |
| --- | --- |
| `media/` | the documents: originals, archived PDFs, thumbnails |
| `data/` | the search index, classifier and logs |
| `consume/` | the inbox: files dropped here are imported, then deleted |
| `export/` | where `docker exec paperless document_exporter ../export` writes a full export |
| `db/` | PostgreSQL |
| `broker/` | Valkey's queue |

`media/`, `data/`, `consume/` and `export/` belong to `paperless_uid`.
For a backup, run the exporter and copy `export/`: it holds the documents
and everything about them, and `document_importer` restores it into an empty
instance.

Upgrades
--------

Paperless and PostgreSQL are pinned. Set `paperless_image` to the new
release and deploy; Paperless migrates its database on start. Read the
release notes first across a major version. A new PostgreSQL major version
needs a dump and restore, or an export and import.

Example
-------

    paperless_fqdn: "paperless.example.invalid"
    paperless_bind_ip: 127.0.0.1
    paperless_oidc_enabled: true
    paperless_oidc_button_name: "Example SSO"
    paperless_oidc_server_url: "https://auth.example.invalid"
    paperless_oidc_superuser_group: homelab_admins
    paperless_logout_redirect_url: "https://auth.example.invalid/logout"
    paperless_secret_key: "{{ vault_paperless_secret_key }}"
    paperless_db_password: "{{ vault_paperless_db_password }}"
    paperless_oidc_client_secret: "{{ vault_paperless_oidc_client_secret }}"
