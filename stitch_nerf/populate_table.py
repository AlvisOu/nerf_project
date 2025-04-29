import sqlite3
import csv

# CONFIG
db_path = "your_db.sqlite"
boundary_txt_path = "boundaries.txt"

# Connect to DB
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Create new combined table
cur.execute("""
    DROP TABLE IF EXISTS blocks;
""")

cur.execute("""
    CREATE TABLE blocks (
        block_name TEXT PRIMARY KEY,
        t00 REAL, t01 REAL, t02 REAL, t03 REAL,
        t10 REAL, t11 REAL, t12 REAL, t13 REAL,
        t20 REAL, t21 REAL, t22 REAL, t23 REAL,
        t30 REAL, t31 REAL, t32 REAL, t33 REAL,
        left_boundary REAL, left_neighbor TEXT,
        right_boundary REAL, right_neighbor TEXT,
        front_boundary REAL, front_neighbor TEXT,
        back_boundary REAL, back_neighbor TEXT
    );
""")

# Load all transforms into a dictionary for fast lookup
cur.execute("SELECT * FROM transforms;")
transform_rows = cur.fetchall()
transform_dict = {row[0]: row[1:] for row in transform_rows}

# Parse boundaries and insert into combined table
with open(boundary_txt_path, newline='') as f:
    reader = csv.reader(f)
    for row in reader:
        block_name = row[0]
        boundaries = row[1:]

        if block_name not in transform_dict:
            print(f"[WARNING] Block '{block_name}' not found in transforms table.")
            continue

        transform = transform_dict[block_name]
        assert len(transform) == 16, f"Transform for '{block_name}' must have 16 values."

        # Combine and insert
        full_row = [block_name] + list(transform) + boundaries
        cur.execute("""
            INSERT INTO blocks VALUES (
                ?,?,?,?,?,?,?,?, ?,?,?,?,?,?,?,?,
                ?,?, ?,?, ?,?, ?,?
            )
        """, full_row)

print("blocks table successfully created.")
conn.commit()
conn.close()
