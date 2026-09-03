# Nexus Role

Installs and manages Sonatype Nexus Repository Manager using Docker Compose.

This role follows the modern Docker-suite app role pattern used elsewhere in the Ansible Homelab suite, including the updated PlantUML role.

## Role Structure

```text
roles/nexus/
├── defaults/main.yml
├── handlers/main.yml
├── tasks/main.yml
├── tasks/validate.yml
├── tasks/install.yml
├── tasks/verify.yml
├── templates/docker-compose.yml.j2
└── README.md
```

## Purpose

The Nexus role provisions a Docker-based Nexus Repository Manager instance on a Docker VM such as `devops01`.

It is responsible for:

- Creating the host-side Nexus user and group
- Creating the application and data directories
- Rendering the Docker Compose file
- Starting the Nexus container
- Optionally exposing a Docker repository connector port
- Verifying that the Nexus HTTP endpoint is reachable
- Verifying that the Nexus container is running

External routing, TLS, SSO, and reverse proxy behavior should continue to be handled by the Traefik / edge routing pattern used by the suite.

## Defaults

| Variable                           | Default                   | Description                                                            |
| ---------------------------------- | ------------------------- | ---------------------------------------------------------------------- | ---------------------------------------------- |
| `nexus_enabled`                    | `true`                    | Enables or disables the role.                                          |
| `nexus_stack_name`                 | `nexus`                   | Docker Compose project name.                                           |
| `nexus_container_name`             | `nexus`                   | Docker container name.                                                 |
| `nexus_user`                       | `nexus`                   | Host user used for Nexus data ownership.                               |
| `nexus_group`                      | `nexus`                   | Host group used for Nexus data ownership.                              |
| `nexus_uid`                        | `200`                     | Host UID used for Nexus data ownership.                                |
| `nexus_gid`                        | `200`                     | Host GID used for Nexus data ownership.                                |
| `nexus_app_dir`                    | `{{ docker_dir }}/nexus`  | Directory containing the generated Docker Compose file.                |
| `nexus_data_dir`                   | `{{ data_dir }}/nexus`    | Persistent Nexus data directory.                                       |
| `nexus_image`                      | `sonatype/nexus3:latest`  | Nexus container image.                                                 |
| `nexus_restart_policy`             | `unless-stopped`          | Docker restart policy.                                                 |
| `nexus_container_port`             | `8081`                    | Internal Nexus web UI/API port.                                        |
| `nexus_docker_network`             | `{{ docker_network }}`    | External Docker network used by the container.                         |
| `nexus_bind_ip`                    | `{{ server_bind_ip }}`    | Host bind IP for published ports.                                      |
| `nexus_host_port`                  | `{{ app_port_nexus        | default(8081) }}`                                                      | Host port for Nexus web UI/API.                |
| `nexus_docker_repo_enabled`        | `true`                    | Enables publication of an additional Docker repository connector port. |
| `nexus_docker_repo_host_port`      | `{{ app_port_nexus_docker | default(10001) }}`                                                     | Host port for the Docker repository connector. |
| `nexus_docker_repo_container_port` | `10001`                   | Container port for the Docker repository connector.                    |
| `nexus_extra_environment`          | `[]`                      | Optional additional environment variables for the container.           |
| `nexus_extra_volumes`              | `[]`                      | Optional additional volume mounts for the container.                   |
| `nexus_verify_enabled`             | `true`                    | Enables role verification tasks.                                       |
| `nexus_verify_retries`             | `60`                      | Number of HTTP verification retries.                                   |
| `nexus_verify_delay`               | `5`                       | Delay, in seconds, between HTTP verification retries.                  |
| `nexus_verify_status_codes`        | `[200, 302, 401]`         | Acceptable HTTP status codes during verification.                      |

## Example Inventory

A typical `devops01` inventory entry can keep the service ports explicit:

```yaml
app_port_nexus: 8081
app_port_nexus_docker: 10001
app_port_plantuml: 8080
```

If you want to override Nexus-specific settings directly:

```yaml
nexus_enabled: true
nexus_host_port: 8081
nexus_docker_repo_enabled: true
nexus_docker_repo_host_port: 10001
```

## Docker Repository Connector Port

The role can publish an additional port for a Nexus Docker repository connector:

```yaml
nexus_docker_repo_enabled: true
app_port_nexus_docker: 10001
```

This only publishes the host/container port. The corresponding Docker hosted, proxy, or group repository connector must still be configured inside Nexus.

For example, if Nexus is configured with a Docker hosted repository using HTTP connector port `10001`, this role can expose that connector from the host as:

```text
<devops01 bind IP>:10001
```

## Traefik / Edge Routing

