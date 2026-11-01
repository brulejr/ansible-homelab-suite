Forgejo
=======

Deploys [Forgejo](https://forgejo.org/), a self-hosted git server (a fork of
Gitea), as a Docker Compose stack with an SQLite database, and provisions its
users, an organization, repositories and SSH push mirrors through the API.

It is a separate role from `gitea` because Gitea can only push mirrors over
HTTPS with a password or token; Forgejo can push them over SSH, with a key it
generates for each mirror.

Access
------

- **Git over SSH**, on `forgejo_ssh_bind_ip:forgejo_ssh_host_port`, with keys
  only. Users' keys come from `forgejo_users`; repositories' deploy keys from
  the API (the `config_snapshot` role adds its own). Forgejo refuses RSA keys
  under 3072 bits, and a refused key fails the deploy before the organization
  and repositories exist; `ssh-keygen -lf key.pub` shows a key's size. Prefer
  ed25519.
- **The web UI and API**, on `forgejo_bind_ip:forgejo_host_port`. The role's
  own API calls go there, so it must be reachable from the host.
- **Git over HTTP** takes a password or token; `forgejo_disable_http_git`
  turns it off. HTTP basic authentication with a password is always off.

Nobody has a known password. The admin user the role works as
(`forgejo_admin_user`) and every user in `forgejo_users` get random passwords
that are never kept. The role keeps an API token for the admin user in
`forgejo_secrets_dir/api_token`, and creates a new one if it stops working.

Single sign-on
--------------

With `forgejo_reverse_proxy_auth_enabled`, Forgejo signs users in from the
`Remote-User` header a forward-auth middleware (Authelia's) sets. Publish the
web UI on loopback and route Traefik to the container:

    forgejo_bind_ip: 127.0.0.1
    forgejo_reverse_proxy_auth_enabled: true

    edge_apps:
      - name: git
        fqdn: git.example.invalid
        backend_url: "http://forgejo:3000"
        sso:
          groups: [homelab_admins]

Only users in `forgejo_users` can sign in (no auto-registration), and the
header is trusted only from the Docker network's subnet (plus
`forgejo_reverse_proxy_trusted_proxies`). Forgejo's own sign-out doesn't end
the SSO session; sign out at the portal.

Push mirrors
------------

A repository with `mirror` gets an SSH push mirror to that address, synced on
every push and every `forgejo_mirror_interval`. Forgejo generates the mirror's
key pair and keeps the private key encrypted with `forgejo_secret_key`, so
that key must never change. Each deploy prints every mirror's public key:

1. Create the remote repository, empty (GitHub doesn't create one on push).
2. Add the printed key as a deploy key with write access (on GitHub:
   Settings → Deploy keys). GitHub can't add write access to an existing
   deploy key; delete a read-only one and add it again.
3. Wait for the next push, or click "Synchronize now" under Push mirrors in
   the repository's Settings → Repository → Mirror settings. That table and
   the deploy output show the last error.

The errors GitHub returns:

- `Permission denied (publickey)`: the remote repository doesn't exist, or
  the key isn't on it.
- `The key you are authenticating with has been marked as read only`: the
  deploy key has no write access.

Push mirrors don't appear under the dashboard's "Mirrors" filter, which lists
pull mirrors, and Forgejo displays their address without the user
(`ssh://github.com/...`).

The remote's host key is accepted on first use and checked from then on.
Push mirrors force-push, so the remote must not be changed by anything else.

Secrets
-------

`forgejo_secret_key` and `forgejo_internal_token` belong in the vault.
Each is a random string of at least 32 characters:

    openssl rand -hex 32

Forgejo can also generate them, with the image:

    docker run --rm codeberg.org/forgejo/forgejo:17 forgejo generate secret SECRET_KEY
    docker run --rm codeberg.org/forgejo/forgejo:17 forgejo generate secret INTERNAL_TOKEN

Example
-------

    forgejo_secret_key: "{{ vault_forgejo_secret_key }}"
    forgejo_internal_token: "{{ vault_forgejo_internal_token }}"
    forgejo_users:
      - username: someone
        email: someone@example.invalid
        admin: true
        ssh_keys:
          - "ssh-ed25519 AAAA... someone@laptop"
    forgejo_org: homelab
    forgejo_org_owners: [someone]
    forgejo_repos:
      - name: config
        mirror: "git@github.com:someone/config.git"
