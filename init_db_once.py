import sqlite3
from pathlib import Path

DB = Path("costing.db")

conn = sqlite3.connect(DB)
conn.execute("""
CREATE TABLE IF NOT EXISTS submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,

    process TEXT NOT NULL,
    supplier TEXT NOT NULL,
    material_thickness REAL NOT NULL,
    foam_thickness REAL NOT NULL,
    bladder_type TEXT NOT NULL,
    panel_config INTEGER NOT NULL,

    quantity INTEGER NOT NULL,
    base_per_ball_usd REAL NOT NULL,
    total_for_quantity_usd REAL NOT NULL
)
""")
conn.commit()
conn.close()

print("Database initialized:", DB.resolve())
