Deploys [Zigbee2MQTT](https://www.zigbee2mqtt.io/) as a Docker Compose stack,
with `zigbee2mqtt_configuration` rendered as its `configuration.yaml`.

# Frontend

The frontend listens on container port 8080 and is published on
`zigbee2mqtt_bind_ip:app_port_zigbee2mqtt` (8200), by default
`server_bind_ip`. It has no login unless the configuration sets
`frontend.auth_token`, and it can control, pair and remove every device.

To put it behind single sign-on, publish it on loopback only and route
Traefik to the container:

```yaml
zigbee2mqtt_bind_ip: 127.0.0.1

edge_apps:
  - name: zigbee2mqtt
    fqdn: zigbee2mqtt.example.invalid
    backend_url: "http://zigbee2mqtt:8080"
    sso:
      groups: [homelab_admins]
```

Home Assistant uses MQTT, not the frontend, so it is not affected.

# Tools

`merge_z2m_db.py` is installed into the app directory. It merges two zigbee2mqtt
`database.db` files, e.g. when moving to a new host whose instance has already
re-interviewed a few devices. Devices are matched by `ieeeAddr` and groups by
`groupID`; entries in the newer database win, and ids are renumbered.

Stop zigbee2mqtt on both instances before copying databases.

```bash
./merge_z2m_db.py old-database.db new-database.db merged-database.db
```

# Resources

Reference

- [Zigbee2MQTT](https://www.zigbee2mqtt.io/)

GitHub

- [koenkk/zigbee2mqtt](https://github.com/Koenkk/zigbee2mqtt)

Video Tutorials

- [How to Install Zigbee2MQTT - Home Assistant or Docker](https://www.youtube.com/watch?v=4hnWqc-5q1c)
- [Zigbee2MQTT Home Assistant: 2024 How To Guide for HAOS, UnRaid & Docker](https://www.youtube.com/watch?v=3elyzOzd2lc)
