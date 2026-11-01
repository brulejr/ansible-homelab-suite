"""Sets the login of Node-RED's MQTT broker config nodes through the admin API.

Run on the Node-RED host, with only the standard library. Reads JSON on stdin:

    {"url": "http://127.0.0.1:1880", "username": "admin", "password": "...",
     "state_file": "/opt/.../broker_logins.json",
     "brokers": [{"id": "mqtt_broker_brulenet", "user": "nodered",
                  "password": "..."}]}

Node-RED never hands out a stored password, so a digest of each login set
here is kept in state_file, and a broker is changed only when its user, its
digest or the presence of a password differs. Changes go out in one full
deploy, which reconnects every node, as Node-RED may not restart a config node
whose credentials alone changed. With a username and password (Node-RED's
adminAuth), it logs in for a token, revoked when done. Prints JSON naming the
brokers it changed and the errors it met; on an error nothing is deployed.
"""

import hashlib
import json
import os
import sys
import urllib.error
import urllib.request

API = {"Node-RED-API-Version": "v2", "Content-Type": "application/json"}


def call(url, body=None, headers=None):
    request = urllib.request.Request(
        url, data=None if body is None else json.dumps(body).encode(),
        headers={**API, **(headers or {})}, method="GET" if body is None else "POST")
    with urllib.request.urlopen(request, timeout=30) as reply:
        text = reply.read()
        return json.loads(text) if text.strip() else None


def digest(broker):
    return hashlib.sha256(f"{broker['user']}\0{broker['password']}".encode()).hexdigest()


def main(request):
    if not request.get("password"):
        return apply(request, {})
    try:
        token = call(f"{request['url']}/auth/token", {
            "client_id": "node-red-admin", "grant_type": "password", "scope": "*",
            "username": request["username"], "password": request["password"]})["access_token"]
    except urllib.error.HTTPError as error:
        return {"changed": [], "errors": [f"login as {request['username']} failed: {error.code}"]}
    auth = {"Authorization": f"Bearer {token}"}
    try:
        return apply(request, auth)
    finally:
        call(f"{request['url']}/auth/revoke", {"token": token}, auth)


def apply(request, auth):
    result = {"changed": [], "errors": []}
    try:
        with open(request["state_file"]) as file:
            state = json.load(file)
    except FileNotFoundError:
        state = {}

    current = call(f"{request['url']}/flows", headers=auth)
    flows = current["flows"]
    nodes = {n["id"]: n for n in flows}
    for broker in request["brokers"]:
        node = nodes.get(broker["id"])
        if node is None or node.get("type") != "mqtt-broker":
            result["errors"].append(f"no mqtt-broker node with id {broker['id']}")
            continue
        live = call(f"{request['url']}/credentials/mqtt-broker/{broker['id']}", headers=auth) or {}
        if (live.get("user") == broker["user"] and live.get("has_password")
                and state.get(broker["id"]) == digest(broker)):
            continue
        node["credentials"] = {"user": broker["user"], "password": broker["password"]}
        result["changed"].append(node.get("name") or broker["id"])

    if result["errors"] or not result["changed"]:
        return result
    try:
        call(f"{request['url']}/flows", {"rev": current["rev"], "flows": flows},
             {**auth, "Node-RED-Deployment-Type": "full"})
    except urllib.error.HTTPError as error:
        # 409: the flows were deployed from the editor since they were read
        result["errors"].append(f"deploy failed: {error.code} {error.read().decode()}")
        return result

    state.update({b["id"]: digest(b) for b in request["brokers"]})
    with open(request["state_file"], "w") as file:
        json.dump(state, file)
    os.chmod(request["state_file"], 0o600)
    return result


print(json.dumps(main(json.load(sys.stdin))))
