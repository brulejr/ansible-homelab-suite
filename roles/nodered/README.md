Node-RED
========

Deploys [Node-RED](https://nodered.org/) as a Docker Compose stack, published
on `nodered_bind_ip:nodered_host_port` (1880), with its data in
`nodered_data_dir`.

Login
-----

Node-RED has one of two kinds of protection:

- **Its own login**: `nodered_admin_password` turns on `adminAuth`, one user
  (`nodered_admin_user`) with full access. The role writes it as a managed
  block in `settings.js`, bcrypt-hashed with Node-RED's own bcryptjs, and
  restarts Node-RED when the block changes. An `adminAuth` of your own in
  `settings.js` fails the play.
- **Single sign-on**, with no login of its own: leave the password empty and
  publish the editor on loopback only, so that only Traefik reaches it:

      nodered_bind_ip: 127.0.0.1

      edge_apps:
        - name: nodered
          fqdn: nodered.example.invalid
          backend_url: "http://nodered:1880"
          sso:
            groups: [homelab_admins]

  The editor then has no sign-out; sign out of the SSO portal instead. Reach
  it with an SSH tunnel (`ssh -L 1880:127.0.0.1:1880 <host>`) if SSO is down.
  Flows with HTTP endpoints that other machines call stop being reachable on
  the port, too.

With neither, anyone who reaches the port has the full editor, including exec
nodes that run commands in the container.

Flow tabs
---------

`nodered_flow_tab_files` are tabs exported from the editor (Export → Current
flow, JSON), with fixed ids. A script on the host swaps them into the live
flows over the admin API, logging in when there is a password, in one deploy
that restarts only the changed tabs. Tabs built in the editor are left alone.
Each managed tab is deployed locked and labelled with ⚙, and edits made to it
in the editor are lost on the next deploy.
