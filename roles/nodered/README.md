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

MQTT broker logins
------------------

`nodered_mqtt_broker_logins` sets the login of broker config nodes built in
the editor, found by id (the node's info panel shows it). Only the login
changes; the rest of the node stays as built. A script on the host sets it
over the admin API, in a full deploy that reconnects every flow. Node-RED
never shows a stored password, so the script keeps a digest of each login it
set in `nodered_app_dir/broker_logins.json`, and changes a node again only
when its login differs.

    nodered_mqtt_broker_logins:
      - id: mqtt_broker_brulenet
        user: nodered
        password: "{{ vault_mqtt_password_nodered }}"

Flow tabs
---------

`nodered_flow_tab_files` are tabs exported from the editor (Export → Current
flow, JSON), with fixed ids. A script on the host swaps them into the live
flows over the admin API, logging in when there is a password, in one deploy
that restarts only the changed tabs. Tabs built in the editor are left alone.
Each managed tab is deployed locked and labelled with ⚙, and edits made to it
in the editor are lost on the next deploy.

A tab that uses nodes from a palette module needs the module in
`nodered_palette_modules`: Node-RED starts no flows at all while a node type
is missing, so a rebuilt Node-RED must get the module before the tab. Missing
modules are installed first, at the version given; an installed one is left
at whatever version it has.

    nodered_palette_modules:
      - name: node-red-contrib-cron-plus
        version: "2.1.0"

