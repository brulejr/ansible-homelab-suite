# docker2mqtt Role

Installs and manages [docker2mqtt](https://github.com/miaucl/docker2mqtt) using Docker Compose.

docker2mqtt watches the host's Docker events and stats and publishes them to MQTT, with Home Assistant MQTT discovery so each container appears as a device named `<host> Docker <container>`.

## Entities per container

| Entity | Meaning |
|---|---|
| `binary_sensor.<host>_docker_<container>_state` | `on` while running, `off` when stopped |
| `binary_sensor.<host>_docker_<container>_health` | `on` healthy, `off` unhealthy, unknown without a `HEALTHCHECK` |
| `sensor.<host>_docker_<container>_cpu` | CPU % |
| `sensor.<host>_docker_<container>_memory` | Memory used (MB) |
| `sensor.<host>_docker_<container>_network_input_rate` / `_output_rate` | Network rates (MB/s) |

Block I/O and cumulative network counters are published as well.

## Variables

| Variable | Default | Description |
|---|---|---|
| `docker2mqtt_mqtt_host` | `""` (required) | Broker Home Assistant listens on |
| `docker2mqtt_mqtt_port` | `1883` | Broker port |
| `docker2mqtt_mqtt_user` / `docker2mqtt_mqtt_password` | `""` | Broker credentials, if the broker requires them |
| `docker2mqtt_hostname` | `inventory_hostname` | Host name used in topics and entity ids |
| `docker2mqtt_image` | `ghcr.io/miaucl/docker2mqtt:2.6.1` | Image (pinned) |
| `docker2mqtt_stats_record_seconds` | `30` | Stats averaging window |
| `docker2mqtt_destroyed_container_ttl` | `86400` | Seconds before a removed container's entities are dropped |
| `docker2mqtt_container_blacklist` | `[]` | Container names or regexes to ignore |

## Example Playbook

```yaml
- hosts: servers
  roles:
    - docker
    - docker2mqtt
```
