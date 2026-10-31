iot-pipeline
============

Deploys [iot-pipeline](https://github.com/brulejr/iot-pipeline) as one Docker
Compose stack: the Spring Boot application, PostgreSQL and Grafana. The
compose file is adapted from the repository's `docker/prod/compose.prod.yaml`.

PostgreSQL holds the registries and the stored readings, all in the
application's own `iot_pipeline` schema, so the database can later move to an
instance shared with other IoT applications.

How the application image is built
----------------------------------

There is no registry. On each deploy the role:

1. checks out `iot_pipeline_git_version` over SSH into `iot_pipeline_src_dir`
2. tags the image with the commit (`iot-pipeline:<12-char sha>`); if that tag
   already exists, nothing is built
3. otherwise runs `./gradlew bootJar` in a throwaway `eclipse-temurin:21-jdk`
   container (Java is never installed on the host; the Gradle cache is the
   `iot-pipeline-gradle` volume), then lets Compose build the upstream
   `docker/Dockerfile` around the jar
4. removes images left from earlier commits

A cold build takes about two minutes; a deploy with no new commits builds
nothing. Set `iot_pipeline_gradle_tasks: [build]` to run the tests and refuse a
failing commit, and `iot_pipeline_force_rebuild: true` to rebuild the same
commit.

The application container is labelled
`com.centurylinklabs.watchtower.enable=false`, since there is no registry for
Watchtower to update it from.

Git access over SSH
-------------------

Create a read-only deploy key for the repository:

    ssh-keygen -t ed25519 -N '' -C 'hasrv00 iot-pipeline' -f iot-pipeline-deploy

Add `iot-pipeline-deploy.pub` under the repository's *Settings → Deploy keys*,
and put the whole private key file in the vault as a block scalar:

    vault_iot_pipeline_git_ssh_private_key: |
      -----BEGIN OPENSSH PRIVATE KEY-----
      ...
      -----END OPENSSH PRIVATE KEY-----

The role writes it to `iot_pipeline_git_key_file` (mode 0600, root only).
GitHub's host key is accepted on first use into the role's own `known_hosts`
file. To use a key that is already on the host, leave
`iot_pipeline_git_ssh_private_key` empty and set `iot_pipeline_git_key_file`
to its path.

The checkout belongs to the role: local changes on the host are discarded on
the next deploy.

Database roles
--------------

On the first start with an empty data directory, PostgreSQL runs the
repository's `docker/postgres/initdb` scripts, which create:

| Role | Can | Used by |
| --- | --- | --- |
| `postgres` | everything | administration only |
| `iot_pipeline_postgres_app_username` (`iot_pipeline`) | owns the `iot_pipeline` schema | the application, whose Flyway migrations create the tables |
| `grafana_reader` | `SELECT` only | Grafana's provisioned datasource |

Secrets
-------

Every secret is written to a file in `iot_pipeline_secrets_dir` (directory
0700) and mounted as a Compose secret under `/run/secrets`. None of them
appears in `docker-compose.yml` or in a container's configured environment:

| Variable | Used by | How it is read |
| --- | --- | --- |
| `iot_pipeline_postgres_admin_password` | PostgreSQL | `POSTGRES_PASSWORD_FILE` |
| `iot_pipeline_postgres_app_password` | PostgreSQL, app | the PostgreSQL entrypoint exports it for initdb; Spring `configtree` |
| `iot_pipeline_postgres_grafana_password` | PostgreSQL, Grafana | the PostgreSQL and Grafana entrypoints export it |
| `iot_pipeline_grafana_admin_password` | Grafana | `GF_SECURITY_ADMIN_PASSWORD__FILE` |

Generate each with:

    openssl rand -base64 24 | tr -d '/+='

All four take effect only on first start: the roles are created when the data
directory is empty, and Grafana sets its admin password when it creates its
database. Changing one in the vault afterwards changes nothing until it is
changed in the database too:

    docker exec -it iot-pipeline-postgres psql -U postgres -d iot_pipeline \
      -c "ALTER ROLE grafana_reader PASSWORD '...'"
    docker exec -it iot-pipeline-grafana grafana cli admin reset-admin-password '...'

Exposure
--------

| Service | Bound to | Port |
| --- | --- | --- |
| Application REST API and console (`/ui`) | `server_bind_ip` | `app_port_iot_pipeline` (8114) |
| Grafana | `server_bind_ip` | `app_port_iot_pipeline_grafana` (8115) |
| PostgreSQL | `127.0.0.1` | `app_port_iot_pipeline_postgres` (5432) |

Neither the REST API nor the operator console at `/ui` has authentication, and
demoting a device deletes it from Home Assistant, so the port is not routed
through Traefik: open the console at `http://<server_bind_ip>:8114/ui` from the
trusted network. Reach PostgreSQL from the
host with `psql -h 127.0.0.1`, or from elsewhere over an SSH tunnel.

Data
----

Bind mounts under `iot_pipeline_data_dir`: `postgres/` and `grafana/`, each
owned by its container's user. Grafana's datasource and **Sensors** dashboard
are provisioned from the checkout (`docker/grafana/provisioning`).

Readings older than the application's `pipeline.store.retention` (30 days) are
deleted by the application as it writes. On first start, an empty database is
seeded with curated models and promoted devices from the seed files bundled in
the jar; export curation from the running system before redeploying onto an
empty database (see the application README).

Grafana single sign-on
----------------------

With `iot_pipeline_grafana_auth_proxy_enabled: true`, Grafana signs users in
from the `Remote-User` header a forward-auth middleware (such as Authelia's)
sets. They are created on their first visit as
`iot_pipeline_grafana_auth_proxy_role` (Viewer). Promote them as the admin
user, who still signs in with the login form.

Grafana trusts the header only from `iot_pipeline_grafana_auth_proxy_whitelist`,
by default Docker's address range, where Traefik's requests appear to come
from. Requests from the LAN to the published port are not trusted. If Grafana
answers "not whitelisted", check the source address in its log and adjust the
whitelist.

Example
-------

    iot_pipeline_git_ssh_private_key: "{{ vault_iot_pipeline_git_ssh_private_key }}"
    iot_pipeline_ingest_mqtt_url: "tcp://mqtt:1883"
    iot_pipeline_publish_mqtt_url: "tcp://mqtt:1883"
    iot_pipeline_postgres_admin_password: "{{ vault_iot_pipeline_postgres_admin_password }}"
    iot_pipeline_postgres_app_password: "{{ vault_iot_pipeline_postgres_app_password }}"
    iot_pipeline_postgres_grafana_password: "{{ vault_iot_pipeline_postgres_grafana_password }}"
    iot_pipeline_grafana_admin_password: "{{ vault_iot_pipeline_grafana_admin_password }}"
    # Broker credentials or other application settings
    iot_pipeline_environment:
      PIPELINE_INGEST_MQTT_USERNAME: iot-pipeline
