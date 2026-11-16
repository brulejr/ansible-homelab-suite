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

Cloudflare token
----------------

`traefik_cloudflare_dns_token` (default `vault_cloudflare_dns_token`) is the
Cloudflare API token for the DNS challenge. Create it in Cloudflare as a
custom token (My Profile → API Tokens) with **Zone → Zone → Read** and
**Zone → DNS → Edit**, both on the one zone it needs, and nothing else.
Traefik needs the first to look the zone up. It is written to `traefik_secrets_dir/cf_dns_api_token` (root only) and
read through `CF_DNS_API_TOKEN_FILE`, so it is in neither
`docker-compose.yml` nor `docker inspect`. Changing it restarts Traefik.

A host that faces the internet should have a token of its own, so a
compromise there is undone by revoking one token rather than every host's.

Debug endpoints
---------------

`traefik_api_debug` (default `true`) adds Traefik's `/debug/` endpoints to the
dashboard's router. Set it to `false` on a host that faces the internet.
