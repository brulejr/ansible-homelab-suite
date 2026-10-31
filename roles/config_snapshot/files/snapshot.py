"""Commits snapshots of app data to git repositories, encrypting secret files.

Run on the host as root, with only the standard library plus git and age.
Takes the path of a JSON configuration (rendered by Ansible):

    {"remote_base": "ssh://git@10.0.0.10:2222/homelab",
     "ssh_key": "/opt/.../id_ed25519", "known_hosts": "/opt/.../known_hosts",
     "work_dir": "/opt/.../repos", "state_dir": "/opt/.../state",
     "recipients": ["age1..."], "author_name": "...", "author_email": "...",
     "repos": [{"name": "config",
                "sources": [{"src": "/opt/.../homeassistant/config",
                             "dest": "homeassistant",
                             "exclude": ["*.log", "backups"],
                             "secrets": ["secrets.yaml", ".storage/auth"]}]}]}

Each source is mirrored into <dest> of its repository's working copy: files
are copied, and files that no longer exist (or are now excluded) are removed.
Files matching "secrets" are written as <name>.age, encrypted to every
recipient, instead. Encryption is not deterministic, so a secret file is only
encrypted again when its content or the recipients change, as recorded in the
state directory (outside the repository). Patterns match the path relative to
src, or with no "/" in them, a name at any depth; a matched directory takes
everything under it.

Whatever changed is committed and pushed. Commits that an earlier run couldn't
push are pushed by the next one. Exits non-zero if any repository failed.
"""

import datetime
import fnmatch
import hashlib
import json
import os
import shutil
import socket
import subprocess
import sys

README = """# {repo}

Snapshots of app data on {host}, committed every night by Ansible's
`config_snapshot` role when something changed. This repository is written
by that job only: don't push to it, or the next snapshot can't push.

| Directory | Copied from |
| --- | --- |
{table}

Files ending in `.age` are secrets, encrypted with [age](https://age-encryption.org/)
to these recipients:

{recipients}

The host can encrypt but not decrypt them. To restore one, decrypt it with
the matching identity (private key):

    age -d -i identity.txt path/to/file.age > path/to/file

Restoring is a manual step: stop the app, copy the files back, and start it.
"""


def matches(rel, patterns):
    """True when rel, or one of its parent directories, matches a pattern."""
    parts = rel.split("/")
    for i in range(1, len(parts) + 1):
        sub = "/".join(parts[:i])
        for pattern in patterns:
            if fnmatch.fnmatchcase(sub, pattern):
                return True
            if "/" not in pattern and fnmatch.fnmatchcase(parts[i - 1], pattern):
                return True
    return False


def wanted_files(source):
    """Maps each path the source puts in the repository to (kind, file)."""
    src, dest = source["src"], source["dest"].strip("/")
    exclude, secrets = source.get("exclude", []), source.get("secrets", [])
    wanted = {}
    if not os.path.isdir(src):
        raise RuntimeError(f"{src} is not a directory")
    for root, dirs, files in os.walk(src):
        rel_root = os.path.relpath(root, src).replace(os.sep, "/")
        rel_root = "" if rel_root == "." else rel_root + "/"
        dirs[:] = sorted(d for d in dirs
                         if not os.path.islink(os.path.join(root, d))
                         and not matches(rel_root + d, exclude))
        for name in sorted(files):
            path = os.path.join(root, name)
            rel = rel_root + name
            if not os.path.isfile(path) or os.path.islink(path) or matches(rel, exclude):
                continue
            if matches(rel, secrets):
                wanted[f"{dest}/{rel}.age"] = ("secret", path)
            else:
                wanted[f"{dest}/{rel}"] = ("plain", path)
    return wanted


def digest(path, recipients):
    hasher = hashlib.sha256("\n".join(sorted(recipients)).encode() + b"\0")
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 16), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def same_content(a, b):
    if not os.path.exists(b) or os.path.getsize(a) != os.path.getsize(b):
        return False
    with open(a, "rb") as left, open(b, "rb") as right:
        return left.read() == right.read()


