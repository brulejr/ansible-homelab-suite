# Ollama Role

Installs and manages Ollama using Docker Compose.

Ollama is intended to run as a backend AI model service. By default, this role does not expose Ollama directly on the host. Other containers, such as Open WebUI, should access Ollama over the shared Docker network.

## Files

```text
roles/ollama/
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

| Variable                 |                   Default | Description                                 |
| ------------------------ | ------------------------: | ------------------------------------------- |
| `ollama_enabled`         |                    `true` | Enables or disables the role                |
| `ollama_stack_name`      |                  `ollama` | Docker Compose project name                 |
| `ollama_container_name`  |                  `ollama` | Container name                              |
| `ollama_app_dir`         | `{{ docker_dir }}/ollama` | Directory containing generated compose file |
| `ollama_data_dir`        |   `{{ data_dir }}/ollama` | Persistent model/data directory             |
| `ollama_image`           |    `ollama/ollama:latest` | Docker image                                |
| `ollama_restart_policy`  |          `unless-stopped` | Docker restart policy                       |
| `ollama_container_port`  |                   `11434` | Internal Ollama API port                    |
| `ollama_docker_network`  |    `{{ docker_network }}` | External Docker network                     |
| `ollama_publish_enabled` |                   `false` | Whether to publish Ollama to the host       |
| `ollama_bind_ip`         |               `127.0.0.1` | Host bind IP when publishing is enabled     |
| `ollama_host_port`       |                   `11434` | Host port when publishing is enabled        |
| `ollama_gpu_enabled`     |                   `false` | Enables NVIDIA GPU reservation              |
| `ollama_environment`     |                      `{}` | Additional environment variables            |
| `ollama_verify_enabled`  |                    `true` | Enables verification tasks                  |

## Example Inventory

```yaml
ollama_enabled: true
ollama_data_dir: "{{ data_dir }}/ollama"

# Recommended default: keep Ollama internal only
ollama_publish_enabled: false

# Enable only if this Docker host has NVIDIA GPU runtime configured
ollama_gpu_enabled: false
```

## Open WebUI Integration

Open WebUI should connect to Ollama using the shared Docker network:

```yaml
openwebui_ollama_base_url: "http://ollama:11434"
```

## Running

```bash
ansible-playbook site.yml --limit ai_servers
```

## Notes

This role assumes the shared Docker network already exists. In this suite, that should normally be handled by the base Docker role.
