ring-mqtt
=========

Deploys [ring-mqtt](https://github.com/tsightler/ring-mqtt), which bridges a
Ring account to MQTT. Doorbell presses, motion, lights, chimes and alarm
devices are published to the broker with Home Assistant MQTT discovery, so
the same events reach Home Assistant and anything else on the broker, such as
Node-RED. Camera live streams are served over RTSP by the go2rtc built into
the image.

ring-mqtt talks to Ring's cloud, as the Ring app does; nothing is local. No
Ring subscription is needed for events, live streams or snapshots, only for
recorded clips.

First login
-----------

Ring has no API keys: ring-mqtt holds a refresh token from a normal login.
After the first deploy there is none, so the container waits with its web UI
open:

1. Browse to `http://<server_bind_ip>:55123/`
2. Sign in with the Ring account and enter the two-factor code
3. ring-mqtt saves the token to `ring-state.json` and connects

The web UI closes once a token works, and opens again only if Ring rejects
the saved one. Ring rotates the token as it is used and ring-mqtt saves each
new one, so `ring-state.json` must be kept: the role never writes it, and
losing it means signing in again. Each login shows up as an authorized device
in the Ring app (Control Center).

Configuration
-------------

The role renders `config.json` in `ring_mqtt_data_dir` from its variables;
ring-mqtt only reads it, so edits on the host are overwritten on the next
deploy.

| Variable | Default | Description |
| --- | --- | --- |
| `ring_mqtt_mqtt_host` / `ring_mqtt_mqtt_port` | `mqtt` / `1883` | Broker Home Assistant listens on |
| `ring_mqtt_mqtt_user` / `ring_mqtt_mqtt_password` | `""` | Broker credentials, if the broker requires them |
| `ring_mqtt_ring_topic` | `ring` | Root of the device topics |
| `ring_mqtt_enable_cameras` | `true` | Publish cameras and doorbells |
| `ring_mqtt_enable_modes` | `false` | Location modes, for locations without a Ring Alarm |
| `ring_mqtt_location_ids` | `[]` | Ring locations to publish; empty for all |
| `ring_mqtt_livestream_user` / `ring_mqtt_livestream_password` | `""` | RTSP credentials; empty leaves the streams open |
| `ring_mqtt_image` | `tsightler/ring-mqtt:5.9.3` | Image (pinned) |

MQTT topics
-----------

Each device publishes under `<ring_topic>/<location id>/<category>/<device id>/`.
A doorbell press turns `ring/<location id>/camera/<device id>/ding/state`
`ON` for the ding duration (180 seconds by default), with the time and
details on `.../ding/attributes`. Node-RED can subscribe to
`ring/+/camera/+/ding/state` and act on the change to `ON`.

In Home Assistant the same press is the doorbell device's `Ding` binary
sensor.

Exposure
--------

| Service | Bound to | Port |
| --- | --- | --- |
| Login web UI (only while there is no working token) | `server_bind_ip` | `app_port_ring_mqtt` (55123) |
| RTSP live streams | `server_bind_ip` | `app_port_ring_mqtt_rtsp` (8554) |

The web UI has no authentication of its own and takes Ring credentials, so it
is not routed through Traefik: reach it from the trusted network.

Each camera's stream is `rtsp://[user:password@]<host>:8554/<device id>_live`.
The `stream_Source` attribute of the device's `Info` sensor in Home Assistant
gives it with the container's own address, which only containers on
`ring_mqtt_docker_network` can reach; from elsewhere use the host's address.
A live stream wakes the camera, which drains battery models.

Example
-------

    ring_mqtt_livestream_user: ring
    ring_mqtt_livestream_password: "{{ vault_ring_mqtt_livestream_password }}"
