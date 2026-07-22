# app/app.py
from flask import Flask, request
from prometheus_client import generate_latest, Counter, Histogram
from prometheus_client.exposition import CONTENT_TYPE_LATEST
import time
import logging
import json
import datetime
import os

app = Flask(__name__)

# JSON logging
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": datetime.datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "pathname": record.pathname,
            "lineno": record.lineno,
        }
        if hasattr(record, "extra_data"):
            log_record.update(record.extra_data)
        return json.dumps(log_record)

handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
app.logger.handlers = []  # avoid duplicate handlers
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)

# Prometheus metrics
REQUEST_COUNT = Counter(
    "flask_app_requests_total",
    "total number of app requests",
    ["method", "endpoint", "status_code"],
)
REQUEST_LATENCY = Histogram(
    "flask_app_request_latency_seconds",
    "Request latency in seconds",
    ["method", "endpoint"],
)

@app.route("/metrics")
def metrics():
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}

@app.route("/hello")
def hello():
    start_time = time.time()
    try:
        response = "Hello from Flask!"
        status_code = 200
        app.logger.info(
            "Hello endpoint called",
            extra={
                "extra_data": {
                    "endpoint": request.path,
                    "method": request.method,
                    "user_agent": request.user_agent.string,
                    "remote_addr": request.remote_addr,
                }
            },
        )
    except Exception as e:
        app.logger.error(
            f"Error processing /hello: {e}",
            extra={
                "extra_data": {
                    "endpoint": request.path,
                    "method": request.method,
                    "error": str(e),
                }
            },
        )
        response = "Internal Server Error"
        status_code = 500
    finally:
        REQUEST_COUNT.labels(request.method, request.path, status_code).inc()
        REQUEST_LATENCY.labels(request.method, request.path).observe(
            time.time() - start_time
        )
    return response, status_code

if __name__ == "__main__":
    port = int(os.getenv("APP_PORT", "5000"))
    app.run(host="0.0.0.0", port=port)