def sync(repo_dir, sources, recipients, state):
    """Brings the working copy in line with the sources; updates state."""
    wanted = {}
    for source in sources:
        wanted.update(wanted_files(source))
    new_state = {}
    for rel, (kind, path) in wanted.items():
        target = os.path.join(repo_dir, rel)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        if kind == "plain":
            if not same_content(path, target):
                shutil.copyfile(path, target)
            executable = os.stat(path).st_mode & 0o111
            os.chmod(target, 0o755 if executable else 0o644)
        else:
            stamp = digest(path, recipients)
            if state.get(rel) != stamp or not os.path.exists(target):
                argv = ["age", "--armor", "--output", target]
                for recipient in recipients:
                    argv += ["--recipient", recipient]
                subprocess.run(argv + [path], check=True)
                os.chmod(target, 0o644)
            new_state[rel] = stamp
    # Remove what the sources no longer produce, within their directories only
    for source in sources:
        dest_dir = os.path.join(repo_dir, source["dest"].strip("/"))
        for root, dirs, files in os.walk(dest_dir, topdown=False):
            for name in files:
                rel = os.path.relpath(os.path.join(root, name), repo_dir).replace(os.sep, "/")
                if rel not in wanted:
                    os.remove(os.path.join(root, name))
            if root != dest_dir and not os.listdir(root):
                os.rmdir(root)
    return new_state


def git(repo_dir, *args, env=None, check=True):
    return subprocess.run(["git", "-C", repo_dir, *args], env=env, check=check,
                          capture_output=True, text=True)


def snapshot(config, repo, env):
    name = repo["name"]
    repo_dir = os.path.join(config["work_dir"], name)
    remote = f"{config['remote_base']}/{name}.git"
    if not os.path.isdir(os.path.join(repo_dir, ".git")):
        os.makedirs(repo_dir, exist_ok=True)
        git(repo_dir, "init", "--initial-branch=main")
        git(repo_dir, "remote", "add", "origin", remote)
    git(repo_dir, "remote", "set-url", "origin", remote)
    git(repo_dir, "config", "user.name", config["author_name"])
    git(repo_dir, "config", "user.email", config["author_email"])

    state_file = os.path.join(config["state_dir"], f"{name}.json")
    state = {}
    if os.path.exists(state_file):
        with open(state_file) as handle:
            state = json.load(handle)
    state = sync(repo_dir, repo["sources"], config["recipients"], state)

    host = socket.gethostname()
    table = "\n".join(f"| `{s['dest'].strip('/')}/` | `{host}:{s['src']}` |" for s in repo["sources"])
    recipients = "\n".join(f"- `{r}`" for r in config["recipients"]) or "- (none)"
    with open(os.path.join(repo_dir, "README.md"), "w") as handle:
        handle.write(README.format(repo=name, host=host, table=table, recipients=recipients))

    git(repo_dir, "add", "--all")
    changed = git(repo_dir, "diff", "--cached", "--name-only").stdout.split()
    if changed:
        stamp = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
        git(repo_dir, "commit", "--quiet", "-m", f"Snapshot of {host} at {stamp}",
            "-m", f"{len(changed)} file(s) changed.")
    # Saved only once committed, so a failed run encrypts again next time
    with open(state_file, "w") as handle:
        json.dump(state, handle, indent=1, sort_keys=True)
    pushed = git(repo_dir, "push", "--quiet", "origin", "main", env=env, check=False)
    if pushed.returncode != 0:
        raise RuntimeError(f"push failed: {pushed.stderr.strip()}")
    return len(changed)


def main(path):
    with open(path) as handle:
        config = json.load(handle)
    os.makedirs(config["state_dir"], mode=0o700, exist_ok=True)
    env = dict(os.environ, GIT_SSH_COMMAND=(
        f"ssh -i {config['ssh_key']} -o IdentitiesOnly=yes -o BatchMode=yes"
        f" -o UserKnownHostsFile={config['known_hosts']} -o StrictHostKeyChecking=yes"))
    failed = False
    for repo in config["repos"]:
        try:
            count = snapshot(config, repo, env)
            print(f"{repo['name']}: " + (f"committed {count} changed file(s)" if count else "no changes"))
        except (RuntimeError, OSError, subprocess.CalledProcessError) as error:
            detail = getattr(error, "stderr", None) or error
            print(f"{repo['name']}: failed: {str(detail).strip()}", file=sys.stderr)
            failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
