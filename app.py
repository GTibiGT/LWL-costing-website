from flask import Flask, render_template, request, jsonify
import sqlite3
from pathlib import Path
import os

from currency_conversion import CurrencyConverter

app = Flask(__name__)
DB_PATH = Path("costing.db")

# ---- Config ----
FIXER_API_KEY = os.environ.get("FIXER_API_KEY")  # set in environment
converter = CurrencyConverter(FIXER_API_KEY)

#Cost tables are in USD 
BASE_CURRENCY = "USD"

# ---- Cost tables (USD) ----
PROCESS_COST = {
    "COT-B": 0.0,
    "Hybrid": 0.0,
    "Foam": 0.0,
    "Machine": 0.0,
    "Hand": 0.0,
}

SUPPLIER_COST = {
    "Teijin": 2.5,
    "SanFang": 2.0,
    "Anli": 1.3,
}

MATERIAL_THICKNESS_COST = {
    0.7: 1.0,
    1.0: 1.3,
    1.2: 1.8,
}

FOAM_THICKNESS_COST = {
    2.0: 0.2,
    2.5: 0.3,
    3.0: 0.4,
    3.5: 0.5,
    4.0: 0.6,
}

BLADDER_COST = {
    "Wound_SR": 2.0,
    "Wound_B30": 2.5,
    "Patch": 3.5,
    "Self_Patch": 3.0,
}

LABOR_COST_PER_BALL = 1.0
OVERHEAD_COST_PER_BALL = 1.0


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,

            process TEXT NOT NULL,
            supplier TEXT NOT NULL,
            material_thickness REAL NOT NULL,
            foam_thickness REAL NOT NULL,
            bladder_type TEXT NOT NULL,
            currency TEXT NOT NULL,

            base_total_usd REAL NOT NULL,
            total_price REAL NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def compute_base_total_usd(process: str, supplier: str, material_thickness: float,
                           foam_thickness: float, bladder_type: str) -> float:
    """Compute base total in USD from selections."""
    return (
        PROCESS_COST[process]
        + SUPPLIER_COST[supplier]
        + MATERIAL_THICKNESS_COST[material_thickness]
        + FOAM_THICKNESS_COST[foam_thickness]
        + BLADDER_COST[bladder_type]
        + LABOR_COST_PER_BALL
        + OVERHEAD_COST_PER_BALL
    )


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/save", methods=["POST"])
def api_save():
    data = request.get_json(silent=True) or {}

    required = ["process", "supplier", "material_thickness", "foam_thickness", "bladder_type", "currency"]
    missing = [k for k in required if not data.get(k)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    # Convert numeric strings safely
    try:
        material_thickness = float(data["material_thickness"])
        foam_thickness = float(data["foam_thickness"])
    except ValueError:
        return jsonify({"error": "Thickness values must be numbers"}), 400

    # Compute base total (USD)
    try:
        base_total = compute_base_total_usd(
            process=data["process"],
            supplier=data["supplier"],
            material_thickness=material_thickness,
            foam_thickness=foam_thickness,
            bladder_type=data["bladder_type"],
        )
    except KeyError as e:
        return jsonify({"error": f"Invalid selection: {str(e)}"}), 400

    # Convert currency (USD -> selected)
    target_currency = data["currency"].upper()

    # If user chose USD, no API key needed
    if target_currency == BASE_CURRENCY:
        total_price = round(base_total, 2)
    else:
        try:
            total_price = converter.convert(base_total, BASE_CURRENCY, target_currency)
        except Exception as e:
            # Most common cause: missing FIXER_API_KEY
            return jsonify({"error": f"Currency conversion failed: {str(e)}"}), 500

    conn = get_db()
    cur = conn.execute("""
        INSERT INTO submissions
        (process, supplier, material_thickness, foam_thickness, bladder_type, currency, base_total_usd, total_price)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["process"],
        data["supplier"],
        material_thickness,
        foam_thickness,
        data["bladder_type"],
        target_currency,
        round(base_total, 2),
        total_price
    ))
    conn.commit()
    new_id = cur.lastrowid
    conn.close()

    return jsonify({
        "ok": True,
        "id": new_id,
        "base_total_usd": round(base_total, 2),
        "total_price": total_price,
        "currency": target_currency
    })


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
