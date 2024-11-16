# Overview
TBD

# Usage
This project can be primed using a bootstrap mechanism by running the following:
```bash
wget --no-cache https://raw.githubusercontent.com/brulejr/ansible-homelab-suite/refs/heads/main/bootstrap.py && python3 bootstrap.py
```

Running this script will prompt for the following information, with which it will build the `inventory` file.

|Prompt|Description|
|:-----|:----------|
|Domain name|Server domain used for certificate generation|
|Cloudflare Email|The email address associate with the Cloudflare account managing the above domain|


# Resources
Ansible Reference
- [Best Practices](https://docs.ansible.com/ansible/latest/tips_tricks/ansible_tips_tricks.html#best-practices)
- [Special Variables](https://docs.ansible.com/ansible/latest/reference_appendices/special_variables.html)
- [Using Variables](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_variables.html)
- [Working with Inventory](https://docs.ansible.com/ansible/latest/user_guide/intro_inventory.html)

Blog Articles
- [Ansible Roles: Basics, Creating & Using](https://spacelift.io/blog/ansible-roles)