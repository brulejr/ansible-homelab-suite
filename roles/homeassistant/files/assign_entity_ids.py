"""Gives Home Assistant entities fixed entity ids over the WebSocket API.

Run inside the Home Assistant container, whose Python has aiohttp. Reads JSON on
stdin:

    {"token": "...", "url": "ws://127.0.0.1:8123/api/websocket",
     "entities": [
       {"platform": "mqtt", "unique_id": "649a63e7dd20_light",
        "entity_id": "light.front_light"}]}

Each entity is found by its integration and unique id. Home Assistant gives an
entity a suffixed id (light.front_light_2) when the plain one is taken, so an
id still held by another entity is left alone and reported as blocked; it is
assigned on a later run, once that entity is gone. Prints JSON naming the
entities it renamed, the ones it could not find and the blocked ones.
"""

import asyncio
import itertools
import json
import sys

import aiohttp


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

            entities = await call("config/entity_registry/list")
            by_id = {e["entity_id"]: e for e in entities}

            result = {"changed": [], "missing": [], "blocked": []}
            for wanted in request["entities"]:
                found = next((e for e in entities
                              if e["platform"] == wanted["platform"]
                              and e.get("unique_id") == wanted["unique_id"]), None)
                if found is None:
                    result["missing"].append(f"{wanted['platform']} {wanted['unique_id']}")
                    continue
                if found["entity_id"] == wanted["entity_id"]:
                    continue
                holder = by_id.get(wanted["entity_id"])
                if holder is not None:
                    result["blocked"].append(
                        f"{found['entity_id']}: {wanted['entity_id']} is held by {holder['platform']}")
                    continue
                await call("config/entity_registry/update", entity_id=found["entity_id"],
                           new_entity_id=wanted["entity_id"])
                result["changed"].append(f"{found['entity_id']} -> {wanted['entity_id']}")
            return result


print(json.dumps(asyncio.run(main(json.load(sys.stdin)))))
