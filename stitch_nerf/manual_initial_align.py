import open3d as o3d
import numpy as np
import json
import argparse
import copy
import os

# ====== Utility to load camera centers from transforms.json ======

def load_camera_centers(transforms_path: str) -> np.ndarray:
    with open(transforms_path) as f:
        data = json.load(f)

    points = []
    for frame in data["frames"]:
        T = np.array(frame["transform_matrix"])
        camera_center = T[:3, 3]
        points.append(camera_center)
    return np.array(points)

# ====== Manual Alignment Script ======

def manual_align(ref_path, target_path, save_path=None):

    if save_path is None:
        block_dir = os.path.dirname(target_path)
        save_path = os.path.join(block_dir, "initial_transform.npy")

    # Load camera centers
    points_A = load_camera_centers(ref_path)
    points_B = load_camera_centers(target_path)

    # Convert to Open3D point clouds
    pcd_A = o3d.geometry.PointCloud()
    pcd_A.points = o3d.utility.Vector3dVector(points_A)
    pcd_A.paint_uniform_color([1, 0, 0])  # Red color for Block A
    points_A = np.asarray(pcd_A.points)
    print("X range:", np.ptp(points_A[:, 0]))
    print("Y range:", np.ptp(points_A[:, 1]))
    print("Z range:", np.ptp(points_A[:, 2]))

    pcd_B = o3d.geometry.PointCloud()
    pcd_B.points = o3d.utility.Vector3dVector(points_B)
    pcd_B.paint_uniform_color([0, 1, 0])  # Green color for Block B
    points_B = np.asarray(pcd_B.points)
    print("X range:", np.ptp(points_B[:, 0]))
    print("Y range:", np.ptp(points_B[:, 1]))
    print("Z range:", np.ptp(points_B[:, 2]))

    # Create a copy to apply transformations interactively
    pcd_B_copy = copy.deepcopy(pcd_B)

    # Start with identity transform
    T = np.eye(4)

    print("[Instructions]")
    print("W/S: move forward/backward")
    print("A/D: move left/right")
    print("R/F: move up/down")
    print("Q/E: rotate yaw left/right")
    print("T/G: rotate pitch up/down")
    print("Z/X: rotate roll ccw/cw")
    print("Space: save current transform and exit")
    print("ESC: exit without saving")

    vis = o3d.visualization.VisualizerWithKeyCallback()
    vis.create_window()
    vis.add_geometry(pcd_A)
    vis.add_geometry(pcd_B_copy)

    axis = o3d.geometry.TriangleMesh.create_coordinate_frame(size=1.0, origin=[0, 0, 0])
    vis.add_geometry(axis)

    move_delta = 0.1  # meters
    rotate_delta = np.radians(5)  # degrees

    def update_geometry():
        pcd_B_copy.points = o3d.utility.Vector3dVector((T[:3, :3] @ points_B.T + T[:3, [3]]).T)
        vis.update_geometry(pcd_B_copy)

    def move(dx=0, dy=0, dz=0):
        nonlocal T
        T_translate = np.eye(4)
        T_translate[:3, 3] = np.array([dx, dy, dz])
        T = T_translate @ T
        update_geometry()

    def rotate_axis(axis: str, angle: float):
        nonlocal T
        R = np.eye(4)
        c, s = np.cos(angle), np.sin(angle)

        if axis == 'x':
            R[:3, :3] = [[1, 0, 0],
                        [0, c, -s],
                        [0, s, c]]
        elif axis == 'y':
            R[:3, :3] = [[c, 0, s],
                        [0, 1, 0],
                        [-s, 0, c]]
        elif axis == 'z':
            R[:3, :3] = [[c, -s, 0],
                        [s,  c, 0],
                        [0,  0, 1]]

        T = R @ T
        update_geometry()

    # Key callbacks
    vis.register_key_callback(ord("W"), lambda vis: move(0, 0, -move_delta))
    vis.register_key_callback(ord("S"), lambda vis: move(0, 0, move_delta))
    vis.register_key_callback(ord("A"), lambda vis: move(-move_delta, 0, 0))
    vis.register_key_callback(ord("D"), lambda vis: move(move_delta, 0, 0))
    vis.register_key_callback(ord("R"), lambda vis: move(0, move_delta, 0))
    vis.register_key_callback(ord("F"), lambda vis: move(0, -move_delta, 0))
    vis.register_key_callback(ord("Q"), lambda vis: rotate_axis('y',  rotate_delta))  # Yaw left
    vis.register_key_callback(ord("E"), lambda vis: rotate_axis('y', -rotate_delta))  # Yaw right
    vis.register_key_callback(ord("T"), lambda vis: rotate_axis('x',  rotate_delta))  # Pitch up
    vis.register_key_callback(ord("G"), lambda vis: rotate_axis('x', -rotate_delta))  # Pitch down
    vis.register_key_callback(ord("Z"), lambda vis: rotate_axis('z',  rotate_delta))  # Roll ccw
    vis.register_key_callback(ord("X"), lambda vis: rotate_axis('z', -rotate_delta))  # Roll cw

    def save_transform(vis):
        np.save(save_path, T)
        print(f"Saved transform to {save_path}")
        vis.destroy_window()

    def exit_without_saving(vis):
        print("Exiting without saving.")
        vis.destroy_window()

    vis.register_key_callback(ord(" "), save_transform)  # Spacebar
    vis.register_key_callback(256, exit_without_saving)   # ESC

    update_geometry()
    vis.run()

# ====== Command Line Interface ======

def main():
    parser = argparse.ArgumentParser(description="Manual alignment tool for NeRF blocks using camera centers.")
    parser.add_argument("ref_block", help="Path to reference block's transforms.json")
    parser.add_argument("target_block", help="Path to target block's transforms.json")
    parser.add_argument("--out", default=None, help="Path to save the initial transform (npy file)")
    args = parser.parse_args()

    manual_align(args.ref_block, args.target_block, args.out)

if __name__ == "__main__":
    main()
