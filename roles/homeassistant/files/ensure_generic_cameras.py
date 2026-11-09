"""Adds Generic Camera entries for stream URLs, named and placed by entity.

Run inside the Home Assistant container, whose Python has aiohttp. Reads JSON on
stdin:

    {"token": "...", "url": "http://127.0.0.1:8123",
     "cameras": [
       {"name": "Front Door Stream", "entity_id": "camera.front_door_stream",
        "stream_source": "rtsp://ring-mqtt:8554/649a639d769b_live",
        "still_image_url": "http://...",      # optional
        "authentication": "digest",            # optional; basic by default
        "username": "ring", "password": "...", "area": "foyer"}]}

The integration names each entry after the stream's host and does not notice
one that already exists, so a camera is matched by its entity id instead. A
missing one is created through the config flow, which opens the stream (and
fetches the still) to test it, then its entry is retitled and its entity
renamed over the WebSocket API. One already registered has its stream URL,
still URL, login and authentication brought in line through the options flow,
which tests them the same way, but only when the options form's current values
differ from these (a password the form does not show is not compared). Its
name and area are brought in line too. The entry's device, which the
integration also names after the host, is given the camera's name. Prints JSON
naming the cameras it created or changed and the errors it met.
"""

import asyncio
import itertools
import json
import sys

import aiohttp


def camera_form(camera):
    """The config/options flow form for a camera's stream, still and login."""
    form = {
        "username": camera.get("username", ""),
        "password": camera.get("password", ""),
        "advanced": {"framerate": 2, "verify_ssl": True, "rtsp_transport": "tcp",
                     "authentication": camera.get("authentication", "basic")},
    }
    for key in ("stream_source", "still_image_url"):
        if camera.get(key):
            form[key] = camera[key]
    return form


# Flow errors that a slow or flaky camera gives now and then (a still or
# stream that timed out), worth submitting the form again for
TRANSIENT_ERRORS = {"unable_still_load", "timeout"}
ATTEMPTS = 3


def suggested_values(schema):
    """A shown form's suggested (current) values, by field, sections nested."""
    values = {}
    for field in schema:
        if field.get("type") == "expandable":
            values[field["name"]] = suggested_values(field.get("schema", []))
        elif "suggested_value" in (field.get("description") or {}):
            values[field["name"]] = field["description"]["suggested_value"]
    return values


def drifted(current, wanted):
    """Whether the entry's current options differ from the wanted form."""
    for key in ("stream_source", "still_image_url", "username"):
        if (current.get(key) or "") != (wanted.get(key) or ""):
            return True
    if "password" in current and current["password"] != wanted["password"]:
        return True
    current_advanced = current.get("advanced", {})
    return any(current_advanced.get(key) != value
               for key, value in wanted["advanced"].items())


