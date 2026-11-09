homeassistant
=============

Runs [Home Assistant](https://www.home-assistant.io/) as a Docker Compose
stack (`lscr.io/linuxserver/homeassistant`), and sets up what can be kept in
the inventory: custom integrations, frontend cards, dashboards, automations,
notify groups, and integrations, device areas and entity ids that only the
API can set.

Every setting is described in `defaults/main.yml`.

What it manages
---------------

**Files in `/config`**, needing nothing but the role:

| Variable | What it does |
| :-- | :-- |
| `homeassistant_custom_components` | Custom integrations (what HACS would install), each pinned to a GitHub tag. The tag's `custom_components/<domain>/` is copied into `/config/custom_components/`, and Home Assistant restarts when the version changes. |
| `homeassistant_frontend_modules` | Custom cards, downloaded from GitHub releases and registered as Lovelace resources, with optional literal patches. Setting any switches resources to YAML mode, so ones added in the UI or by HACS are ignored. |
| `homeassistant_dashboards` | YAML-mode dashboards. UI edits to them are overwritten on deploy. |
| `homeassistant_notify_groups` | Notify services that send to several services at once, passing iOS options such as critical alerts through. |
| `homeassistant_automation_files` | Automations, one per file, loaded beside the UI's `automations.yaml` and reloaded without a restart. |

**Through the API**, with a long-lived access token in
`homeassistant_api_token`. While it is empty, these are skipped:

| Variable | What it does |
| :-- | :-- |
| `homeassistant_ping_hosts` | Ping integration entries. |
| `homeassistant_brother_printers`, `homeassistant_roku_devices`, `homeassistant_onvif_cameras` | Integration entries, each with its device placed in an area. |
| `homeassistant_generic_cameras` | Generic Camera entries for RTSP streams and still image URLs, with fixed entity ids; their URLs and logins are reapplied when they drift. |
| `homeassistant_mqtt_username` | The MQTT integration's broker login, set on the entry made in the UI. |
| `homeassistant_mqtt_devices` | Areas for MQTT devices, by the identifier their bridge publishes. |
| `homeassistant_devices` | Areas for devices of any integration set up in the UI, custom ones among them, by the `[domain, id]` identifier the integration registers. |
| `homeassistant_entity_ids` | Fixed entity ids, matched by platform and unique id. |

Entries are created when missing and never removed. Areas and entity ids are
reapplied on every deploy, so the inventory is their source of truth.

Custom integrations
-------------------

    homeassistant_custom_components:
      - domain: tryfi                 # directory under custom_components/
        repo: sbabcock23/hass-tryfi
        version: "0.0.26"             # git tag

- **Only the code is installed.** Add the integration itself (its login) once
  in the UI: Settings → Devices & services → Add integration. Refresh the
  browser after the restart, or it may not be listed yet.
- **The installed version is recorded** in `.ansible_version` inside the
  component, so a deploy downloads only when the pinned version changes. The
  component is replaced wholesale, so files dropped upstream don't linger.
- **Permissions are reset on every deploy.** A directory without its
  execute bit stops Home Assistant reading the manifest, and it then skips
  the integration without logging anything.
- **Dropping a component from the list leaves it in place**; delete it from
  `/config/custom_components/` by hand.

An integration's entities are named after the area chosen while adding it
(for example `sensor.living_room_…`). Pin the ones dashboards refer to with
`homeassistant_entity_ids`, and place its devices with `homeassistant_devices`.

Requirements
------------

- The `community.docker` and `community.general` collections.
- `homeassistant_api_token` for the API-driven settings: in Home Assistant,
  Profile → Security → Long-lived access tokens.
