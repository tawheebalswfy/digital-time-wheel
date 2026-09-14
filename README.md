# DIGITAL TIME WHEEL

Multi-symbol MT5 market-data, Time Wheel, signal-audit, research, and controlled DEMO execution platform.

## Windows Server setup

1. Install Python 3.11 x64 and MetaTrader 5. Sign in to the intended broker terminal; the application does not install or modify MT5.
2. Install backend dependencies:

   ```powershell
   py -3.11 -m venv .venv
   .\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt
   ```

3. For frontend development/build, install Node.js 22.13+ and run:

   ```powershell
   cd frontend
   npm install
   npm run build
   cd ..
   ```

4. Start the local application:

   ```powershell
   .\\scripts\\start-local.ps1
   ```

   The frontend is available at `http://127.0.0.1:5173/` and backend health at `http://127.0.0.1:8000/api/health`.

Trading starts disabled after restart and remains DEMO-account gated. No credentials belong in this repository; use the MT5 terminal and the application settings UI for local configuration.
