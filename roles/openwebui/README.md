# Open WebUI Role

Installs and manages Open WebUI using Docker Compose.

Open WebUI is the user-facing AI web interface. It is expected to connect to Ollama over the shared Docker network.

## Files

```text
roles/openwebui/
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

| Variable                    |                              Default | Description                                 |
| --------------------------- | -----------------------------------: | ------------------------------------------- | --------- |
| `openwebui_enabled`         |                               `true` | Enables or disables the role                |
| `openwebui_stack_name`      |                          `openwebui` | Docker Compose project name                 |
| `openwebui_container_name`  |                          `openwebui` | Container name                              |
| `openwebui_app_dir`         |         `{{ docker_dir }}/openwebui` | Directory containing generated compose file |
| `openwebui_data_dir`        |           `{{ data_dir }}/openwebui` | Persistent app data directory               |
| `openwebui_image`           | `ghcr.io/open-webui/open-webui:main` | Docker image                                |
| `openwebui_restart_policy`  |                     `unless-stopped` | Docker restart policy                       |
| `openwebui_container_port`  |                               `8080` | Internal web port                           |
| `openwebui_docker_network`  |               `{{ docker_network }}` | External Docker network                     |
| `openwebui_bind_ip`         |               `{{ server_bind_ip }}` | Host bind IP                                |
| `openwebui_host_port`       |               `{{ app_port_openwebui | default(3000) }}`                           | Host port |
| `openwebui_ollama_base_url` |                `http://ollama:11434` | Ollama API URL from inside container        |
| `openwebui_webui_auth`      |                               `true` | Enables Open WebUI authentication           |
| `openwebui_secret_key`      |                                 `""` | Required secret key                         |
| `openwebui_environment`     |                                 `{}` | Additional environment variables            |
| `openwebui_verify_enabled`  |                               `true` | Enables verification tasks                  |

## Required Secret

`openwebui_secret_key` must be provided from private inventory, preferably using Ansible Vault.

Example:

```yaml
openwebui_secret_key: !vault |
  $ANSIBLE_VAULT;1.1;AES256
  ...
```

Create an encrypted value with:

```bash
ansible-vault encrypt_string 'replace-with-long-random-secret' --name openwebui_secret_key
```

## Example Inventory

```yaml
openwebui_enabled: true
openwebui_host_port: 3000
openwebui_ollama_base_url: "http://ollama:11434"
openwebui_webui_auth: true
```

## Traefik Exposure

This role only publishes Open WebUI on the Docker host. External routing should continue to be handled by the existing `traefik` / `traefik_apps` pattern.

Example private inventory routing entry:

```yaml
edge_apps:
  - id: openwebui
    host: "ai.{{ domain_name }}"
    upstream_url: "http://{{ hostvars['aisrv01'].server_bind_ip }}:3000"
    sso: true
```

## Running

```bash
ansible-playbook site.yml --limit ai_servers --ask-vault-pass
```

## Notes

The generated `docker-compose.yml` is written with mode `0600` because it contains `WEBUI_SECRET_KEY`.
