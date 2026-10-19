"""Puts Home Assistant devices in areas over the WebSocket API.

Run inside the Home Assistant container, whose Python has aiohttp. Reads JSON on
stdin:

    {"token": "...", "url": "ws://127.0.0.1:8123/api/websocket",
     "devices": [
       {"label": "HL-L3220CDW", "area": "master_bedroom",
        "configuration_url": "http://10.10.120.70/"},
       {"label": "Roku Ultra", "area": "living_room",
        "identifier": ["roku", "X01000CUPS96"]}]}

Each device is found by its configuration URL or by one of its integration
identifiers. Prints JSON naming the devices it moved, the ones it could not
find, and any area that does not exist. A device already in its area is left
alone.
"""

import asyncio
import itertools
import json
import sys

import aiohttp


def matches(device, wanted):
    if "configuration_url" in wanted:
        return device.get("configuration_url") == wanted["configuration_url"]
    return list(wanted["identifier"]) in [list(i) for i in device.get("identifiers", [])]


async def main(request):
    ids = itertools.count(1)
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(request["url"]) as ws:

            async def call(command, **fields):
                message_id = next(ids)
                await ws.send_json({"id": message_id, "type": command, **fields})
                while True:
                    reply = await ws.receive_json()
                    if reply.get("id") == message_id:
                        if not reply.get("success"):
                            raise RuntimeError(f"{command}: {reply.get('error')}")
                        return reply["result"]

            await ws.receive_json()  # auth_required
            await ws.send_json({"type": "auth", "access_token": request["token"]})
            if (await ws.receive_json()).get("type") != "auth_ok":
                raise RuntimeError("authentication failed")

            areas = {area["area_id"] for area in await call("config/area_registry/list")}
            devices = await call("config/device_registry/list")

            result = {"changed": [], "missing": [], "unknown_areas": []}
            for wanted in request["devices"]:
                if wanted["area"] not in areas:
                    result["unknown_areas"].append(wanted["area"])
                    continue
                found = [d for d in devices if matches(d, wanted)]
                if not found:
                    result["missing"].append(wanted["label"])
                for device in found:
                    if device.get("area_id") != wanted["area"]:
                        await call("config/device_registry/update",
                                   device_id=device["id"], area_id=wanted["area"])
                        name = device.get("name_by_user") or device.get("name")
                        result["changed"].append(
                            f"{name}: {device.get('area_id') or 'no area'} -> {wanted['area']}")
            return result


print(json.dumps(asyncio.run(main(json.load(sys.stdin)))))
