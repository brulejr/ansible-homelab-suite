mqtt
====

Deploys the [Mosquitto](https://mosquitto.org/) MQTT broker as a Docker
Compose stack, listening on port 1883 of the host and of the Docker network
(as `mqtt:1883`).

Users
-----

With `mqtt_users`, clients log in with a username and password, and
`mqtt_allow_anonymous: false` turns away everyone else. Every user may read
and write every topic. With no users, the broker is open to anyone who
reaches it, whatever `mqtt_allow_anonymous` says.

    mqtt_allow_anonymous: false
    mqtt_users:
      - name: homeassistant
        password: "{{ vault_mqtt_password_homeassistant }}"

Generate each password with:

    openssl rand -hex 24

Hex passwords need no escaping in the URLs some clients take
(`mqtt://user:password@host`).

Mosquitto reads only hashed passwords, and hashing salts them afresh each
time. So the role keeps the plain list root-only in
`mqtt_secrets_dir/passwd.plain`. When the list changes, it hashes it into
`mqtt_config_dir/passwd` with the image's `mosquitto_passwd` and restarts the
broker. It applies its changes before the role ends, so roles later in the
play can log in with the new users. Run it before its clients.

Turning anonymous access off
----------------------------

Clients without a login are turned away once `mqtt_allow_anonymous` is false.
To find them first, deploy once with the users but anonymous access still on:

    ansible-playbook ... -e mqtt_allow_anonymous=true

Then list the clients that connected without a username, the ones the log
shows with no `u'...'`:

    grep "New client connected" /path/to/mqtt/log/mosquitto.log | grep -v "u'"

Deploy again without the override once there are none.

The broker log shows each refused login as
`Client <id> disconnected, not authorised`.

Example
-------

    - hosts: iot_servers
      roles:
        - mqtt
