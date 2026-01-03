# ansible-homelab-suite

Public, reusable Ansible **core** for homelabs.

This repository intentionally contains **no environment-specific inventory**, **no secrets**, and (by design) can be reused across multiple environments by pairing it with a **private inventory repository**. The private repo contains hostnames/IPs, VLAN details, DNS overrides, and vaulted secrets.

---

## What this repo is (and is not)

### ✅ This repo **is**

- A **public core library** of roles (Traefik, Keycloak, Portainer, apps, etc.)
- A generic `site.yml` that applies roles to host groups (`admin_servers`, `ha_servers`, etc.)
- Public-safe defaults in `group_vars/all/all.yml`
- Designed to be consumed from a private repo via **Git submodule**

### ❌ This repo is **not**

- An inventory repo
- A secrets repo
- A “single checkout that contains your real network details”

---

## Architecture: Edge Gateway + Central SSO (local + VPN only)

This project is designed for a **central Edge Gateway** that provides:

- HTTPS for all apps
- centralized SSO policy
- centralized routing (Traefik file provider)
- no direct access to backend app ports from user networks

**No WAN access** is assumed. Access is either:

- local LAN/WIFI, or
- remote via WireGuard VPN on pfSense (treated like LAN access)

### Key principles

- **Only the Edge VIP** is reachable by users on ports **80/443**
- All apps run on backend servers and publish ports only on **SERVER VLAN IPs**
- pfSense rules prevent bypassing the gateway and SSO
- An `id_server` is management-only (MGMT), and **does not** expose port 80

---

## Repository layout (public core)

```
ansible-homelab-suite/
├─ README.md
├─ site.yml
├─ group_vars/
│  └─ all/
│     └─ all.yml
└─ roles/
   ├─ common/
   ├─ docker/
   ├─ watchtower/
   ├─ traefik/
   ├─ sso_gateway/
   ├─ keycloak/
   ├─ portainer/
   ├─ homarr/
   ├─ wikijs/
   ├─ vaultwarden/
   ├─ nexus/
   ├─ homeassistant/
   ├─ nodered/
   ├─ mqtt/
   └─ jellyfin/
```

### `group_vars/all/all.yml` (public-safe defaults only)

This file is intentionally minimal and safe to publish. The private inventory overrides these values.

---

## How you run this project (recommended pattern)

You run Ansible from a **private inventory repo** that includes this repo as a **git submodule**.

---

# Private repo setup (recommended)

Create a private repository (example name: `ansible-homelab-inventory`) and add this public repo as a submodule.

## 1) Create the private repo and add the submodule

```bash
mkdir -p ansible-homelab-inventory
cd ansible-homelab-inventory
git init

mkdir -p vendor
git submodule add -b feature/edge_gateway_central_sso \
  https://github.com/brulejr/ansible-homelab-suite.git \
  vendor/ansible-homelab-suite

git commit -m "Add ansible-homelab-suite as submodule"
```

> Tip: If you prefer to pin to `main`, replace the branch name accordingly.

## 2) Private repo structure

Your inventory is organized under `inventories/<usage>/...`. For example,

```
ansible-homelab-inventory/
├─ ansible.cfg
├─ run.yml
├─ Makefile
├─ inventories/
│  └─ homelab/
│     ├─ hosts.yml
│     ├─ group_vars/
│     │  ├─ all.yml
│     │  ├─ id_servers.yml
│     │  ├─ admin_servers.yml
│     │  ├─ devops_servers.yml
│     │  ├─ ha_servers.yml
│     │  └─ media_servers.yml
│     ├─ host_vars/
│     │  ├─ idsrv01.yml
│     │  ├─ admin01.yml
│     │  ├─ devops01.yml
│     │  ├─ ha01.yml
│     │  └─ media01.yml
│     └─ vault/
│        └─ vault.yml
└─ vendor/
   └─ ansible-homelab-suite/   # git submodule
```

---

## 3) Private repo `ansible.cfg`

Create `ansible.cfg` in the **private** repo root (so you can run from there):

```ini
[defaults]
inventory = inventories/homelab/hosts.yml
roles_path = vendor/ansible-homelab-suite/roles
host_key_checking = True
retry_files_enabled = False
stdout_callback = yaml
interpreter_python = auto_silent

[inventory]
enable_plugins = yaml, ini
```

---

## 4) Private repo wrapper playbook: `run.yml`

```yaml
- import_playbook: vendor/ansible-homelab-suite/site.yml
```

---

## 5) Private repo Makefile (optional, but handy)

```makefile
.PHONY: deploy ping

ping:
\tansible -m ping all

deploy:
\tansible-playbook run.yml
```

Usage:

```bash
make ping
make deploy
```

---

# Required inventory variables

Your private inventory provides the environment-specific values this repo expects.

