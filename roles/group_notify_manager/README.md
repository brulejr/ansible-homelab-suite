group-notify-manager
====================

Deploys [group-notify-manager](https://github.com/brulejr/group-notify-manager),
which sends scheduled notifications to groups over groups.io, Discord and
plugins, as one Docker Compose stack: the Spring Boot application and
PostgreSQL. The compose file is adapted from the repository's
`docker/prod/compose.prod.yaml`, and the role is modelled on `iot_pipeline`.

How the application image is built
----------------------------------

There is no registry. On each deploy the role:

1. checks out `group_notify_manager_git_version` over SSH into
   `group_notify_manager_src_dir`
2. tags the image with the commit (`group-notify-manager:<12-char sha>`); if
   that tag already exists, nothing is built
3. otherwise runs `./gradlew bootJar` in a throwaway `eclipse-temurin:21-jdk`
   container (Java is never installed on the host; the Gradle cache is the
   `group-notify-manager-gradle` volume), then lets Compose build the upstream
   `docker/Dockerfile` around the jar
4. removes images left from earlier commits

Set `group_notify_manager_gradle_tasks: [build]` to run the tests and refuse a
failing commit, and `group_notify_manager_force_rebuild: true` to rebuild the
same commit. The application container is labelled
`com.centurylinklabs.watchtower.enable=false`, since there is no registry for
Watchtower to update it from.

Git access over SSH
-------------------

Create a read-only deploy key for the repository (GitHub allows a key on one
repository only, so this is not iot-pipeline's):

    ssh-keygen -t ed25519 -N '' -C '<host> group-notify-manager' -f group-notify-manager-deploy

Add `group-notify-manager-deploy.pub` under the repository's
*Settings → Deploy keys*, and put the whole private key file in the vault as a
block scalar:

    vault_group_notify_manager_git_ssh_private_key: |
      -----BEGIN OPENSSH PRIVATE KEY-----
      ...
      -----END OPENSSH PRIVATE KEY-----

The role writes it to `group_notify_manager_git_key_file` (mode 0600, root
only). GitHub's host key is accepted on first use into the role's own
`known_hosts` file. The checkout belongs to the role: local changes on the host
are discarded on the next deploy.

Signing in
----------

The application has no login of its own. It believes the `Remote-User`,
`Remote-Groups`, `Remote-Name` and `Remote-Email` headers that Traefik copies
from Authelia, so it must be reachable only through Traefik. Its port is on
127.0.0.1 by default (`group_notify_manager_bind_ip`), and Traefik reaches the
container over the shared Docker network:

    edge_apps:
      - name: notify
        fqdn: notify.example.invalid
        backend_url: "http://group-notify-manager:5002"
        sso:
          groups: [homelab_admins, homelab_users]

The `sso` groups decide who reaches the application at all. Within it:

| Setting | Decides |
| --- | --- |
| `group_notify_manager_admin_group` | who sees and manages every group's notifications, provisions delivery instances and reads `/mgmt` |
| `group_notify_manager_group_pattern` | which of a user's groups hold notifications; a regular expression the whole name must match |
| `group_notify_manager_trusted_proxies` | where the headers are believed from; empty (any sender) by default, see below |
| `group_notify_manager_logout_url` | the console's sign-out link, e.g. Authelia's `https://<authelia_fqdn>/logout` |

Set the pattern: the default, every group, also offers the admin group and
LLDAP's own groups as notification groups.

Leave `group_notify_manager_trusted_proxies` empty. The application checks
the sender's address after Spring has replaced it with the first
`X-Forwarded-For` address (its `server.forward-headers-strategy` is
`framework`). So it sees the browser, never Traefik, and any address range
there refuses every sign-in with a 401, logging "not a trusted proxy". The
loopback-only port is what keeps anyone else from setting the headers.

Secrets
-------

Every secret is written to a file in `group_notify_manager_secrets_dir`
(directory 0700) and mounted as a Compose secret under `/run/secrets`. None of
them appears in `docker-compose.yml` or in a container's configured
environment:

| Variable | Used by | How it is read | Generate with |
| --- | --- | --- | --- |
| `group_notify_manager_postgres_admin_password` | PostgreSQL | `POSTGRES_PASSWORD_FILE` | `openssl rand -base64 24 \| tr -d '/+='` |
| `group_notify_manager_postgres_app_password` | PostgreSQL, app | the PostgreSQL entrypoint exports it for initdb; Spring `configtree` | the same |
| `group_notify_manager_secret_key` | app | Spring `configtree`, as `NOTIFY_SECRET_KEY` | `openssl rand -base64 32` |
| `group_notify_manager_mail_password` | app, optional | Spring `configtree`, as `MAIL_PASSWORD` | from the mail provider |

The secret key encrypts the credentials admins enter on delivery instances (a
groups.io API key, a Discord webhook URL). Never change it, and back it up
beside the database: without it, every stored credential must be entered
again.

Both PostgreSQL passwords take effect only on the first start with an empty
data directory, when the repository's `docker/postgres/initdb` creates the
application's role and its `group_notify` schema. To change one afterwards,
change it in the database too:

    docker exec -it group-notify-manager-postgres psql -U postgres -d group_notify \
      -c "ALTER ROLE group_notify PASSWORD '...'"

Exposure
--------

| Service | Bound to | Port |
| --- | --- | --- |
| Application console, REST API and `/mgmt` | `group_notify_manager_bind_ip` (127.0.0.1) | `app_port_group_notify_manager` (8121) |
| PostgreSQL | `127.0.0.1` | `app_port_group_notify_manager_postgres` (5433) |

Data
----

Bind mounts under `group_notify_manager_data_dir`: `postgres/`, owned by its
container's user, and `plugins/`, for extra delivery plugin jars, mounted
read-only at `/app/plugins` (see the application's `docs/plugins.md`). The
bundled groups.io and Discord plugins need nothing there.

Example
-------

    group_notify_manager_git_ssh_private_key: "{{ vault_group_notify_manager_git_ssh_private_key }}"
    group_notify_manager_postgres_admin_password: "{{ vault_group_notify_manager_postgres_admin_password }}"
    group_notify_manager_postgres_app_password: "{{ vault_group_notify_manager_postgres_app_password }}"
    group_notify_manager_secret_key: "{{ vault_group_notify_manager_secret_key }}"
    group_notify_manager_admin_group: homelab_admins
    group_notify_manager_group_pattern: "notify_.*"
    group_notify_manager_logout_url: "https://auth.example.invalid/logout"
