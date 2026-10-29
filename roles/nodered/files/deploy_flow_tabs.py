"""Deploys whole Node-RED tabs through the admin API, leaving other tabs alone.

Run on the Node-RED host, with only the standard library. Reads JSON on stdin:

    {"url": "http://10.10.40.75:1880", "username": "admin", "password": "...",
     "tabs": [["door_watch.json",
               [{"id": "door_watch_tab", "type": "tab", ...},
                {"id": "door_watch_learn", "z": "door_watch_tab", ...}]]]}

Each tab is a file name and one exported tab: its tab node and the nodes on
it, whose ids must be fixed so the tab is found again on the next run. Config
nodes (such as MQTT brokers) are shared with UI-built tabs, so any in an
export are only checked to be live already, never deployed from here. Each
tab is deployed locked, its label marked with MARK and its description headed
with where it comes from, so it reads as Ansible's in the editor; a tab
exported again with those marks loses them before the comparison. A tab whose
live nodes already match is left alone, so nothing restarts. With a username
and password (Node-RED's adminAuth), it logs in for a token, revoked when done. Otherwise its live nodes are replaced by the export,
including anything added to it in the editor, and all changes go out in one
deploy that restarts only the changed tabs. Prints JSON naming the tabs it
added or changed and the errors it met; on an error nothing is deployed.
"""

import json
import sys
import urllib.error
import urllib.request

API = {"Node-RED-API-Version": "v2", "Content-Type": "application/json"}
MARK = "\u2699 "  # the gear sign
HEADER = "Managed by Ansible from {}; changes made here are overwritten on deploy.\n\n"


def marked(tab, source):
    """The tab as deployed: locked, with MARK and HEADER applied once."""
    label = tab.get("label", "").removeprefix(MARK)
    info = tab.get("info", "")
    if info.startswith("Managed by Ansible from "):
        info = info.partition("\n\n")[2]
    return {**tab, "label": MARK + label, "info": HEADER.format(source) + info, "locked": True}


def call(url, body=None, headers=None):
    request = urllib.request.Request(
        url, data=None if body is None else json.dumps(body).encode(),
        headers={**API, **(headers or {})}, method="GET" if body is None else "POST")
    with urllib.request.urlopen(request, timeout=30) as reply:
        text = reply.read()
        return json.loads(text) if text.strip() else None


def matches(live, wanted):
    """True when the live nodes hold every field of the wanted ones; Node-RED
    may add fields of its own, which are not a change."""
    if set(live) != set(wanted):
        return False
    return all(live[i].get(key) == value for i, node in wanted.items() for key, value in node.items())


def main(request):
    if not request.get("password"):
        return deploy(request, {})
    try:
        token = call(f"{request['url']}/auth/token", {
            "client_id": "node-red-admin", "grant_type": "password", "scope": "*",
            "username": request["username"], "password": request["password"]})["access_token"]
    except urllib.error.HTTPError as error:
        return {"added": [], "changed": [], "errors": [f"login as {request['username']} failed: {error.code}"]}
    auth = {"Authorization": f"Bearer {token}"}
    try:
        return deploy(request, auth)
    finally:
        call(f"{request['url']}/auth/revoke", {"token": token}, auth)


def deploy(request, auth):
    current = call(f"{request['url']}/flows", headers=auth)
    flows = current["flows"]
    result = {"added": [], "changed": [], "errors": []}

    for source, export in request["tabs"]:
        tabs = [n for n in export if n.get("type") == "tab"]
        if len(tabs) != 1:
            result["errors"].append(f"{source} holds {len(tabs)} tabs, not one")
            continue
        tab = marked(tabs[0], source)
        export = [tab if n is tabs[0] else n for n in export]
        # The editor's export brings the shared config nodes the tab uses;
        # they are not deployed from here, but must already be live
        live_ids = {n["id"] for n in flows}
        shared = [n for n in export if n is not tab and "z" not in n]
        missing = [n.get("name") or n["id"] for n in shared if n["id"] not in live_ids]
        if missing:
            result["errors"].append(f"{tab['label']}: config nodes not deployed: {', '.join(missing)}")
            continue
        export = [n for n in export if n not in shared]
        strays = [n["id"] for n in export if n is not tab and n.get("z") != tab["id"]]
        if strays:
            result["errors"].append(f"{tab['label']}: nodes not on the tab: {', '.join(strays)}")
            continue
        wanted = {n["id"]: n for n in export}
        ours = lambda n: n["id"] == tab["id"] or n.get("z") == tab["id"]
        taken = [n["id"] for n in flows if n["id"] in wanted and not ours(n)]
        if taken:
            result["errors"].append(f"{tab['label']}: ids used elsewhere: {', '.join(taken)}")
            continue

        live = {n["id"]: n for n in flows if ours(n)}
        if matches(live, wanted):
            continue
        # Keep the tab where it was in the editor; a new one goes last
        at = next((i for i, n in enumerate(flows) if n["id"] == tab["id"]), None)
        rest = [n for n in flows if not ours(n)]
        if at is None:
            flows = rest + export
            result["added"].append(tab["label"])
        else:
            before = sum(1 for n in flows[:at] if not ours(n))
            flows = rest[:before] + export + rest[before:]
            result["changed"].append(tab["label"])

    if result["errors"] or not (result["added"] or result["changed"]):
        return result
    try:
        call(f"{request['url']}/flows", {"rev": current["rev"], "flows": flows},
             {**auth, "Node-RED-Deployment-Type": "flows"})
    except urllib.error.HTTPError as error:
        # 409: the flows were deployed from the editor since they were read
        result["errors"].append(f"deploy failed: {error.code} {error.read().decode()}")
    return result


print(json.dumps(main(json.load(sys.stdin))))
