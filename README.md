# chatgpt-module

## OpenAI keys in Docker Compose

Put the shared default key in `../../secrets/chatgpt_default_openai_api_key`,
outside the plugin build context, and restrict its host permissions. Alternatively,
set `CHATGPT_DEFAULT_OPENAI_API_KEY_FILE` to the host file path. Keep `PORT` and
`OPENAI_MODEL` in `.env`, but remove `OPENAI_API_KEY` from `.env` after migrating
the key. Start with `docker compose up -d --build`.

To add account-specific keys, create an additional Compose file such as:

```yaml
services:
  chatgpt:
    environment:
      OPENAI_API_KEY_FILES: '{"alice": "/run/secrets/chatgpt_alice", "bob": "/run/secrets/chatgpt_bob"}'
    secrets:
      - chatgpt_alice
      - chatgpt_bob

secrets:
  chatgpt_alice:
    file: ../../secrets/chatgpt_alice
  chatgpt_bob:
    file: ../../secrets/chatgpt_bob
```

Place the key files outside the build context, restrict their host permissions,
and keep the override file alongside `docker-compose.yml`. Start or recreate
with `docker compose -f docker-compose.yml -f <override-file> up -d --build`.
Add a secret and a mapping entry for each account; never put key values in the
mapping. Changes to keys or mappings require recreating the service.

The caller supplies `key_user_account` as a form field. An omitted or empty
account uses the default key; an unknown account is rejected. This field is
not authenticated: any caller who can reach the module can choose any configured
account. Only expose the module to trusted callers; this is key routing, not
per-user authorization.

Compose file-backed secrets are not encrypted; Docker administrators can access
them, and Docker Desktop may not enforce container-side ownership or permissions.
For standalone use, set `OPENAI_API_KEY_FILE` or `OPENAI_API_KEY` for the
default key, and optionally `OPENAI_API_KEY_FILES` to a JSON object mapping
account IDs to readable key file paths.

To build into an executable:
```sh
python -m pip install pyinstaller
python -m PyInstaller --onefile --name chatgpt-module main.py
```