oiltank-monitor
===============

Deploys [oiltank-monitor](https://github.com/brulejr/oiltank-monitor), which
reads the oil tank's float gauge from a camera every 30 seconds and publishes
the level to Home Assistant over MQTT discovery. It is the Spring Boot
application alone, with no database and nothing kept between restarts. The
compose file is adapted from the repository's `docker/prod/compose.prod.yaml`.

How the application image is built
----------------------------------

There is no registry. On each deploy the role:

1. checks out `oiltank_monitor_git_version` over HTTPS into
   `oiltank_monitor_src_dir` (the repository is public, so no key is needed)
2. tags the image with the commit (`oiltank-monitor:<12-char sha>`); if that
   tag already exists, nothing is built
3. otherwise runs `./gradlew bootJar` in a throwaway `eclipse-temurin:21-jdk`
   container (Java is never installed on the host; the Gradle cache is the
   `oiltank-monitor-gradle` volume), then lets Compose build the upstream
   `docker/Dockerfile` around the jar, adding ffmpeg
4. removes images left from earlier commits

The image is about 1.1 GB, mostly ffmpeg. A deploy with no new commits builds
nothing. Set `oiltank_monitor_gradle_tasks: [build]` to run the tests and
refuse a failing commit, and `oiltank_monitor_force_rebuild: true` to rebuild
the same commit.

The application container is labelled
`com.centurylinklabs.watchtower.enable=false`, since there is no registry for
Watchtower to update it from.

The checkout belongs to the role: local changes on the host are discarded on
the next deploy.

Camera calibration
------------------

The gauge's region and mark rows are in the application's `application.yml`,
measured for one camera position in the full 1920x1080 frame (the Tapo
`stream1`). After the camera moves, re-measure from `GET /api/detection/debug`,
commit upstream, and redeploy.

Secrets
-------

Each secret is written to a file in `oiltank_monitor_secrets_dir` (directory
0700) and mounted as a Compose secret under `/run/secrets`, where Spring's
`configtree` import reads it. Neither appears in `docker-compose.yml` or in the
container's configured environment, so neither shows in `docker inspect`:

| Variable | Mounted as | Resolves |
| --- | --- | --- |
| `oiltank_monitor_camera_rtsp_url` | `OILTANK_CAMERA_RTSP_URL` | `oiltank.camera.rtsp-url` |
| `oiltank_monitor_mqtt_password` | `MQTT_PASSWORD` | `oiltank.publish.mqtt.password` |

The camera URL carries the camera account's credentials; URL-encode each of
them (`urlencode`, plus `replace('/', '%2F')`, since Jinja's `urlencode`
leaves slashes alone). The application redacts the URL wherever it logs or
reports it. Leave the broker password empty for an anonymous broker.

Home Assistant
--------------

The sensor is `oiltank_level` on the device `oiltank_monitor`, the identity
of the earlier prototype (`brulejr/monitor-oiltank`), so an existing entity
and its history carry over. Stop the prototype before the first deploy, or
both publish to the same entity and may knock each other off the broker with
the same client id.

Without a reachable broker the application still starts: its publish health
goes DOWN, the latest message per topic is held and retried, and Home
Assistant shows the sensor unavailable until it connects.

Exposure
--------

| Service | Bound to | Port |
| --- | --- | --- |
| Application REST API and actuator (`/mgmt`) | `server_bind_ip` | `app_port_oiltank_monitor` (8116) |

The API has no authentication and serves camera snapshots of the basement, so
the port is not routed through Traefik: reach it at
`http://<server_bind_ip>:8116` from the trusted network.

Verification
------------

The role waits up to `oiltank_monitor_verify_timeout` (180 seconds) for
`/mgmt/health` to answer 200. It answers 503 while the camera, the latest
detection or the broker is DOWN, so a deploy fails when the camera cannot be
read or the gauge cannot be found in the frame. See the response's details.

Example
-------

    oiltank_monitor_mqtt_url: "tcp://mqtt:1883"
    oiltank_monitor_camera_rtsp_url: >-
      rtsp://{{ 'camera-user' | urlencode }}:{{ vault_camera_password | urlencode | replace('/', '%2F') }}@10.0.0.10:554/stream1
    # If the broker needs credentials
    oiltank_monitor_mqtt_username: oiltank-monitor
    oiltank_monitor_mqtt_password: "{{ vault_oiltank_monitor_mqtt_password }}"
