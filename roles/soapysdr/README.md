soapysdr
========

Runs a [SoapyRemote](https://github.com/pothosware/SoapyRemote) server, which
offers the SDR attached to the host over the network. SoapySDR applications
reach it as a `remote` device: OpenWebRX (its `soapy_remote` source), and
desktop apps such as SDR++, GQRX or CubicSDR.

The server owns the SDR, and only one client at a time can use it. While
OpenWebRX is streaming, other clients are refused, and the other way around.
OpenWebRX holds the SDR only while someone is listening, unless background
decoding is on.

How it works
------------

- **The image is built on the host** from Debian's SoapySDR packages
  (`soapysdr_modules` lists the hardware modules; RTL-SDR by default), with
  `SoapySDRServer` built from SoapyRemote's source
  (`soapysdr_remote_version`) without Avahi. Debian's server exits when it
  can't reach an Avahi daemon, and the container has none. It is
  tagged with a hash of its Dockerfile and rebuilt only when that changes, or
  with `-e soapysdr_force_rebuild=true` for Debian's updates. Watchtower
  leaves it alone.
- **It uses the host's network.** The server listens on
  `soapysdr_bind_ip:soapysdr_port` (55132), and each stream opens its own
  socket, which published ports can't cover.
- **The kernel's DVB-T drivers are blacklisted and unloaded**
  (`soapysdr_blacklist_dvb`). They claim RTL-SDR dongles as TV tuners, and
  the SDR drivers can't open a claimed dongle.
- **The container sees the host's USB bus**, and any USB device on it, so a
  dongle can be unplugged and plugged back in without a restart.
- **The deploy checks the SDR is attached** (`soapysdr_verify_device`).

Security
--------

SoapyRemote has no login and no TLS, so it can't sit behind Traefik or an
SSO portal. Anyone who can reach the port can tune and listen through the
SDR. Keep it on a trusted network.

Connecting
----------

    SoapySDRUtil --find="driver=remote,remote=10.0.0.5"       # from a client
    docker exec soapysdr SoapySDRUtil --find="driver=rtlsdr"  # on the host

In a desktop app, use the device string
`driver=remote,remote=10.0.0.5:55132,remote:driver=rtlsdr`. The server
isn't announced over mDNS (it is built without Avahi), so give the address. Over a slow
link, add `remote:format=CS8` to halve the traffic.
