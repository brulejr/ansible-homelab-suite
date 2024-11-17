# Overview
This Ansible tool provides the ability to easily built a variety of different types of container-based homelab servers. Each server runs Docker to manage approriate services and proxies these services to name-based URLs using Traefik.

# Setup
This project can be primed using a bootstrap mechanism by running the following:
```bash
wget --no-cache https://raw.githubusercontent.com/brulejr/ansible-homelab-suite/refs/heads/main/bootstrap.py && python3 bootstrap.py
```

Running this script will prompt for the following information. These values are then used to build the Ansible default `inventory` file from the `inventory_template` file.

|Prompt|Description|
|:-----|:----------|
|Domain name|Server domain used for certificate generation|
|Cloudflare Email|Email address associate with the Cloudflare account managing the above domain|
|Cloudflare DNS Token|Token used in DNS Challenge by Let's Encrypt to generate server certificates|
|Traefik Username|User id for the Traefik dashboard|
|Traefik Password|Password for the Traefik dashboard|
|Admin Server|The administrative server|
|Devops Server|The devops server|
|Home Automation Server|The home automation server|
|Network Server|The network server|

# Usage
Once the project has been setup using the above bootstrap process, then the Ansible playbook may be run to build different types of servers.

To build all defined servers:
```bash
ansible-playbook site.yml
```

To build only a specific type of server (i.e. admin servers):
```bash
ansible-playbook --limit admin_servers site.yml
```

To build only a specific server (i.e. `admsrv01`):
```bash
ansible-playbook --limit admsrv01 site.yml
```

# Server Profiles
TBD

# Resources
Ansible Reference
- [Best Practices](https://docs.ansible.com/ansible/latest/tips_tricks/ansible_tips_tricks.html#best-practices)
- [Special Variables](https://docs.ansible.com/ansible/latest/reference_appendices/special_variables.html)
- [Using Variables](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_variables.html)
- [Working with Inventory](https://docs.ansible.com/ansible/latest/user_guide/intro_inventory.html)

Blog Articles (Inspiration!)
- [Automating my Homelab with Ansible (AnsibleFest 2022)](https://www.jeffgeerling.com/blog/2022/automating-my-homelab-ansible-ansiblefest-2022)
- [Ansible Roles: Basics, Creating & Using](https://spacelift.io/blog/ansible-roles)
- [Ansible — Configuration as Code for building up my Homelab](https://akashrajpurohit.com/blog/ansible-infrastructure-as-a-code-for-building-up-my-homelab/)

Related Projects (More Inspiration!)
- [Github - rishavnandi/ansible_homelab](https://github.com/rishavnandi/ansible_homelab)
- [Github - nleiva/ansible-home](https://github.com/rishavnandi/ansible_homelab)
