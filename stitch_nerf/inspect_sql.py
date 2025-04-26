import sqlite3
import numpy as np
import argparse

def load_metadata(db_path: str):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Check if table exists
    c.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='block_transforms'
    """)
    if not c.fetchone():
        raise RuntimeError("No 'block_transforms' table found in this database.")

    # Load all rows
    c.execute("SELECT * FROM block_transforms")
    rows = c.fetchall()
    column_names = [desc[0] for desc in c.description]

    conn.close()
    return column_names, rows

def print_metadata(db_path: str):
    _, rows = load_metadata(db_path)
    for row in rows:
        block_name = row[0]
        transform = np.array(row[1:17]).reshape((4, 4))
        aabb_min = np.array(row[17:20])
        aabb_max = np.array(row[20:23])

        print("="*50)
        print(f"Block: {block_name}")
        print("Transform (T_block_to_global):")
        print(transform)
        print("AABB (global):")
        print(f"Min: {aabb_min}")
        print(f"Max: {aabb_max}")
        print("="*50 + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Print all stored transforms and AABBs in metadata.sqlite")
    parser.add_argument("db", help="Path to metadata.sqlite")
    args = parser.parse_args()

    print_metadata(args.db)
