openwebrx
=========

Runs [OpenWebRX+](https://github.com/luarvique/openwebrx), a web SDR
receiver, from the `slechev/openwebrxplus-softmbe` image (with the SoftMBE
codecs for digital voice).

- **The receiver has no login**; only its settings pages do, as
  `openwebrx_admin_user`. Put it on 127.0.0.1 (`openwebrx_bind_ip`) behind a
  Traefik route with SSO, or on a trusted network.
- **The admin user is created on the first start only.** Changing
  `openwebrx_admin_password` afterwards has no effect; reset it with
  `docker exec -it openwebrx openwebrx admin resetpassword admin`.
- **Settings are made on the settings pages** and kept in
  `var/settings.json` under `openwebrx_data_dir`. `openwebrx_initial_settings`
  seeds that file when it doesn't exist yet, for example with an SDR device;
  after that, the deploy leaves it alone.
- **The SDR** is either passed in (`openwebrx_device`, `/dev/bus/usb` by
  default) or reached over the network, for example from the `soapysdr`
  role's SoapyRemote server, with `openwebrx_device: ""` and a
  `soapy_remote` device in the settings.

The deploy lists the SDR devices OpenWebRX loaded, from `/status.json`.

Resources
---------

- [OpenWebRX](https://www.openwebrx.de/)
- [OpenWebRX+ Docker builder](https://github.com/0xAF/openwebrxplus-docker-builder)
