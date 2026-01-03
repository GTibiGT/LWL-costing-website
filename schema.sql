CREATE TABLE IF NOT EXISTS submissions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

  process TEXT NOT NULL,
  supplier TEXT NOT NULL,
  material_thickness REAL NOT NULL,
  foam_thickness REAL NOT NULL,
  bladder_type TEXT NOT NULL,
  panel_config INTEGER NOT NULL,

  quantity INTEGER NOT NULL CHECK(quantity >= 1),

  base_per_ball_usd REAL NOT NULL,
  total_for_quantity_usd REAL NOT NULL
);

--Helpful index for "latest submissions"
CREATE INDEX IF NOT EXISTS idx_submissions_created_at
ON submissions(created_at);
