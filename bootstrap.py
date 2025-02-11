#!/usr/bin/env python3

import getpass
import os
import re
import subprocess

RE_DOMAIN_NAME = r"^[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9]\.[a-zA-Z]{2,}$"
RE_EMAIL = r"^[a-zA-Z0-9-_]+@[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9]\.[a-zA-Z]{2,}$"
RE_PASSWORD = r"^.+$"
RE_SERVER_NAME = r"^[a-zA-Z0-9][a-zA-Z0-9-]{1,61}$"
RE_TOKEN = r"^.+$"
RE_USERNAME = r"^.+$"

def input_val(prompt, pattern = r"^.+$", type = "string", password = False):
    while True:
        str_input = getpass(prompt + ": ") if password else input(prompt + ": ")
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
traefik_password = input_val("Enter the Traefik dashboard password", RE_PASSWORD, "password", True)
admin_server = input_val("Enter the admin server name", RE_SERVER_NAME, "admin server name")
network_server = input_val("Enter the network server name", RE_SERVER_NAME, "network server name")
ha_server = input_val("Enter the home automation server name", RE_SERVER_NAME, "home automation server name")
devops_server = input_val("Enter the devops server name", RE_SERVER_NAME, "devops server name")
media_server = input_val("Enter the medisa server name", RE_SERVER_NAME, "media server name")

# Calculate derived values
traefik_user_hash = subprocess.run([f"htpasswd", "-nBb", traefik_username, traefik_password], stdout=subprocess.PIPE, text=True).stdout

# Clone the repository
subprocess.run(
    ['git', 'clone', 'https://github.com/brulejr/ansible-homelab-suite.git'])
os.chdir('ansible-homelab-suite')

# Clone inventory template replacing values
with open('inventory_template', 'r') as f:
    content = f.read()
content = content.replace('<admin_server>', admin_server)
content = content.replace('<network_server>', network_server)
content = content.replace('<ha_server>', ha_server)
content = content.replace('<devops_server>', devops_server)
content = content.replace('<media_server>', media_server)
content = content.replace('<domain_name>', domain_name)
content = content.replace('<cloudflare_email>', cloudflare_email)
content = content.replace('<cloudflare_dns_token>', cloudflare_dns_token)
content = content.replace('<traefik_basic_auth_hash>', traefik_user_hash)
with open('inventory', 'w') as f:
    f.write(content)