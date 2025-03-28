from datetime import datetime
import sqlite3
from flask import Flask, jsonify, request

app = Flask(__name__)

def init_db():
    """
    Initializes the database and creates the 'tokens' table if it doesn't exist.
    """
    conn = sqlite3.connect("tokens.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token TEXT UNIQUE,
            expiration DATETIME,
            ip_address TEXT
        )
        """
    )
    conn.commit()
    conn.close()

@app.route("/Tlogin", methods=["GET"])
def token_info():
    """
    Fetches and returns the information of a token including expiration and IP address.
    If the token is invalid or expired, it returns an error.
    """
    token = request.args.get("token")
    if not token:
        return jsonify({"error": "Token is required"}), 400

    conn = sqlite3.connect("tokens.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT token, expiration, ip_address FROM tokens WHERE token = ?", (token,)
    )
    result = cursor.fetchone()
    conn.close()

    if not result:
        return jsonify({"error": "Token not found or invalid"}), 400

    token_data = {
        "token": result[0],
        "expiration": result[1],
        "ip_address": result[2],
    }

    expiration = datetime.fromisoformat(token_data["expiration"])
    remaining_time = (expiration - datetime.utcnow()).total_seconds()

    if remaining_time <= 0:
        return jsonify({"error": "Token has expired"}), 400

    return jsonify(
        {
            "token": token_data["token"],
            "expiration": token_data["expiration"],
            "ip_address": token_data["ip_address"],
            "remaining_time": remaining_time,
        }
    )


if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=1830)
