#!/usr/bin/env python3

import os
import re
import subprocess

RE_DOMAIN_NAME = r"^[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9]\.[a-zA-Z]{2,}$"
RE_EMAIL = r"^[a-zA-Z0-9-_]+@[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9]\.[a-zA-Z]{2,}$"
RE_PASSWORD = r"^.+$"
RE_SERVER_NAMES = r"^([a-zA-Z0-9][a-zA-Z0-9-]{1,61})*(,[a-zA-Z0-9][a-zA-Z0-9-]{1,61})*$"
RE_TOKEN = r"^.+$"
RE_USERNAME = r"^.+$"

def input_val(prompt, pattern = r"^.+$", type = "string"):
    while True:
        str_input = input(prompt + ": ")
        if re.match(pattern, str_input):
            break
        else:
            print(f"Please input a valid {type}.")
    return str_input

# Read user input
domain_name = input_val("Enter the domain name", RE_DOMAIN_NAME, "domain name")
cloudflare_email = input_val("Enter the Cloudflare email address", RE_EMAIL, "email address")
cloudflare_dns_token = input_val("Enter the Cloudflare DNS Token", RE_TOKEN, "token")
traefik_username = input_val("Enter the Traefik dashboard user", RE_USERNAME, "username")
traefik_password = input_val("Enter the Traefik dashboard password", RE_PASSWORD, "password")
admin_servers = input_val("Enter the admin server name(s)", RE_SERVER_NAMES, "admin server name(s)")
network_servers = input_val("Enter the network server name(s)", RE_SERVER_NAMES, "network server name(s)")
ha_servers = input_val("Enter the home automation server name(s)", RE_SERVER_NAMES, "home automation server name(s)")
devops_servers = input_val("Enter the devops server name(s)", RE_SERVER_NAMES, "devops server name(s)")

# Calculate derived values
traefik_user_hash = subprocess.run([f"htpasswd", "-nBb", traefik_username, traefik_password], stdout=subprocess.PIPE, text=True).stdout
admin_servers = "\n".join(admin_servers.split(","))
network_servers = "\n".join(network_servers.split(","))
ha_servers = "\n".join(ha_servers.split(","))
devops_servers = "\n".join(devops_servers.split(","))

# Clone the repository
subprocess.run(
    ['git', 'clone', 'https://github.com/brulejr/ansible-homelab-suite.git'])
os.chdir('ansible-homelab-suite')

# Clone inventory template replacing values
with open('inventory_template', 'r') as f:
    content = f.read()
content = content.replace('<admin_servers>', admin_servers)
content = content.replace('<network_servers>', network_servers)
content = content.replace('<ha_servers>', ha_servers)
content = content.replace('<devops_servers>', devops_servers)
content = content.replace('<domain_name>', domain_name)
content = content.replace('<cloudflare_email>', cloudflare_email)
content = content.replace('<cloudflare_dns_token>', cloudflare_dns_token)
content = content.replace('<traefik_basic_auth_hash>', traefik_user_hash)
with open('inventory', 'w') as f:
    f.write(content)