# it-service-agent

## Run the server

From the project root:

```powershell
python -m app.server
```

Direct script execution also works, including from another working directory:

```powershell
python C:\Users\shivensingh\it-service-agent\app\server.py
```

The server listens at http://127.0.0.1:8000. Dashboard endpoints are
`/dashboard/roi` and `/dashboard/responsible-ai`. Press Ctrl+C to stop it.

## Dashboard data

The dashboard reads ROI inputs from `data/roi.json` and responsible AI
controls from `data/responsible_ai.json`. Both files must contain valid JSON
and be saved as UTF-8 (with or without a byte order mark).

If loading fails, the error identifies the file. Empty files must be restored
with their intended data; invalid JSON errors include the line and column to
correct. The dashboard does not substitute empty or default data on failure.

Run the dashboard regression tests from the project root:

```powershell
python -m pytest tests\test_dashboard.py -q
```