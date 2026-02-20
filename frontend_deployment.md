# Frontend Deployment Guide

## Quick Start

### Start the Development Server
```powershell
cmd /c "cd frontend && npm run dev"
```

The server will start on:
- **Local**: http://localhost:3000
- **Network**: http://192.168.1.108:3000 (your IP may vary)

### Stop the Server
Press `Ctrl+C` in the terminal where the server is running, or:
```powershell
taskkill /F /IM node.exe
```

### Restart the Server
```powershell
taskkill /F /IM node.exe; Start-Sleep -Seconds 2; cmd /c "cd frontend && npm run dev"
```

---

## Why `cmd /c` Instead of `npm` Directly?

PowerShell has execution policy restrictions that block running `npm.ps1` and `npx.ps1` scripts. Using `cmd /c` bypasses these restrictions.

---

## Troubleshooting

### Port Already in Use (EADDRINUSE)
**Error:** `address already in use :::3000`

**Solution:** Kill all Node.js processes and restart:
```powershell
taskkill /F /IM node.exe
```

To see what's using port 3000:
```powershell
netstat -ano | findstr :3000
tasklist | findstr <PID>
```

### PowerShell Execution Policy Errors
**Error:** `cannot be loaded because running scripts is disabled on this system`

**Solution:** Use `cmd /c` as shown in Quick Start, or permanently fix with:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Server Starts But Page Won't Load
1. Check if server is running:
```powershell
(Invoke-WebRequest -Uri http://localhost:3000 -UseBasicParsing).StatusCode
```
Should return `200`.

2. Check for port conflicts:
```powershell
netstat -ano | findstr :3000
```

3. Try a different port:
```powershell
cmd /c "cd frontend && set PORT=3001 && npm run dev"
```

### Build Errors
If you see build/compilation errors:
```powershell
cmd /c "cd frontend && npm install"
cmd /c "cd frontend && npm run build"
```

### Missing Environment Variables
The app expects a `.env` file. Copy from the example:
```powershell
copy frontend\.env.example frontend\.env
```
Then edit `frontend\.env` with your actual API keys.

---

## Production Build (Future)

To create a production build:
```powershell
cmd /c "cd frontend && npm run build"
```

To start the production server:
```powershell
cmd /c "cd frontend && npm start"
```

---

## Common Commands Reference

| Action | Command |
|--------|---------|
| Start dev server | `cmd /c "cd frontend && npm run dev"` |
| Build for production | `cmd /c "cd frontend && npm run build"` |
| Start production server | `cmd /c "cd frontend && npm start"` |
| Install dependencies | `cmd /c "cd frontend && npm install"` |
| Run linter | `cmd /c "cd frontend && npm run lint"` |
| Kill all Node processes | `taskkill /F /IM node.exe` |

---

## Notes

- The server uses **Turbopack** for faster builds (Next.js 15)
- There's a warning about Webpack config vs Turbopack - this is cosmetic and doesn't affect functionality
- The `.next` folder contains build cache - delete it if builds act weird: `Remove-Item -Recurse -Force frontend\.next`
