import sqlite3
import numpy as np
import csv

def load_transform_matrix(conn, block_name):
    c = conn.cursor()
    c.execute("""
        SELECT t00, t01, t02, t03,
               t10, t11, t12, t13,
               t20, t21, t22, t23,
               t30, t31, t32, t33
        FROM block_transforms
        WHERE block_name = ?
    """, (block_name,))
    row = c.fetchone()
    if row is None:
        raise ValueError(f"Transform for block '{block_name}' not found.")
    return np.array(row).reshape(4, 4)

def ensure_portals_table_exists(conn):
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS portals")
    c.execute("""
        CREATE TABLE portals (
            portal_id TEXT PRIMARY KEY,
            block_a TEXT,
            local_x_a REAL,
            local_z_a REAL,
            block_b TEXT,
            local_x_b REAL,
            local_z_b REAL,
            radius REAL
        )
    """)
    conn.commit()

def add_portals_from_csv(conn, csv_path, radius=0.5):
    c = conn.cursor()
    with open(csv_path, newline='') as csvfile:
        reader = csv.reader(csvfile)
        for idx, row in enumerate(reader):
            block_a, x_a, z_a, block_b = row
            x_a, z_a = float(x_a), float(z_a)

            T_a = load_transform_matrix(conn, block_a)
            T_b = load_transform_matrix(conn, block_b)

            # Local A → Global
            local_a = np.array([x_a, 0.0, z_a, 1.0])
            global_pos = T_a @ local_a

            # Global → Local B
            T_b_inv = np.linalg.inv(T_b)
            local_b = T_b_inv @ global_pos
            x_b, z_b = local_b[0], local_b[2]

            portal_id = f"{block_a}_to_{block_b}_{idx}"

            c.execute("""
                INSERT INTO portals (
                    portal_id,
                    block_a, local_x_a, local_z_a,
                    block_b, local_x_b, local_z_b,
                    radius
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                portal_id,
                block_a, x_a, z_a,
                block_b, x_b, z_b,
                radius
            ))

    conn.commit()

if __name__ == "__main__":
    metadata_db_path = "metadata.sqlite"
    csv_path = "portals.csv"

    conn = sqlite3.connect(metadata_db_path)
    ensure_portals_table_exists(conn)
    add_portals_from_csv(conn, csv_path)
    conn.close()
    print("Portals successfully populated.")
