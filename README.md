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

The server listens at http://127.0.0.1:8000.

## Tests

```powershell
python -m unittest discover -s tests
```