@echo off
REM Double-click to run the whole site on your PC (needs Docker Desktop running)
cd /d "%~dp0"
docker info >nul 2>&1
if errorlevel 1 (
  echo Docker Desktop is not running. Start it, wait until it says Running, then try again.
  pause
  exit /b 1
)
echo Building and starting... first time takes 5-10 minutes.
docker compose -f docker-compose.local.yml up --build -d
if errorlevel 1 (
  echo Something failed. Run:  docker compose -f docker-compose.local.yml logs
  pause
  exit /b 1
)
echo.
echo  Site  : http://localhost:3000
echo  Admin : http://localhost:3000/admin   (admin@example.com / admin12345)
echo  API   : http://localhost:8001/api/
echo.
start http://localhost:3000
pause
