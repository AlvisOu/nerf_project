import sqlite3
import csv

def read_transformations(transform_db_path):
    conn = sqlite3.connect(transform_db_path)
    c = conn.cursor()

    # Assumes table is called 'transforms' and has block_name and 16 matrix columns
    c.execute("SELECT name FROM sqlite_master WHERE type='table';")
    table_names = [row[0] for row in c.fetchall()]
    if "transforms" not in table_names:
        raise ValueError("No 'transforms' table found in the database.")

    c.execute("SELECT * FROM transforms;")
    rows = c.fetchall()
    col_names = [desc[0] for desc in c.description]

    transforms = {}
    for row in rows:
        row_dict = dict(zip(col_names, row))
        block_name = row_dict['block_name']
        matrix = [row_dict[f"t{i}{j}"] for i in range(4) for j in range(4)]
        transforms[block_name] = matrix

    conn.close()
    return transforms

def read_boundaries(boundary_txt_path):
    boundaries = {}
    with open(boundary_txt_path, "r") as f:
        reader = csv.reader(f)
        for row in reader:
            (
                block_name,
                left_boundary, left_neighbor,
                right_boundary, right_neighbor,
                front_boundary, front_neighbor,
                back_boundary, back_neighbor
            ) = row
            boundaries[block_name] = {
                "left_boundary": float(left_boundary),
                "left_neighbor": left_neighbor,
                "right_boundary": float(right_boundary),
                "right_neighbor": right_neighbor,
                "front_boundary": float(front_boundary),
                "front_neighbor": front_neighbor,
                "back_boundary": float(back_boundary),
                "back_neighbor": back_neighbor
            }
    return boundaries

def write_combined_table(output_db_path, transforms, boundaries):
    conn = sqlite3.connect(output_db_path)
    c = conn.cursor()

    # Drop if exists for clean slate
    c.execute("DROP TABLE IF EXISTS blocks")

    # Create new blocks table
    c.execute("""
        CREATE TABLE blocks (
            block_name TEXT PRIMARY KEY,
            t00 REAL, t01 REAL, t02 REAL, t03 REAL,
            t10 REAL, t11 REAL, t12 REAL, t13 REAL,
            t20 REAL, t21 REAL, t22 REAL, t23 REAL,
            t30 REAL, t31 REAL, t32 REAL, t33 REAL,
            left_boundary REAL,
            left_neighbor TEXT,
            right_boundary REAL,
            right_neighbor TEXT,
            front_boundary REAL,
            front_neighbor TEXT,
            back_boundary REAL,
            back_neighbor TEXT
        )
    """)

    for block_name, matrix in transforms.items():
        if block_name not in boundaries:
            print(f"[Warning] No boundary info for {block_name}, skipping...")
            continue

        b = boundaries[block_name]
        values = (
            block_name,
            *matrix,
            b["left_boundary"], b["left_neighbor"],
            b["right_boundary"], b["right_neighbor"],
            b["front_boundary"], b["front_neighbor"],
            b["back_boundary"], b["back_neighbor"]
        )

        c.execute("""
            INSERT INTO blocks VALUES (
                ?,?,?,?,?,?,?,?,?,
                ?,?,?,?,?,?,?,?,
                ?,?,?,?,?,?,?,?
            )
        """, values)

    conn.commit()
    conn.close()
    print(f"✅ Combined table written to {output_db_path}")

if __name__ == "__main__":
    # Change these paths to your actual files
    transform_db = "transforms.sqlite"
    boundary_txt = "boundaries.txt"
    output_db = "blocks.sqlite"

    transforms = read_transformations(transform_db)
    boundaries = read_boundaries(boundary_txt)
    write_combined_table(output_db, transforms, boundaries)
