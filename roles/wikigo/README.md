Wiki-Go
=======

Deploys [Wiki-Go](https://github.com/leomoon-studios/wiki-go), a flat-file
Markdown wiki, as a Docker Compose stack.

TLS is expected to be terminated by Traefik: add an `edge_apps` entry pointing
at `http://<server_bind_ip>:<app_port_wikigo>` in the inventory.

Configuration
-------------

The role renders the full `config.yaml` from `wikigo_*` variables (see
`defaults/main.yml`), including users and access rules. The inventory is the
source of truth: changes made in the Wiki-Go admin UI are overwritten on the
next deploy.

The template mirrors the file Wiki-Go writes itself. Wiki-Go rewrites
`config.yaml` on startup whenever its output differs, so if a new image release
adds settings, update `templates/config.yaml.j2` to match (otherwise each deploy
reports a change and restarts the container). The image is pinned to a minor
release line for this reason.

At least one admin user is required. Passwords are bcrypt hashes and belong in
the vault:

    htpasswd -nbBC 14 "" 'secret' | tr -d ':\n'

When `wikigo_trust_docker_network` is true (default), the IPv4 subnet of the
Docker network is added to `trusted_proxies`, so client IPs forwarded by Traefik
are used for logging and login bans.

Example
-------

    wikigo_title: "📚 Homelab Wiki"
    wikigo_private: true
    wikigo_users:
      - username: admin
        password: "{{ vault_wikigo_admin_password_hash }}"
        role: admin
    wikigo_access_rules:
      - pattern: "/public/**"
        access: public
        description: "Visible to everyone"
