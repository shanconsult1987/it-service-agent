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

## Tests

```powershell
python -m unittest discover -s tests
```