async def main(request):
    ids = itertools.count(1)
    headers = {"Authorization": f"Bearer {request['token']}"}
    flow_url = f"{request['url']}/api/config/config_entries/flow"
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.ws_connect(f"{request['url']}/api/websocket") as ws:

            async def call(command, **fields):
                message_id = next(ids)
                await ws.send_json({"id": message_id, "type": command, **fields})
                while True:
                    reply = await ws.receive_json()
                    if reply.get("id") == message_id:
                        if not reply.get("success"):
                            raise RuntimeError(f"{command}: {reply.get('error')}")
                        return reply["result"]

            async def name_device(entity, name):
                """Names the entity's device; True when it had to change."""
                if not entity.get("device_id"):
                    return False
                devices = await call("config/device_registry/list")
                device = next((d for d in devices if d["id"] == entity["device_id"]), None)
                if device is None or device.get("name_by_user") == name:
                    return False
                await call("config/device_registry/update",
                           device_id=device["id"], name_by_user=name)
                return True

            async def flow(url, method="POST", body=None):
                async with session.request(method, url, json=body) as reply:
                    return await reply.json(content_type=None)

            async def submit(step_url, form):
                """Submits a form, again while it fails only on transient errors."""
                for attempt in range(ATTEMPTS):
                    step = await flow(step_url, body=form)
                    errors = set((step.get("errors") or {}).values())
                    if not errors or not errors <= TRANSIENT_ERRORS:
                        return step
                    if attempt + 1 < ATTEMPTS:
                        await asyncio.sleep(2)
                return step

            async def reconfigure(entry_id, camera):
                """Brings an entry's options in line; True when they changed."""
                options_url = f"{request['url']}/api/config/config_entries/options/flow"
                shown = await flow(options_url, body={"handler": entry_id})
                if shown.get("step_id") != "init":
                    raise RuntimeError(f"options flow: {shown.get('reason') or shown}")
                step_url = f"{options_url}/{shown['flow_id']}"
                current = suggested_values(shown.get("data_schema", []))
                wanted = camera_form(camera)
                if not drifted(current, wanted):
                    await flow(step_url, method="DELETE")
                    return False
                # Keep the options this script does not manage
                wanted["advanced"] = {**current.get("advanced", {}), **wanted["advanced"]}
                step = await submit(step_url, wanted)
                if step.get("step_id") != "user_confirm":
                    await flow(step_url, method="DELETE")
                    raise RuntimeError(
                        f"options: {step.get('errors') or step.get('reason') or step}")
                done = await flow(step_url, body={"confirmed_ok": True})
                if done.get("type") != "create_entry":
                    raise RuntimeError(f"options: {done}")
                return True

            await ws.receive_json()  # auth_required
            await ws.send_json({"type": "auth", "access_token": request["token"]})
            if (await ws.receive_json()).get("type") != "auth_ok":
                raise RuntimeError("authentication failed")

            result = {"created": [], "changed": [], "errors": []}
            for camera in request["cameras"]:
                wanted = {"name": camera["name"]}
                if camera.get("area"):
                    wanted["area_id"] = camera["area"]
                entities = await call("config/entity_registry/list")
                entity = next((e for e in entities if e["entity_id"] == camera["entity_id"]), None)

                if entity is None:
                    started = await flow(flow_url, body={"handler": "generic"})
                    step_url = f"{flow_url}/{started['flow_id']}"
                    step = await submit(step_url, camera_form(camera))
                    if step.get("step_id") != "user_confirm":
                        await flow(step_url, method="DELETE")
                        result["errors"].append(
                            f"{camera['name']}: {step.get('errors') or step.get('reason') or step}")
                        continue
                    created = await flow(step_url, body={"confirmed_ok": True})
                    if created.get("type") != "create_entry":
                        result["errors"].append(f"{camera['name']}: {created}")
                        continue
                    entry_id = created["result"]["entry_id"]
                    await call("config_entries/update", entry_id=entry_id, title=camera["name"])

                    # The entity is registered once the new entry has set up
                    for _ in range(30):
                        entities = await call("config/entity_registry/list")
                        entity = next(
                            (e for e in entities if e.get("config_entry_id") == entry_id), None)
                        if entity:
                            break
                        await asyncio.sleep(1)
                    else:
                        result["errors"].append(f"{camera['name']}: entity never registered")
                        continue
                    await call("config/entity_registry/update", entity_id=entity["entity_id"],
                               new_entity_id=camera["entity_id"], **wanted)
                    await name_device(entity, camera["name"])
                    result["created"].append(f"{camera['name']} ({camera['entity_id']})")
                    continue

                if entity.get("platform") != "generic":
                    result["errors"].append(
                        f"{camera['name']}: {camera['entity_id']} belongs to {entity.get('platform')}")
                    continue
                renamed = False
                entry_id = entity.get("config_entry_id")
                if entry_id:
                    try:
                        renamed = await reconfigure(entry_id, camera)
                    except RuntimeError as err:
                        result["errors"].append(f"{camera['name']}: {err}")
                        continue
                renamed = await name_device(entity, camera["name"]) or renamed
                if any(entity.get(key) != value for key, value in wanted.items()):
                    await call("config/entity_registry/update",
                               entity_id=camera["entity_id"], **wanted)
                    renamed = True
                if renamed:
                    result["changed"].append(f"{camera['name']} ({camera['entity_id']})")
            return result


print(json.dumps(asyncio.run(main(json.load(sys.stdin)))))
