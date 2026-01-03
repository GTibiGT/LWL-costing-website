from flask import Flask, render_template, request, jsonify
import sqlite3
from pathlib import Path


app = Flask(__name__)
DB_PATH = Path("costing.db")

# ---- Cost tables (USD) ----
PROCESS_COST = {
    "COT-B": 0.0,
    "COT-B LFB": 0.0,
    "Hybrid G-2": 0.0,
    "Hybrid G-1": 0.0,
    "Hybrid G-1 Light": 0.0,
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
    "Wound_B50": 2.7,
    "Wound_B80": 2.9,
    "Patch": 3.5,
    "Self_Patch": 3.0,
    "Foam Filled": 1.8,
}

PANEL_COST = {
    32: 0.0,
    30: 0.0,
    28: 0.0,
    24: 0.0,
    22: 0.0,
    20: 0.0,
    18: 0.0,
    14: 0.0,
    12: 0.0,
    10: 0.0,
    8: 0.0,
    6: 0.0,
    4: 0.0,
}

LABOR_COST_PER_BALL = 1.0
OVERHEAD_COST_PER_BALL = 1.0


import sqlite3
from pathlib import Path

DB_PATH = Path("costing.db")
SCHEMA_PATH = Path("schema.sql")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    conn.commit()
    conn.close()

def compute_base_total_usd(process: str, supplier: str, material_thickness: float,
                           foam_thickness: float, bladder_type: str, panel_config: int) -> float:
    """Compute base total in USD from selections."""
    return (
        PROCESS_COST[process]
        + SUPPLIER_COST[supplier]
        + MATERIAL_THICKNESS_COST[material_thickness]
        + FOAM_THICKNESS_COST[foam_thickness]
        + BLADDER_COST[bladder_type]
        + LABOR_COST_PER_BALL
        + OVERHEAD_COST_PER_BALL
        + PANEL_COST[panel_config]
    )


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/save", methods=["POST"])
def api_save():
    data = request.get_json(silent=True) or {}

    required = ["process", "supplier", "material_thickness", "foam_thickness", "bladder_type", "panel_config"]
    missing = [k for k in required if not data.get(k)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    try:
        material_thickness = float(data["material_thickness"])
        foam_thickness = float(data["foam_thickness"])
        panel_config = int(data["panel_config"])
    except ValueError:
        return jsonify({"error": "Thickness values must be numbers or panel configuration must be numbers"}), 400

    try:
        quantity = int(data.get("quantity", 1))
        if quantity < 1:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({"error": "Quantity must be an integer ≥ 1"}), 400

    # ---- Base cost PER BALL (USD) ----
    try:
        base_per_ball_usd = round(
            compute_base_total_usd(
                process=data["process"],
                supplier=data["supplier"],
                material_thickness=material_thickness,
                foam_thickness=foam_thickness,
                bladder_type=data["bladder_type"],
                panel_config=panel_config,
            ),
            2
        )
    except KeyError as e:
        return jsonify({"error": f"Invalid selection: {str(e)}"}), 400

    # ---- Total for quantity ----
    total_for_quantity = round(base_per_ball_usd * quantity, 2)

    # ---- Save to DB ----
    conn = get_db()
    cur = conn.execute("""
    INSERT INTO submissions (
        process, supplier, material_thickness, foam_thickness,
        bladder_type, panel_config, quantity,
        base_per_ball_usd, total_for_quantity_usd
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (
    data["process"],
    data["supplier"],
    material_thickness,
    foam_thickness,
    data["bladder_type"],
    panel_config,
    quantity,
    base_per_ball_usd,
    total_for_quantity
))
        
    conn.commit()
    new_id = cur.lastrowid
    conn.close()

    return jsonify({
        "ok": True,
        "id": new_id,
        "per_ball_usd": base_per_ball_usd,
        "quantity": quantity,
        "total_for_quantity_usd": total_for_quantity
    })


#the link for submissions
#http://127.0.0.1:5000/api/submissions

@app.route("/submissions")
def submissions():
    conn = get_db()
    rows = conn.execute("""
        SELECT *
        FROM submissions
        ORDER BY created_at DESC
    """).fetchall()
    conn.close()

    return render_template("submissions.html", rows=rows)

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
