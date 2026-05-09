# PlantUML Role

Installs and manages PlantUML Server using Docker Compose.

This role is the Docker-suite equivalent of the PlantUML application role used in the k3s suite, but it renders a Docker Compose stack instead of Kubernetes manifests.

## Files

```text
roles/plantuml/
├── defaults/main.yml
├── tasks/main.yml
├── tasks/validate.yml
├── tasks/install.yml
├── tasks/verify.yml
├── templates/docker-compose.yml.j2
├── handlers/main.yml
├── meta/main.yml
└── README.md
```

## Default Variables

| Variable                  |                          Default | Description                                 |
| ------------------------- | -------------------------------: | ------------------------------------------- | --------- |
| `plantuml_enabled`        |                           `true` | Enables or disables the role                |
| `plantuml_stack_name`     |                       `plantuml` | Docker Compose project name                 |
| `plantuml_container_name` |                       `plantuml` | Container name                              |
| `plantuml_app_dir`        |      `{{ docker_dir }}/plantuml` | Directory containing generated compose file |
| `plantuml_data_dir`       |        `{{ data_dir }}/plantuml` | Reserved persistent data directory          |
| `plantuml_image`          | `plantuml/plantuml-server:jetty` | Docker image                                |
| `plantuml_restart_policy` |                 `unless-stopped` | Docker restart policy                       |
| `plantuml_container_port` |                           `8080` | Internal PlantUML web port                  |
| `plantuml_docker_network` |           `{{ docker_network }}` | External Docker network                     |
| `plantuml_bind_ip`        |           `{{ server_bind_ip }}` | Host bind IP                                |
| `plantuml_host_port`      |            `{{ app_port_plantuml | default(8080) }}`                           | Host port |
| `plantuml_verify_enabled` |                           `true` | Enables verification tasks                  |

## Example Inventory

```yaml
plantuml_enabled: true
app_port_plantuml: 8080
```

## Traefik Exposure

This role only publishes PlantUML on the Docker host. External routing should continue to be handled by the existing `traefik` / `traefik_apps` pattern.

Example private inventory routing entry:

```yaml
edge_apps:
  - id: plantuml
    host: "plantuml.{{ domain_name }}"
    upstream_url: "http://{{ hostvars['aisrv01'].server_bind_ip }}:8080"
    sso: false
```

## Running

```bash
ansible-playbook site.yml --limit ai_servers
```

## Notes

The `plantuml_data_dir` variable is included for consistency with the Docker app role pattern, even though the basic PlantUML server container does not require persistent storage.
