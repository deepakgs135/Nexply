# NEXPLY React workspace

The web interface is built with React, TypeScript, Vite, and Lucide icons.

## Local development

Start the FastAPI backend from `backend` in one terminal:

```powershell
.\.venv\Scripts\python.exe .\run.py
```

Then start the React dev server from the repository root (`D:\Nexply`) in another terminal:

```powershell
npm --prefix backend/frontend install
npm run dev
```

Open `http://127.0.0.1:5173`. Vite proxies API calls to the backend at port 8000.

## Production build

```powershell
npm --prefix backend/frontend install
npm run build
```

Vite writes the production app to `frontend/dist`. FastAPI serves that build at `http://127.0.0.1:8000/` and its `/assets` bundle. Rebuild after changing the React app.
