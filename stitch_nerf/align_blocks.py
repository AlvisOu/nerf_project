import open3d as o3d
import numpy as np
import os
import sqlite3
import argparse

import open3d as o3d
import numpy as np
import copy
import json

def load_camera_centers(transforms_path: str) -> np.ndarray:
    with open(transforms_path) as f:
        data = json.load(f)

    centers = []
    for frame in data["frames"]:
        T = np.array(frame["transform_matrix"])
        center = T[:3, 3]
        centers.append(center)
    return np.array(centers)

def visualize_global_camera_centers(path_A, path_B, transform_A_to_global, transform_B_to_global):
    """
    Loads camera centers from paths A and B, applies global transforms, and visualizes them.
    """
    points_A = load_camera_centers(path_A)
    points_B = load_camera_centers(path_B)

    # Homogenize and transform
    points_A_homog = np.hstack((points_A, np.ones((points_A.shape[0], 1))))
    points_B_homog = np.hstack((points_B, np.ones((points_B.shape[0], 1))))

    points_A_global = (transform_A_to_global @ points_A_homog.T).T[:, :3]
    points_B_global = (transform_B_to_global @ points_B_homog.T).T[:, :3]

    # Create point clouds
    pcd_A = o3d.geometry.PointCloud()
    pcd_A.points = o3d.utility.Vector3dVector(points_A_global)
    pcd_A.paint_uniform_color([1, 0, 0])  # Red

    pcd_B = o3d.geometry.PointCloud()
    pcd_B.points = o3d.utility.Vector3dVector(points_B_global)
    pcd_B.paint_uniform_color([0, 1, 0])  # Green

    # Axis helper
    axis = o3d.geometry.TriangleMesh.create_coordinate_frame(size=1.0)

    # Visualize
    o3d.visualization.draw_geometries([pcd_A, pcd_B, axis])

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

    if init_transform_path is None:
        init_transform_path = os.path.join(os.path.dirname(path_B), "initial_transform.npy")

    print(f"Using initial transform from: {init_transform_path}")
    init_transform = np.load(init_transform_path)

    print(f"Running ICP with threshold {threshold}")
    result = o3d.pipelines.registration.registration_icp(
        pcd_B, pcd_A, threshold,
        init_transform,
        o3d.pipelines.registration.TransformationEstimationPointToPoint()
    )
    print("Transformation matrix B → A:")
    print(result.transformation)

    # Additional insights
    print(f"Inlier RMSE: {result.inlier_rmse:.6f}")
    delta = np.linalg.norm(result.transformation - init_transform)
    print(f"Δ from init transform (Frobenius norm): {delta:.6f}")

    transform_B_to_global = transform_A @ result.transformation

    if store_db_path:
        store_transform_sqlite(store_db_path, block_name_B, transform_B_to_global)

    if viewer:
        path_A_transforms = os.path.join(os.path.dirname(path_A), "transforms.json")
        path_B_transforms = os.path.join(os.path.dirname(path_B), "transforms.json")
        visualize_global_camera_centers(path_A_transforms, path_B_transforms, transform_A, transform_B_to_global)

def main():
    parser = argparse.ArgumentParser(description="Align NeRF blocks via ICP and store transforms.")
    parser.add_argument("ref_block", help="Path to reference block's .ply file")
    parser.add_argument("target_block", help="Path to target block's .ply file (to be aligned)")
    parser.add_argument("--init_transform", default=None, help="Path to initial transform (npy) file to use as ICP starting guess.")
    parser.add_argument("--db", default="metadata.sqlite", help="Path to SQLite DB to store global transforms and AABB")
    parser.add_argument("--threshold", type=float, default=0.2, help="ICP distance threshold")
    parser.add_argument("--viewer", action="store_true", help="Open viewer to visualize the alignment")
    args = parser.parse_args()

    icp_align(args.ref_block, args.target_block, args.init_transform, args.db, args.threshold, args.viewer)

if __name__ == "__main__":
    main()
