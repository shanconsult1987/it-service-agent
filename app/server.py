
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import logging
import sys
import time
import uuid
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(
        0,
        str(Path(__file__).resolve().parent.parent)
    )

from app.agent import investigate, generate_resolution
from app.orchestrator import ITServiceOrchestrator
from app.guardrails import (
    validate_incident_description,
    validate_incident_id
)
from app.monitoring import record_request, snapshot
from app.audit import write_audit_event
from app.dashboard import executive_dashboard
from app.dashboard_page import render_dashboard

ROOT = Path(__file__).resolve().parent.parent
MAX_BODY_BYTES = 16 * 1024

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("it_service_agent")

orchestrator = ITServiceOrchestrator()


def emit_log(event):
    """Emit structured logs without incident text or secrets."""
    logger.info(json.dumps(event, separators=(",", ":")))


class Handler(BaseHTTPRequestHandler):

    def log_message(self, format_string, *args):
        # Use emit_log instead of the default access log, which can
        # include request-target details.
        return

    def _correlation_id(self):
        supplied = self.headers.get("X-Request-ID", "").strip()

        if (
            supplied
            and len(supplied) <= 80
            and all(
                char.isalnum() or char in "-_"
                for char in supplied
            )
        ):
            return supplied

        return str(uuid.uuid4())

    def _start_request(self):
        self.request_started = time.perf_counter()
        self.correlation_id = self._correlation_id()
        self.request_path = self.path.split("?", 1)[0]

    def send_json(self, data, status=200):
        elapsed_ms = (
            time.perf_counter() - self.request_started
        ) * 1000

        record_request(
            self.request_path,
            status,
            elapsed_ms
        )

        emit_log({
            "event": "http_response",
            "correlation_id": self.correlation_id,
            "path": self.request_path,
            "status": status,
            "elapsed_ms": round(elapsed_ms, 2)
        })

        body = json.dumps(data, indent=2).encode("utf-8")

        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Request-ID", self.correlation_id)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def send_html(self, html, status=200):
        elapsed_ms = (
            time.perf_counter() - self.request_started
        ) * 1000

        record_request(
            self.request_path,
            status,
            elapsed_ms
        )

        emit_log({
            "event": "http_response",
            "correlation_id": self.correlation_id,
            "path": self.request_path,
            "status": status,
            "elapsed_ms": round(elapsed_ms, 2)
        })

        body = html.encode("utf-8")

        self.send_response(status)
        self.send_header(
            "Content-Type",
            "text/html; charset=utf-8"
        )
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Request-ID", self.correlation_id)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def read_json(self):
        content_length = self.headers.get("Content-Length")

        if content_length is None:
            raise ValueError("Content-Length is required.")

        try:
            length = int(content_length)
        except ValueError as error:
            raise ValueError("Invalid Content-Length.") from error

        if length < 0 or length > MAX_BODY_BYTES:
            raise OverflowError(
                f"Request body must not exceed {MAX_BODY_BYTES} bytes."
            )

        content_type = self.headers.get("Content-Type", "")
        if "application/json" not in content_type.lower():
            raise TypeError("Content-Type must be application/json.")

        raw = self.rfile.read(length)

        try:
            payload = json.loads(raw.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            raise ValueError("Request body must be valid JSON.") from error

        if not isinstance(payload, dict):
            raise ValueError("JSON body must be an object.")

        return payload

    def _readiness(self):
        required_files = [
            ROOT / "data" / "agent_state.json",
            ROOT / "data" / "agent_memory.md",
            ROOT / "data" / "responsible_ai.json",
            ROOT / "data" / "roi.json",
            ROOT / "knowledge" / "it-support.md"
        ]

        missing = [
            str(path.relative_to(ROOT))
            for path in required_files
            if not path.is_file() or not path.exists()
        ]

        return {
            "ready": not missing,
            "missing_files": missing,
            "scope": "local_file_readiness_check"
        }

    def do_GET(self):
        self._start_request()

        if self.request_path == "/":
            self.send_json({
                "service": "Contoso IT Service Agent",
                "status": "running",
                "correlation_id": self.correlation_id
            })
            return

        if self.request_path == "/health":
            self.send_json({
                "status": "healthy",
                "service": "Contoso IT Service Agent",
                "correlation_id": self.correlation_id
            })
            return

        if self.request_path == "/ready":
            result = self._readiness()
            self.send_json(
                {
                    **result,
                    "correlation_id": self.correlation_id
                },
                200 if result["ready"] else 503
            )
            return

        if self.request_path == "/metrics":
            self.send_json(snapshot())
            return

        if self.request_path == "/api/dashboard":
            try:
                self.send_json(executive_dashboard())
            except (ValueError, KeyError, OSError) as error:
                emit_log({
                    "event": "dashboard_data_error",
                    "correlation_id": self.correlation_id,
                    "error_type": type(error).__name__
                })
                self.send_json(
                    {"error": "Dashboard data is unavailable."},
                    500
                )
            return

        if self.request_path == "/dashboard":
            try:
                self.send_html(render_dashboard())
            except (ValueError, KeyError, OSError) as error:
                emit_log({
                    "event": "dashboard_page_error",
                    "correlation_id": self.correlation_id,
                    "error_type": type(error).__name__
                })
                self.send_json(
                    {"error": "Dashboard page is unavailable."},
                    500
                )
            return

        self.send_json({"error": "Not found"}, 404)

    def do_POST(self):
        self._start_request()

        if self.request_path not in (
            "/investigate",
            "/resolve",
            "/orchestrate"
        ):
            self.send_json({"error": "Not found"}, 404)
            return

        try:
            payload = self.read_json()
        except OverflowError:
            write_audit_event(
                "request_rejected",
                "rejected",
                self.correlation_id,
                reason_code="REQUEST_BODY_TOO_LARGE"
            )
            self.send_json(
                {"error": "Request body is too large."},
                413
            )
            return
        except TypeError:
            write_audit_event(
                "request_rejected",
                "rejected",
                self.correlation_id,
                reason_code="INVALID_CONTENT_TYPE"
            )
            self.send_json(
                {"error": "Content-Type must be application/json."},
                415
            )
            return
        except ValueError:
            write_audit_event(
                "request_rejected",
                "rejected",
                self.correlation_id,
                reason_code="INVALID_JSON"
            )
            self.send_json(
                {"error": "Request body must be a JSON object."},
                400
            )
            return

        description = payload.get("description", "")
        validation = validate_incident_description(description)

        if not validation["allowed"]:
            write_audit_event(
                "guardrail_rejection",
                "rejected",
                self.correlation_id,
                reason_code=validation["code"]
            )
            self.send_json({
                "error": validation["reason"],
                "guardrail": validation,
                "correlation_id": self.correlation_id
            }, 400)
            return

        description = validation["description"]

        try:
            if self.request_path == "/investigate":
                result = investigate(description)
                self.send_json({
                    **result,
                    "correlation_id": self.correlation_id
                })
                return

            if self.request_path == "/resolve":
                result = generate_resolution(description)
                self.send_json({
                    **result,
                    "correlation_id": self.correlation_id
                })
                return

            incident_id = payload.get("incident_id", "INC-DEMO")
            id_result = validate_incident_id(incident_id)

            if not id_result["allowed"]:
                write_audit_event(
                    "guardrail_rejection",
                    "rejected",
                    self.correlation_id,
                    reason_code=id_result["code"]
                )
                self.send_json({
                    "error": id_result["reason"],
                    "guardrail": id_result,
                    "correlation_id": self.correlation_id
                }, 400)
                return

            result = orchestrator.process(
                id_result["incident_id"],
                description,
                correlation_id=self.correlation_id
            )
            self.send_json(result)

        except Exception as error:
            # Do not expose exception messages, prompts, keys or stack
            # traces in an HTTP response.
            emit_log({
                "event": "request_processing_error",
                "correlation_id": self.correlation_id,
                "path": self.request_path,
                "error_type": type(error).__name__
            })
            write_audit_event(
                "request_processing_error",
                "failed",
                self.correlation_id,
                reason_code=type(error).__name__
            )
            self.send_json({
                "error": "The request could not be processed.",
                "correlation_id": self.correlation_id
            }, 500)


if __name__ == "__main__":
    server = ThreadingHTTPServer(
        ("127.0.0.1", 8000),
        Handler
    )
    print(
        "Contoso IT Service Agent running at "
        "http://127.0.0.1:8000"
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
    finally:
        server.server_close()
