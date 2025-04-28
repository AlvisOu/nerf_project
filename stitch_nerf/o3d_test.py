import open3d as o3d
import numpy as np
import os
os.environ["OPEN3D_CPU_ONLY"] = "true"

pcd = o3d.geometry.PointCloud()
pcd.points = o3d.utility.Vector3dVector(np.random.rand(100, 3))
o3d.visualization.draw_geometries([pcd])

# Generate point cloud A
points_A = np.random.rand(100, 3)
pcd_A = o3d.geometry.PointCloud()
pcd_A.points = o3d.utility.Vector3dVector(points_A)

# Generate point cloud B (translated version of A)
points_B = points_A + np.array([0.5, 0.2, -0.1])
pcd_B = o3d.geometry.PointCloud()
pcd_B.points = o3d.utility.Vector3dVector(points_B)

print("Running ICP...")
result = o3d.pipelines.registration.registration_icp(
    pcd_B, pcd_A, 1.0,  # threshold = 1.0
    np.eye(4),
    o3d.pipelines.registration.TransformationEstimationPointToPoint()
)
print("Done.")

print("ICP Transformation:")
print(result.transformation)
print("Fitness:", result.fitness)
print("Inlier RMSE:", result.inlier_rmse)
