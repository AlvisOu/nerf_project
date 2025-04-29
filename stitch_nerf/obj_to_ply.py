import open3d as o3d
import argparse

def main(input_path: str):

    # Load and sample
    mesh = o3d.io.read_triangle_mesh(input_path)
    mesh.compute_vertex_normals()
    pcd = mesh.sample_points_uniformly(number_of_points=100000)
    print("Loaded and sampled mesh")

    output_path = input_path.replace(".obj", ".ply")
    # Save as .ply
    o3d.io.write_point_cloud(output_path, pcd)
    print(f"Saved {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert .obj to .ply")
    parser.add_argument("input", help="Path to input .obj file")
    args = parser.parse_args()
    main(args.input)
