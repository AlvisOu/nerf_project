import open3d as o3d
import numpy as np
import json
import os
import sqlite3
import argparse

def load_camera_centers(transforms_path: str) -> np.ndarray:
    with open(transforms_path) as f:
        data = json.load(f)

    points = []
    for frame in data["frames"]:
        T = np.array(frame["transform_matrix"])
        camera_center = T[:3, 3]
        points.append(camera_center)
    return np.array(points)

def points_to_pcd(points: np.ndarray, color=[1, 0, 0]) -> o3d.geometry.PointCloud:
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(points)
    colors = np.tile(np.array(color), (points.shape[0], 1))
    pcd.colors = o3d.utility.Vector3dVector(colors)
    return pcd

def apply_global_transform(transforms_path: str, output_path: str, transform: np.ndarray) -> None:
    with open(transforms_path) as f:
        data = json.load(f)

    for frame in data["frames"]:
        T = np.array(frame["transform_matrix"])
        T_new = transform @ T
        frame["transform_matrix"] = T_new.tolist()

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(data, f, indent=4)

def compute_global_aabb(transforms_path: str, transform: np.ndarray):
    with open(transforms_path) as f:
        data = json.load(f)

    points = []
    for frame in data["frames"]:
        T = np.array(frame["transform_matrix"])
        T_global = transform @ T
        points.append(T_global[:3, 3])

    points = np.array(points)
    aabb_min = np.min(points, axis=0)
    aabb_max = np.max(points, axis=0)
    return aabb_min.tolist(), aabb_max.tolist()

def store_transform_sqlite(db_path: str, block_name: str, transform: np.ndarray, aabb_min, aabb_max):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS block_transforms (
            block_name TEXT PRIMARY KEY,
            t00 REAL, t01 REAL, t02 REAL, t03 REAL,
            t10 REAL, t11 REAL, t12 REAL, t13 REAL,
            t20 REAL, t21 REAL, t22 REAL, t23 REAL,
            t30 REAL, t31 REAL, t32 REAL, t33 REAL,
            aabb_min_x REAL, aabb_min_y REAL, aabb_min_z REAL,
            aabb_max_x REAL, aabb_max_y REAL, aabb_max_z REAL
        )
    """)

    flat = transform.flatten().tolist()
    values = [block_name] + flat + aabb_min + aabb_max
    placeholders = ', '.join(['?'] * len(values))
    columns = ', '.join(
        ['block_name'] + [f"t{i}{j}" for i in range(4) for j in range(4)] +
        ["aabb_min_x", "aabb_min_y", "aabb_min_z", "aabb_max_x", "aabb_max_y", "aabb_max_z"]
    )

    c.execute(f"""
        INSERT INTO block_transforms ({columns})
        VALUES ({placeholders})
        ON CONFLICT(block_name) DO UPDATE SET
        {', '.join([f"{col} = excluded.{col}" for col in columns if col != 'block_name'])}
    """, values)

    conn.commit()
    conn.close()

def icp_align(path_A: str, path_B: str, out_B_aligned: str, store_db_path: str = None, threshold: float = 0.5, viewer: bool = False):
    points_A = load_camera_centers(path_A)
    points_B = load_camera_centers(path_B)

    pcd_A = points_to_pcd(points_A, color=[1, 0, 0])
    pcd_B = points_to_pcd(points_B, color=[0, 1, 0])

    print("Initial alignment (red = A, green = B)")
    if viewer:
        o3d.visualization.draw_geometries([pcd_A, pcd_B])

    print("Running ICP...")
    result = o3d.pipelines.registration.registration_icp(
        pcd_B, pcd_A, threshold,
        np.eye(4),
        o3d.pipelines.registration.TransformationEstimationPointToPoint()
    )
    print("Transformation matrix B → A:")
    print(result.transformation)

    apply_global_transform(path_B, out_B_aligned, result.transformation)

    if store_db_path:
        block_name = os.path.basename(os.path.dirname(path_B))
        aabb_min, aabb_max = compute_global_aabb(path_B, result.transformation)
        store_transform_sqlite(store_db_path, block_name, result.transformation, aabb_min, aabb_max)

    points_B_aligned = (result.transformation @ np.hstack((points_B, np.ones((points_B.shape[0], 1)))).T).T[:, :3]
    pcd_B_aligned = points_to_pcd(points_B_aligned, color=[0, 1, 1])

    print("Aligned result (red = A, cyan = B-aligned)")
    if viewer:
        o3d.visualization.draw_geometries([pcd_A, pcd_B_aligned])

def main():
    parser = argparse.ArgumentParser(description="Align NeRF blocks via ICP and store transforms.")
    parser.add_argument("ref_block", help="Path to reference block's transforms.json")
    parser.add_argument("target_block", help="Path to target block's transforms.json (to be aligned)")
    parser.add_argument("--out", default="aligned/transforms.json", help="Output path for aligned transforms.json")
    parser.add_argument("--db", default="metadata.sqlite", help="Path to SQLite DB to store global transforms and AABB")
    parser.add_argument("--threshold", type=float, default=0.5, help="ICP distance threshold")
    parser.add_argument("--viewer", action="store_true", help="Open viewer to visualize the alignment")
    args = parser.parse_args()

    icp_align(args.ref_block, args.target_block, args.out, args.db, args.threshold, args.viewer)

if __name__ == "__main__":
    main()
