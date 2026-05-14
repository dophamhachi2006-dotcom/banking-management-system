@echo off
echo === Banking Management System ===
echo Starting backend...
start cmd /k "cd backend && python app.py"
timeout /t 3 >nul
echo Starting frontend...
start cmd /k "cd frontend && npm run dev"
echo All services started.
