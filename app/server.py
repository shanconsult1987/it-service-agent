from http.server import (
    BaseHTTPRequestHandler,
    HTTPServer
)

import json
import sys
from pathlib import Path


if __package__ in (None, ""):
    # Direct script execution places app, not the project root, on sys.path.
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.agent import (
    investigate,
    generate_resolution
)

from app.orchestrator import (
    ITServiceOrchestrator
)


orchestrator = (
    ITServiceOrchestrator()
)


class Handler(
    BaseHTTPRequestHandler
):

    def send_json(
        self,
        data,
        status=200
    ):

        body = json.dumps(
            data,
            indent=2
        ).encode("utf-8")

        self.send_response(status)

        self.send_header(
            "Content-Type",
            "application/json"
        )

        self.send_header(
            "Content-Length",
            str(len(body))
        )

        self.end_headers()

        self.wfile.write(body)

    def read_json(self):

        length = int(
            self.headers.get(
                "Content-Length",
                "0"
            )
        )

        raw = self.rfile.read(
            length
        )

        return json.loads(
            raw.decode("utf-8")
        )

    def do_GET(self):

        if self.path == "/":

            self.send_json({
                "service":
                    "Contoso IT Service Agent",
                "status":
                    "running"
            })

            return

        self.send_json(
            {"error": "Not found"},
            404
        )

    def do_POST(self):

        if self.path == "/investigate":

            payload = self.read_json()

            result = investigate(
                payload.get(
                    "description",
                    ""
                )
            )

            self.send_json(result)

            return

        if self.path == "/resolve":

            payload = self.read_json()

            result = generate_resolution(
                payload.get(
                    "description",
                    ""
                )
            )

            self.send_json(result)

            return

        if self.path == "/orchestrate":

            payload = self.read_json()

            incident_id = payload.get(
                "incident_id",
                "INC-DEMO"
            )

            description = payload.get(
                "description",
                ""
            )

            if not description:

                self.send_json(
                    {
                        "error":
                            "description required"
                    },
                    400
                )

                return

            result = orchestrator.process(
                incident_id,
                description
            )

            self.send_json(result)

            return

        self.send_json(
            {"error": "Not found"},
            404
        )


if __name__ == "__main__":

    server = HTTPServer(
        ("127.0.0.1", 8000),
        Handler
    )

    print(
        "Contoso IT Service Agent "
        "running on "
        "http://127.0.0.1:8000"
    )

    server.serve_forever()