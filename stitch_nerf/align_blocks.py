import open3d as o3d
import numpy as np
import os
import sqlite3
import argparse

import open3d as o3d
import numpy as np
import copy

def transform_point_cloud(pcd: o3d.geometry.PointCloud, transform: np.ndarray) -> o3d.geometry.PointCloud:
    """
    Applies a 4x4 transform to an Open3D PointCloud, preserving colors and normals.

    Parameters:
        pcd: Input PointCloud in local coordinates
        transform: 4x4 NumPy transformation matrix (T_local_to_global)

    Returns:
        Transformed PointCloud with original colors and normals (if present)
    """
    pcd_transformed = o3d.geometry.PointCloud()

    # Transform the point coordinates
    points_np = np.asarray(pcd.points)
    points_homog = np.hstack((points_np, np.ones((points_np.shape[0], 1))))
    points_transformed = (transform @ points_homog.T).T[:, :3]
    pcd_transformed.points = o3d.utility.Vector3dVector(points_transformed)

    # Copy colors if available
    if pcd.has_colors():
        pcd_transformed.colors = copy.deepcopy(pcd.colors)

    # Copy normals if available
    if pcd.has_normals():
        pcd_transformed.normals = copy.deepcopy(pcd.normals)

    return pcd_transformed

def store_transform_sqlite(db_path: str, block_name: str, transform: np.ndarray):
    """
    Stores the transformation matrix in a SQLite database.
    The transformation matrix is stored as a flattened 1D array.
    """
    print("Storing transform in SQLite database:", db_path)
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    flat = transform.flatten().tolist()
    values = [block_name] + flat
    placeholders = ', '.join(['?'] * len(values))
    columns = ', '.join(
        ['block_name'] + [f"t{i}{j}" for i in range(4) for j in range(4)]
    )

    c.execute(f"""
        INSERT INTO block_transforms ({columns})
        VALUES ({placeholders})
        """, values
    )

    conn.commit()
    conn.close()

def load_transform_from_sqlite(db_path: str, block_name: str) -> np.ndarray:
    """
    Loads the transformation matrix for a given block name from the SQLite database.
    The transformation matrix is returned as a 4x4 numpy array.
    """
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT " + ", ".join([f"t{i}{j}" for i in range(4) for j in range(4)]) + " FROM block_transforms WHERE block_name = ?", (block_name,))
    row = c.fetchone()
    conn.close()
    if row is None:
        raise ValueError(f"No transform found for block '{block_name}'")
    return np.array(row).reshape(4, 4)

def ensure_block_table_exists(db_path: str):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS block_transforms (
            block_name TEXT PRIMARY KEY,
            t00 REAL, t01 REAL, t02 REAL, t03 REAL,
            t10 REAL, t11 REAL, t12 REAL, t13 REAL,
            t20 REAL, t21 REAL, t22 REAL, t23 REAL,
            t30 REAL, t31 REAL, t32 REAL, t33 REAL
        )
    """)
    conn.commit()
    conn.close()

def icp_align(path_A: str, path_B: str, init_transform_path: str, store_db_path: str, threshold: float, viewer: bool):
    """
    Main function to align two NeRF blocks using ICP.
    It loads the camera centers from the transforms.json files, applies ICP to align them,
    and saves the aligned transforms.json for the target block.
    Stores the transformation matrix and AABB in a SQLite database.
    """
    if store_db_path:
        ensure_block_table_exists(store_db_path)

    pcd_A = o3d.io.read_point_cloud(path_A)
    pcd_B = o3d.io.read_point_cloud(path_B)

    block_name_A = os.path.basename(os.path.dirname(path_A))
    block_name_B = os.path.basename(os.path.dirname(path_B))

    print("Initial alignment (red = A, green = B)")
    if viewer:
        o3d.visualization.draw_geometries([pcd_A, pcd_B])

    print(f"pcd_A has {len(pcd_A.points)} points")
    print(f"pcd_B has {len(pcd_B.points)} points")

    # load transform from SQLite. If not found, that's the anchor block
    # need to compute global transform starting from the anchor block and propagate outwards
    try:
        transform_A = load_transform_from_sqlite(store_db_path, block_name_A)
    except ValueError:
        transform_A = np.eye(4)
        store_transform_sqlite(store_db_path, block_name_A, transform_A)

    init_transform = np.load(init_transform_path)
    print("Running ICP...")
    result = o3d.pipelines.registration.registration_icp(
        pcd_B, pcd_A, threshold,
        init_transform,
        o3d.pipelines.registration.TransformationEstimationPointToPoint()
    )
    print("Transformation matrix B → A:")
    print(result.transformation)

    transform_B_to_global = transform_A @ result.transformation

    if store_db_path:
        store_transform_sqlite(store_db_path, block_name_B, transform_B_to_global)

    if viewer:
        pcd_B_aligned = transform_point_cloud(pcd_B, transform_B_to_global)
        print("Aligned result (red = A, cyan = B-aligned)")
        o3d.visualization.draw_geometries([pcd_A, pcd_B_aligned])

def main():
    parser = argparse.ArgumentParser(description="Align NeRF blocks via ICP and store transforms.")
    parser.add_argument("ref_block", help="Path to reference block's .ply file")
    parser.add_argument("target_block", help="Path to target block's .ply file (to be aligned)")
    parser.add_argument("--init_transform", help="Path to initial transform (npy) file to use as ICP starting guess.")
    parser.add_argument("--db", default="../metadata.sqlite", help="Path to SQLite DB to store global transforms and AABB")
    parser.add_argument("--threshold", type=float, default=5.0, help="ICP distance threshold")
    parser.add_argument("--viewer", action="store_true", help="Open viewer to visualize the alignment")
    args = parser.parse_args()

    icp_align(args.ref_block, args.target_block, args.init_transform, args.db, args.threshold, args.viewer)

if __name__ == "__main__":
    main()
