@echo off
cd /d "%~dp0"
docker compose -f docker-compose.local.yml down
echo Stopped. Your local data is kept. (To wipe it: docker compose -f docker-compose.local.yml down -v)
pause
