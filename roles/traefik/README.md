Traefik
=======

Deploys [Traefik](https://traefik.io/) as a Docker Compose stack: the reverse
proxy on ports 80 and 443, with certificates from Let's Encrypt through
Cloudflare's DNS challenge. It reads routes from Docker labels and from the
files the `traefik_apps` role renders into `traefik_dynamic_dir`.

Dashboard
---------

The dashboard is served only through Traefik's own router, at
`traefik_dashboard_host` (default `traefik.<domain_name>`). No port is
published for it.

- **With basic auth** (the default): set `traefik_basic_auth_hash`, generated
  with `htpasswd -nB user`, each `$` doubled for the compose label.
- **With single sign-on**: set `traefik_dashboard_sso_middleware: "sso@file"`,
  the forward-auth middleware `traefik_apps` defines. The basic auth
  middleware is then left out. Add an access rule for the dashboard's host
  name, for example in `authelia_access_control_extra_rules`; with Authelia's
  default deny, there is none for it otherwise.
