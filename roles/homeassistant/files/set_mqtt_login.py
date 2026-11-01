"""Sets the broker login of Home Assistant's MQTT entry through its reconfigure flow.

Run on the Home Assistant host, with only the standard library. Reads JSON on
stdin:

    {"token": "...", "url": "http://127.0.0.1:8123",
     "entry_id": "01M448H8RK0FF97YNJ6SP1T11Q",
     "username": "homeassistant", "password": "..."}

The flow's form comes back filled with the entry's current settings, which
are sent back as they are with only the username and password replaced. Home
Assistant logs in to the broker with them before it saves anything, and
reloads the integration once it has. Prints JSON: changed, and the errors met.
"""

import json
import sys
import urllib.error
import urllib.request


def call(request, path, body=None, method=None):
    http = urllib.request.Request(
        request["url"] + path, data=None if body is None else json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {request['token']}", "Content-Type": "application/json"},
        method=method or ("GET" if body is None else "POST"))
    with urllib.request.urlopen(http, timeout=60) as reply:
        text = reply.read()
        return json.loads(text) if text.strip() else None


def values(schema):
    """The form's values as shown: suggested values, else defaults; sections
    become nested objects."""
    result = {}
    for field in schema:
        if field.get("type") == "expandable":
            result[field["name"]] = values(field["schema"])
            continue
        suggested = (field.get("description") or {}).get("suggested_value")
        if suggested is not None:
            result[field["name"]] = suggested
        elif "default" in field:
            result[field["name"]] = field["default"]
    return result


def main(request):
    flow = call(request, "/api/config/config_entries/flow",
                {"handler": "mqtt", "entry_id": request["entry_id"]})
    if flow.get("type") != "form":
        return {"changed": False, "errors": [f"reconfigure flow did not start: {flow}"]}
    answer = values(flow["data_schema"])
    answer["username"] = request["username"]
    answer["password"] = request["password"]
    try:
        reply = call(request, f"/api/config/config_entries/flow/{flow['flow_id']}", answer)
    except urllib.error.HTTPError as error:
        reply = {"type": "error", "message": f"{error.code} {error.read().decode()}"}
    if reply.get("type") == "abort" and reply.get("reason") == "reconfigure_successful":
        return {"changed": True, "errors": []}
    try:
        call(request, f"/api/config/config_entries/flow/{flow['flow_id']}", method="DELETE")
    except urllib.error.HTTPError:
        pass
    return {"changed": False,
            "errors": [f"broker rejected the settings: {reply.get('errors') or reply.get('reason') or reply.get('message')}"]}


print(json.dumps(main(json.load(sys.stdin))))
