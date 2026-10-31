ESPHome
=======

Deploys the [ESPHome](https://esphome.io/) dashboard as a Docker Compose
stack, with its device configurations in `esphome_config_dir`.

The dashboard has no login, and it shows the device configurations and their
secrets and can flash devices. It is published on
`esphome_bind_ip:app_port_esphome` (6052), by default `server_bind_ip`.

To put it behind single sign-on, publish it on loopback only and route
Traefik to the container:

    esphome_bind_ip: 127.0.0.1

    edge_apps:
      - name: esphome
        fqdn: esphome.example.invalid
        backend_url: "http://esphome:6052"
        sso:
          groups: [homelab_admins]

Reach it with an SSH tunnel (`ssh -L 6052:127.0.0.1:6052 <host>`) if SSO is
down. Home Assistant talks to the devices directly, not to the dashboard.