This role does not directly configure Traefik. It publishes Nexus on the Docker host and expects the suite's Traefik edge routing pattern to expose the application externally.

Example private inventory routing entry:

```yaml
edge_apps:
  - id: nexus
    host: "nexus.{{ domain_name }}"
    upstream_url: "http://{{ hostvars['devops01'].server_bind_ip }}:8081"
    sso: true

  - id: plantuml
    host: "plantuml.{{ domain_name }}"
    upstream_url: "http://{{ hostvars['devops01'].server_bind_ip }}:8080"
    sso: false
```

Adjust the exact fields to match the current edge routing schema used by your inventory.

## Initial Admin Password

After the first startup, Nexus creates an initial admin password in the persistent data directory.

On `devops01`:

```bash
sudo cat /opt/data/nexus/admin.password
```

If your inventory overrides `data_dir`, adjust the path accordingly:

```bash
sudo cat <data_dir>/nexus/admin.password
```

After the first login, Nexus will normally prompt you to change this password and complete initial setup.

## Deployment

From the private inventory repository, run the Docker-suite entrypoint playbook with a limit for `devops01`:

```bash
time ansible-playbook --ask-vault-pass \
  -i inventories/brulenet/hosts.yml \
  run.yml \
  --limit devops01; date
```

If running directly against the suite playbook:

```bash
time ansible-playbook --ask-vault-pass \
  -i inventories/brulenet/hosts.yml \
  playbooks/devops_servers.yml \
  --limit devops01; date
```

## Verification

On `devops01`, check the container:

```bash
docker ps --filter name=nexus
```

Check the Compose project:

```bash
docker compose -p nexus -f /opt/docker/nexus/docker-compose.yml ps
```

Check the HTTP endpoint from the host:

```bash
curl -I http://$(hostname -I | awk '{print $1}'):8081/
```

If Nexus is bound to a specific `server_bind_ip`, check that address directly:

```bash
curl -I http://<server_bind_ip>:8081/
```

Check the generated admin password:

```bash
sudo cat /opt/data/nexus/admin.password
```

## Expected Runtime Behavior

Nexus can take several minutes to become available during first startup. This is normal.

The verification task allows the following HTTP status codes by default:

```yaml
nexus_verify_status_codes:
  - 200
  - 302
  - 401
```

A `401` response can still indicate that the Nexus HTTP endpoint is alive and protected.

## Data Persistence

Nexus persistent data is stored under:

```text
{{ nexus_data_dir }}
```

By default:

```text
{{ data_dir }}/nexus
```

This directory must remain writable by the Nexus container user, which defaults to UID/GID `200`.

The role creates the host-side user and group and assigns ownership of the data directory accordingly.

## Backups

At minimum, back up the Nexus data directory:

```text
{{ nexus_data_dir }}
```

For the default layout this is usually:

```text
/opt/data/nexus
```

The generated Compose file can be recreated by Ansible, but the Nexus data directory contains repository metadata, configuration, uploaded artifacts, users, and security configuration.

## Common Troubleshooting

### Nexus container exits or fails to start

Check container logs:

```bash
docker logs nexus --tail=200
```

Check the Compose project:

```bash
docker compose -p nexus -f /opt/docker/nexus/docker-compose.yml ps
```

### Nexus reports permission errors

Confirm the data directory ownership:

```bash
sudo ls -ld /opt/data/nexus
sudo stat -c '%u:%g %n' /opt/data/nexus
```

The default expected owner is:

```text
200:200
```

You can repair ownership with:

```bash
sudo chown -R 200:200 /opt/data/nexus
```

Then restart the Compose project:

```bash
docker compose -p nexus -f /opt/docker/nexus/docker-compose.yml restart
```

### Nexus web UI is not reachable through Traefik

First verify Nexus directly from the Docker host:

```bash
curl -I http://<server_bind_ip>:8081/
```

If the direct check works, the issue is likely in the Traefik edge routing configuration rather than the Nexus role.

Check the generated Traefik route for the Nexus hostname and confirm that the upstream points to:

```text
http://<devops01 server_bind_ip>:8081
```

### Docker repository port is not working

Confirm that the host port is published:

```bash
docker port nexus
```

You should see a mapping for `10001` if `nexus_docker_repo_enabled` is true.

Remember that publishing the port is not enough. Nexus itself must also have a Docker repository connector configured for the same port.

## Operational Notes

- Keep Nexus and PlantUML as separate roles even though they run on the same VM.
- Keep external routing in Traefik rather than embedding routing behavior into this role.
- Keep Nexus data outside the Compose application directory.
- Avoid deleting `{{ nexus_data_dir }}` unless intentionally rebuilding Nexus from scratch.
- Prefer explicit service port variables in inventory so that VM-level service assignments are easy to audit.