## Global environment vars (`inventories/homelab/group_vars/all.yml`)

At minimum:

- `domain_name` (e.g. `homelab.dev`)
- `edge_vip_ip` (EDGE VIP where Traefik binds 80/443)
- `traefik_bind_ip` (usually equal to `edge_vip_ip`)
- `traefik_dynamic_dir` / `traefik_dynamic_mount` (if different from defaults)
- secrets (Cloudflare token, Keycloak admin pass, etc.) via `vault.yml`

Example (illustrative):

```yaml
domain_name: homelab.dev

# idsrv01 (.30 convention across interfaces)
idsrv01_mgmt_ip: 192.168.10.30
idsrv01_server_ip: 192.168.4.30
edge_vip_ip: 192.168.6.30
traefik_bind_ip: "{{ edge_vip_ip }}"
```

## Host vars (`inventories/homelab/host_vars/<host>.yml`)

Each host running apps should provide its **SERVER VLAN bind IP**:

```yaml
server_bind_ip: 192.168.4.11
```

> The core roles bind published container ports to `server_bind_ip` to avoid exposing apps on unintended interfaces.

## Edge routing list (`inventories/homelab/group_vars/id_servers.yml`)

The Edge Gateway renders routes from `edge_apps`. Each entry defines:

- the public hostname (`host`)
- the upstream URL (`upstream_url`) on the SERVER VLAN
- whether SSO is enabled (`sso: true|false`)

Example:

```yaml
edge_apps:
  - id: homarr
    host: "homarr.{{ domain_name }}"
    upstream_url: "http://{{ hostvars['admin01'].server_bind_ip }}:7575"
    sso: true
```

---

# Network prerequisites and policy (pfSense + DNS)

This repo does not configure pfSense for you, but it assumes a compatible network policy.

## Recommended VLANs/subnets

- **MGMT**: `192.168.10.0/24` (SSH/admin plane)
- **SERVER**: `192.168.4.0/24` (backend app network)
- **EDGE**: `192.168.6.0/24` (Edge VIP network)
- **VPN**: `10.10.200.0/24` (WireGuard)

### Homelab convention for idsrv01

Use `.30` across interfaces:

- MGMT: `192.168.10.30`
- SERVER: `192.168.4.30`
- EDGE VIP: `192.168.6.30`

## DNS (pfSense DNS Resolver host overrides)

Use host overrides so clients always reach the Edge VIP for apps.

- `idsrv01.<domain>` → MGMT IP (`192.168.10.30`)
- each app (`homarr.<domain>`, `portainer.<domain>`, …) → EDGE VIP (`192.168.6.30`)

## Firewall expectations (high-level)

- Allow **LAN/WIFI/VPN → EDGE VIP** on **80/443**
- Block **LAN/WIFI/VPN → SERVER VLAN** (app ports)
- Allow **idsrv01 (SERVER IP) → SERVER VLAN** only on required upstream ports

This prevents bypassing the gateway and central SSO policy.

---

# Typical workflow

## Initial bring-up (suggested order)

1. Bring up networking (EDGE VLAN + routing) and DNS overrides
2. Deploy idsrv01 stack (`traefik`, `keycloak`, `sso_gateway`, `portainer`)
3. Deploy backend servers (apps bind only to SERVER VLAN IPs)
4. Add/verify `edge_apps` routes
5. Tighten pfSense rules (deny direct access to app ports)

## Updating the core suite (submodule)

From the private repo root:

```bash
cd vendor/ansible-homelab-suite
git checkout feature/edge_gateway_central_sso
git pull
cd ../..
git add vendor/ansible-homelab-suite
git commit -m "Bump core suite submodule"
```

## Running a deploy

```bash
ansible-playbook run.yml
# or
make deploy
```

---

# Notes on secrets

Store secrets in the private repo only (and encrypt them):

```bash
ansible-vault create inventories/homelab/vault/vault.yml
```

Examples of secrets:

- Cloudflare DNS token for Traefik (DNS-01 certs)
- Keycloak admin password
- any app-specific credentials

Never commit these secrets to the public core repo.

---

# Troubleshooting quick hits

- **Traefik binds to the wrong interface**  
  Ensure `traefik_bind_ip` is set to your EDGE VIP (e.g. `192.168.6.30`) in the private inventory.

- **Apps are reachable directly by IP:port from LAN/WIFI**  
  This is a firewall/DNS policy issue. Confirm:

  - backend app ports are bound to `server_bind_ip` (not `0.0.0.0`)
  - pfSense blocks LAN/WIFI/VPN → SERVER VLAN app ports

- **HTTP should redirect to HTTPS for apps**  
  Ensure Traefik listens on EDGE VIP port 80 and your edge routes include an HTTP router redirect.

---

## License

See repository license (if applicable).
