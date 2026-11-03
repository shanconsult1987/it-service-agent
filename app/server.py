from http.server import (
    BaseHTTPRequestHandler,
    HTTPServer
)

import json

if __package__:
    from .agent import investigate
    from .dashboard import (
        calculate_roi,
        responsible_ai_summary
    )
else:
    from agent import investigate
    from dashboard import (
        calculate_roi,
        responsible_ai_summary
    )


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
            "application/json"
        )

        self.send_header(
            "Content-Length",
            str(len(body))
        )

        self.end_headers()

        self.wfile.write(body)

    def do_GET(self):

        if self.path == "/":

            self.send_json({
                "service":
                    "IT Service Agent",
                "status":
                    "running"
            })

            return

        if self.path == "/dashboard/roi":

            self.send_json(
                calculate_roi()
            )

            return

        if self.path == (
            "/dashboard/responsible-ai"
        ):

            self.send_json(
                responsible_ai_summary()
            )

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
        "IT Service Agent running "
        "on http://127.0.0.1:8000"
    )

    server.serve_forever()