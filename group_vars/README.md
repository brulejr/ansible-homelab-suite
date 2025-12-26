# Secrets Management

1. Secrets are managed within the following file:

- `vault_sso.yml`

Example (plaintext initially):

```yaml
# group_vars/all/vault_sso.yml
vault_keycloak_bootstrap_admin_password: "super-long-random"
vault_keycloak_db_password: "another-long-random"

vault_sso_oidc_client_secret: "client-secret-from-keycloak"
vault_sso_cookie_secret: "base64-32-bytes-cookie-secret"
```

2. Encrypt it with ansible-vault

From the repo root, run

```bash
ansible-vault encrypt group_vars/all/vault_sso.yml
```

This will prompt for a vault password. (Or, use a vault password file—see below.)

3. Use the variables normally

Sample usage:

```yaml
keycloak_bootstrap_admin_password: "{{ vault_keycloak_bootstrap_admin_password }}"
```

That variable will resolve at runtime as long as you provide the vault password.

4. Running playbooks

Prompt for the vault password:

```yaml
ansible-playbook site.yml --ask-vault-pass
```

Or use a vault password file (often more convenient for homelab automation):

```yaml
ansible-playbook site.yml --vault-password-file .vault_pass
```

Where `.vault_pass` contains the vault password and is added to `.gitignore`.
