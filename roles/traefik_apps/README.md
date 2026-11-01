traefik_apps
============

Renders Traefik's dynamic configuration (file provider) for the apps published
through it: one route file per app, plus shared middlewares. Apps are listed
in `edge_apps` in each `*_servers` group's group_vars, and every Traefik that
runs this role renders the apps of all groups, or only those in
`traefik_apps_namespaces`.

Edge apps
---------

    edge_apps:
      - name: nodered            # unique within its namespace
        namespace: homelab       # or namespaces: [homelab, lab]
        fqdn: nodered.example.invalid
        backend_url: "http://{{ server_bind_ip }}:{{ app_port_nodered }}"
        sso:                     # optional: put the app behind SSO
          groups: [homelab_admins]
        middlewares: []          # optional: more Traefik middlewares
        redirect_http: true      # optional: HTTP to HTTPS redirect (default)
        streaming: false         # optional: flush responses every 100ms

Each app gets a router on the `https` entry point for its `fqdn`, a
redirecting router on `http`, and a load-balancer service for `backend_url`.
Route files are named `55-edge-route-<namespace>-<name>.yml` (no namespace
prefix for `traefik_apps_default_namespace`), and files for apps no longer
listed are removed.

Since ansible-core 2.19, another host's `edge_apps` are templated with that
host's inventory variables only, never role defaults. Every variable a
`backend_url` uses, such as an `app_port_*`, must be defined in the inventory.

Single sign-on
--------------

With `traefik_sso_forward_auth_url` set, the shared route file defines a
forward-auth middleware named `traefik_sso_middleware` (`sso`), and every app
with `sso` is routed through it. Set the URL for every host whose Traefik
renders an `sso` app; rendering one without it fails the play rather than
publishing the app unprotected. Authelia's endpoint is
`http://<host>:<port>/api/authz/forward-auth`.

The `authelia` role reads the same `edge_apps` and turns each `sso` entry into
an access rule, so an app's groups are set in one place. Other route sources,
such as the `traefik` role's dashboard labels, refer to the middleware as
`sso@file`.

The middleware passes `traefik_sso_auth_response_headers` (`Remote-User`,
`Remote-Groups`, `Remote-Email`, `Remote-Name`) on to the app.

SSO protects the host name only. An app with no login of its own should be
published on loopback, with a `backend_url` that names its container on the
Docker network Traefik shares with it (`http://nodered:1880`), so that its
port doesn't skip SSO. Such a route only works on a Traefik on the same host.
