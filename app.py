"""
Flask application for Dynamic Time Portal.

This file contains a minimal Flask app that serves a simple webpage
showing the current server time and a small endpoint used to log
visits into an Oracle database (optional).

The code is annotated for beginners to explain key parts:
- imports and optional Oracle client import
- helper to establish DB connection
- three routes: index (HTML), /time (JSON time), /log_visit (DB insert)

Run locally with `python app.py` or in production using gunicorn.
"""

from flask import Flask, jsonify, render_template
import datetime
import os

# Attempt to import Oracle DB client. If import fails the app will
# still run but the DB features will be disabled. This makes the
# Oracle dependency optional for development.
try:
    import oracledb

    ORACLE_AVAILABLE = True
except Exception:
    # Keep a placeholder and mark that Oracle is not available.
    oracledb = None
    ORACLE_AVAILABLE = False


# Create the Flask application. `template_folder` points to where
# the HTML template files live (templates/index.html).
app = Flask(__name__, template_folder="templates")


def get_db_conn():
    """Return an Oracle DB connection or None.

    This helper reads connection details from environment variables:
    - ORACLE_USER
    - ORACLE_PASSWORD
    - ORACLE_DSN

    If the oracledb module is not installed or the env vars are
    missing, the function returns None which the caller can handle.
    """

    if not ORACLE_AVAILABLE:
        # Oracle client not installed; skip DB functionality.
        return None

    user = os.getenv("ORACLE_USER")
    password = os.getenv("ORACLE_PASSWORD")
    dsn = os.getenv("ORACLE_DSN")

    # If any required credential is missing return None rather than
    # trying to connect and raising an exception.
    if not (user and password and dsn):
        return None

    try:
        # oracledb.connect will raise on failure; we catch and log it.
        conn = oracledb.connect(user=user, password=password, dsn=dsn)
        return conn
    except Exception as exc:
        app.logger.error("Oracle connect error: %s", exc)
        return None


@app.route("/")
def index():
    """Serve the main HTML page.

    The template contains client-side JavaScript that calls the
    `/time` endpoint each second to update the displayed time.
    """

    return render_template("index.html")


@app.route("/time")
def time_route():
    """Return the current server time in ISO format as JSON.

    Using UTC avoids timezone surprises for beginners; the frontend
    converts and formats the timestamp for display.
    """

    now = datetime.datetime.utcnow().isoformat() + "Z"
    return jsonify(server_time=now)


@app.route("/log_visit", methods=["POST"])
def log_visit():
    """Insert a visit row into the `visits` table in Oracle.

    This endpoint demonstrates a simple DB write. It will return 503
    if the DB connection could not be created (for example, missing
    oracledb or env vars). On error it returns status 500 with the
    exception string for debugging.
    """

    conn = get_db_conn()
    if not conn:
        # Inform the client there is no DB available.
        return jsonify(status="no_db"), 503

    try:
        # Use a cursor to execute SQL. This example uses SYSTIMESTAMP
        # so Oracle records the DB server timestamp.
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO visits (visited_at) VALUES (SYSTIMESTAMP)"
        )
        conn.commit()
        cur.close()
        conn.close()
        return jsonify(status="ok")

    except Exception as exc:
        # Log the full exception on the server and return a simple
        # error payload to the client for troubleshooting.
        app.logger.exception(exc)
        return jsonify(status="error", error=str(exc)), 500


if __name__ == "__main__":
    # Development server: read PORT from env (useful for containers).
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
