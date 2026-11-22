

import math
from datetime import datetime

from flask import Flask, jsonify, request
from flask_cors import CORS

from db import get_connection

SERIES_ID = "CPIAUCNS"

app = Flask (__name__)
cors = CORS(app, origins="http://localhost:5173", supports_credentials=True)


def parse_month(text):
    """Turn '1985-03' or '1985-03-17' into a date on the 1st of that month.

    Returns None if the text isn't a valid date.

    """

    for fmt in ("%Y-%m-%d", "%Y-%m"):
        try:
            parsed = datetime.strptime(text, fmt)
            return parsed.date().replace(day=1)
        except ValueError:
            continue
    return None

def error(message, status):
    return jsonify({"error": message}), status

     

@app.route("/api/health", methods=["GET"])

def health():
    """Temporary test route: proves Flask can reach MySQL."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM observations")
        (count,) = cur.fetchone()
        cur.close()
    finally: 
        conn.close()
    return jsonify({"status": "ok", "observations": count})

@app.route("/api/value", methods=["GET"])
def value():

    "get amount and date form the request"

    amount_raw = request.args.get("amount")
    data_raw = request.args.get("date")
    if amount_raw is None or data_raw is None:
        return error("Both 'amount' and 'date' are required.", 400)
    
    try:
        amount = float(amount_raw)
    except ValueError:
        return error("'amount' must be a number.", 400)
    if not math.isfinite(amount) or amount <= 0:
        return error ("'amount' must be a positive number.", 400)


    then_month = parse_month(data_raw)
    if then_month is None:
        return error ("'date' must look like 1985-03 or 1985-03-17.", 400)

    #2. look up the data we need.

    conn = get_connection()

    try:
        cur = conn.cursor()
        cur.execute(
       " SELECT MIN(obs_date), MAX(obs_date) FROM observations WHERE series_id = %s",
       (SERIES_ID,),
        )
        first_date, latest_date = cur.fetchone()
        if first_date is None:
            return error("No CPI data found. Run cpi.py to load it.", 500)

        if then_month < first_date:
            return error(
                f"Data starts in {first_date.strftime('%Y-%m')}. Pick a later date.", 400,    
            )

        if then_month > latest_date:
            return error(f"Latest available data is {latest_date.strftime('%Y-%m')}. Pick an earlier date.",400,)

        cur.execute(
            "SELECT obs_date, value FROM observations "
            "WHERE series_id = %s AND obs_date IN (%s, %s)",
            (SERIES_ID, then_month, latest_date),
        )

        cpi_by_date = {row_date: row_value for row_date, row_value in cur.fetchall()}
        cur.close()
    finally:
        conn.close()

    if then_month not in cpi_by_date:
        return error(f"No CPI data for {then_month.strftime('%Y-%m')}.", 404)

    #apply the formula. MySQL gives back Decimal values. so conver to float.
    cpi_then = float(cpi_by_date[then_month])
    cpi_now = float(cpi_by_date[latest_date])
    value_today = amount * (cpi_now / cpi_then)

    return jsonify(
        {
            "amount": amount,
            "from_date": then_month.strftime("%Y-%m"),
            "to_date": latest_date.strftime("%Y-%m"),
            "cpi_from": cpi_then,
            "cpi_to": cpi_now,
            "value_today": round(value_today, 2),
        }
    )

@app.route("/api/series", methods=["GET"])
def series():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT obs_date, value FROM observations WHERE series_id = %s ORDER BY obs_date",  (SERIES_ID,), )

        rows = cur.fetchall()
        cur.close()
    finally:
        conn.close()

    points = [
    {"date": obs_date.strftime("%Y-%m"), "value": float(value)}
    for obs_date, value in rows
]

    return jsonify(points)





if __name__ == "__main__":
    app.run(debug=True, port=8080)
 
