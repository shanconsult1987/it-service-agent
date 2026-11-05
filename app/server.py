from http.server import BaseHTTPRequestHandler, HTTPServer

import json

import sys

import time

from pathlib import Path


if not __package__:

    sys.path.insert(
        0,
        str(
            Path(__file__).resolve().parent.parent
        )
    )


from app.agent import (
    investigate,
    generate_resolution
)

from app.orchestrator import (
    ITServiceOrchestrator
)

from app.guardrails import (
    enforce_request_policy
)

from app.audit import (
    record_event
)

from app.monitoring import (
    record_http_request
)

from app.dashboard import (
    dashboard_snapshot
)

from app.dashboard_page import HTML


orchestrator = ITServiceOrchestrator()


class Handler(BaseHTTPRequestHandler):

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
            "application/json; charset=utf-8"
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

        if length > 100_000:

            raise ValueError(
                "Request body is too large"
            )

        raw = self.rfile.read(length)

        return json.loads(
            raw.decode("utf-8") or "{}"
        )


    def do_GET(self):

        start = time.perf_counter()

        status = 200

        try:

            if self.path == "/":

                self.send_json({
                    "service": "Contoso IT Service Agent",
                    "status": "running"
                })

            elif self.path == "/api/dashboard":

                self.send_json(
                    dashboard_snapshot()
                )

            elif self.path == "/dashboard":

                body = HTML.encode("utf-8")

                self.send_response(200)

                self.send_header(
                    "Content-Type",
                    "text/html; charset=utf-8"
                )

                self.send_header(
                    "Content-Length",
                    str(len(body))
                )

                self.end_headers()

                self.wfile.write(body)

            else:

                status = 404

                self.send_json(
                    {"error": "Not found"},
                    status
                )

        except Exception as exc:

            status = 500

            self.send_json(
                {
                    "error": "Internal server error",
                    "type": type(exc).__name__
                },
                status
            )

        finally:

            record_http_request(
                self.path,
                status,
                (
                    time.perf_counter() - start
                ) * 1000
            )


    def do_POST(self):

        start = time.perf_counter()

        status = 200

        incident_id = None

        try:

            payload = self.read_json()

            description = payload.get(
                "description",
                ""
            )

            incident_id = payload.get(
                "incident_id",
                "INC-DEMO"
            )

            if self.path in (
                "/investigate",
                "/resolve",
                "/orchestrate"
            ):

                policy = enforce_request_policy(
                    description,
                    incident_id
                )

                if not policy["allowed"]:

                    status = 400

                    record_event(
                        "guardrail_block",
                        incident_id,
                        "blocked",
                        {
                            "reason": policy["reason"]
                        }
                    )

                    self.send_json(
                        {
                            "error": policy["reason"],
                            "details": policy["errors"]
                        },
                        status
                    )

                    return

                if self.path == "/investigate":

                    self.send_json(
                        investigate(description)
                    )

                elif self.path == "/resolve":

                    self.send_json(
                        generate_resolution(description)
                    )

                else:

                    result = orchestrator.process(
                        incident_id,
                        description
                    )

                    record_event(
                        "incident_orchestrated",
                        incident_id,
                        result.get(
                            "status",
                            "Escalated"
                        ),
                        {
                            "category":
                                result.get(
                                    "triage",
                                    {}
                                ).get("category")
                        }
                    )

                    self.send_json(result)

            else:

                status = 404

                self.send_json(
                    {"error": "Not found"},
                    status
                )

        except (
            ValueError,
            json.JSONDecodeError
        ) as exc:

            status = 400

            self.send_json(
                {"error": str(exc)},
                status
            )

        except Exception as exc:

            status = 500

            record_event(
                "request_error",
                incident_id,
                "error",
                {
                    "error_type": type(exc).__name__
                }
            )

            self.send_json(
                {
                    "error": "Internal server error",
                    "type": type(exc).__name__
                },
                status
            )

        finally:

            record_http_request(
                self.path,
                status,
                (
                    time.perf_counter() - start
                ) * 1000
            )


if __name__ == "__main__":

    server = HTTPServer(
        ("127.0.0.1", 8000),
        Handler
    )

    print(
        "IT Service Agent running on "
        "http://127.0.0.1:8000"
    )

    server.serve_forever()