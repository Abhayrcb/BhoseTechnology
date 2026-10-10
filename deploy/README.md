# Deploy: local + production

| | Local (PC, Docker Desktop) | Production (AWS EC2) |
|---|---|---|
| Compose file | `docker-compose.local.yml` | `docker-compose.yml` (adds Caddy HTTPS) |
| Config | built in (no .env) | `deploy/.env` (copy from `.env.example`) |
| Start / update | double-click `run-local.bat` | `./deploy.sh` |
| Stop | `stop-local.bat` | `docker compose down` |
| URL | http://localhost:3000 | https://your-domain |

## Local
Docker Desktop chalu karo → `deploy\run-local.bat` double-click.
Admin: `admin@example.com` / `admin12345` (sirf local ke liye).

## Production (server par)
```bash
cd BhoseTechnology/deploy
cp .env.example .env && nano .env     # ek baar
./deploy.sh                           # pehli baar bhi, aur har update par bhi
```
Server ki pehli setup (EC2, DNS, Docker install): `../DEPLOY_AWS.md`.

## Rules
- `deploy/.env` kabhi git mein commit mat karo (`.gitignore` mein already hai).
- Production mein local wala admin password kabhi use mat karo.
- Backup: `./backup.sh` (cron se nightly).
