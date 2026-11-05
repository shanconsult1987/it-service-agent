# it-service-agent

## Run locally

From the project root:

```powershell
python -m app.server
```

Direct-file startup is also supported:

```powershell
python .\app\server.py
```

You can also run the server by its absolute file path from another directory.
Direct-file startup resolves the application's package imports automatically.

The server listens at http://127.0.0.1:8000.

POST requests to `/investigate`, `/resolve`, and `/orchestrate` require a
non-empty `description` (up to 2000 characters) and an `incident_id` in the
format `INC-` followed by 4 to 8 digits, for example `INC-1001`.
Blocked phrases are configured in [security_policy.json](data/security_policy.json).
Requests that fail these checks return HTTP 400 with `error` and `details`.

## Tests

```powershell
python -m pytest tests
```