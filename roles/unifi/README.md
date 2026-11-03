UniFi Network Application
=========================

Deploys the [UniFi Network Application](https://ui.com/download/releases/network-server)
(the self-hosted UniFi controller) from the
[linuxserver.io image](https://github.com/linuxserver/docker-unifi-network-application),
with the MongoDB database it needs, as a Docker Compose stack.

Database
--------

MongoDB runs in its own container, on the stack's private network only. On
its first start, with an empty data directory, `init-mongo.sh` creates the
application's user. The passwords, `unifi_db_root_password` and
`unifi_db_password`, are mounted as Compose secrets and appear nowhere else;
changing them later doesn't change the database's.

`unifi_db_image` is pinned to `mongo:7.0`. MongoDB 8.0 refuses to start on
Linux 6.19 and newer ([SERVER-121912](https://jira.mongodb.org/browse/SERVER-121912)),
and MongoDB never upgrades its files across major versions by itself: going
from 7.0 to 8.0 later means setting `featureCompatibilityVersion` first.
MongoDB 5.0 and newer needs a CPU with AVX.

Exposure
--------

| Service | Bound to | Port |
| --- | --- | --- |
| Web UI and API (HTTPS, self-signed) | `unifi_ui_bind_ip` | `app_port_unifi` (8443) |
| Device inform | `unifi_bind_ip` | 8080/tcp |
| STUN | `unifi_bind_ip` | 3478/udp |
| Anything in `unifi_extra_ports` | as given | |

Both bind addresses default to `server_bind_ip`. The inform and STUN ports
can't be remapped: the controller hands devices its own port numbers.

To put the web UI behind SSO, publish it on loopback and route Traefik to
the container. UniFi has no header or OIDC sign-in, so its own login stays:

    unifi_ui_bind_ip: 127.0.0.1

    edge_apps:
      - name: unifi
        fqdn: unifi.example.invalid
        backend_url: "https://unifi:8443"
        backend_tls_insecure: true
        sso:
          groups: [homelab_admins]

Inform host
-----------

Inside Docker, the application only knows its container's address, and
would hand that to devices. Set **Inform Host Override** to an address the
devices can reach, such as `unifi_bind_ip`. UniFi moves the option between
releases: in 10.6 it's under UniFi Devices (not Settings) → Device Updates &
Settings; in 9.0, under Settings. It's part of the configuration, so a
restored backup carries it. Devices that can't be told otherwise can be
pointed at it over SSH:

    set-inform http://<unifi_bind_ip>:8080/inform

First run
---------

The first visit to the web UI starts the setup wizard, which can also
restore a backup (`.unf`) from another controller of the same or an older
version.

Example
-------

    unifi_ui_bind_ip: 127.0.0.1
    unifi_db_root_password: "{{ vault_unifi_db_root_password }}"
    unifi_db_password: "{{ vault_unifi_db_password }}"
