import os
import glob
import sqlite3
import numpy as np
from dataclasses import dataclass
from collections import defaultdict
from typing import List, Dict

def load_block_transforms(db_path: str):
    """
    Returns {block: T} and {block: T‑inv} where T is a 4×4 world‑from‑local matrix.
    """
    f32 = np.float32
    to_mat = lambda row: np.array(row, dtype=f32).reshape(4, 4)
    transforms, inv_transforms = {}, {}

    with sqlite3.connect(db_path) as conn:
        cur = conn.execute("""
            SELECT block_name,
                   t00, t01, t02, t03,
                   t10, t11, t12, t13,
                   t20, t21, t22, t23,
                   t30, t31, t32, t33
            FROM block_transforms
        """)
        for row in cur.fetchall():
            name, *vals = row
            T = to_mat(vals)
            transforms[name] = T
            inv_transforms[name] = np.linalg.inv(T)

    return transforms, inv_transforms


@dataclass(frozen=True)
class Portal:
    """
        One directional portal entry: from (block_a, x_a, z_a) → (block_b, x_b, z_b)
    """
    cx: float
    cz: float
    dest_block: str
    dest_x: float
    dest_z: float
    radius_sq: float


def load_portals(db_path: str):
    """
    Reads the portals table and returns:
        {Source_BLOCK: [Portal, Portal, ...], ...}
    Both directions are stored
    """

    """
    str is block name, List[Portal] is list of portals from that block
    e.g.:
    portals = {
        "SceneA": [Portal(to SceneB), Portal(to SceneC)],
        "SceneB": [Portal(to SceneA)],
        "SceneC": [Portal(to SceneA)],
    }
    """
    portals: Dict[str, List[Portal]] = defaultdict(list)
    
    # Run query to collect data
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute("""
             SELECT block_a, local_x_a, local_z_a,
                   block_b, local_x_b, local_z_b,
                   radius
              FROM portals
        """)
        # Iterate over each portal and add it bidirectionally to portals
        for (block_a, xa, za, block_b, xb, zb, r) in cur.fetchall():
            r_sq = r * r
            portals[block_a].append(Portal(xa, za, block_b, xb, zb, r_sq))

    for block_name in portals:
        print(" -", block_name)
    return portals

class BlockManager:
    def __init__(self, snapshots, db_path):
        """
        snapshots: List of (block_id, path_to_msgpack)
        """
        self.snapshots = snapshots
        self.block_to_idx = {bid: i for i, (bid, _) in enumerate(snapshots)}
        self.curr_idx = 0
        self.portals_by_block = load_portals(db_path) # load the portals
        self.T, self.T_inv = load_block_transforms(db_path)

    def get_current_block_id(self):
        return self.snapshots[self.curr_idx][0]

    def get_current_snapshot_path(self):
        return self.snapshots[self.curr_idx][1]

    def check_switch(self, x, y, z, testbed):
        """
        Returns (new_snapshot, new_x, new_z) if a portal is triggered,
        or None otherwise.
        """
        block_id = self.get_current_block_id()
        for p in self.portals_by_block.get(block_id, ()):
            dx = x - p.cx
            dz = z - p.cz
            # If radius is smaller, teleport
            if dx*dx + dz*dz <= p.radius_sq:
                
                start_cam = np.eye(4, dtype=np.float32)
                start_cam[:3, :4] = testbed.camera_matrix # set identity 3x4 to cam matrix

                # 2. transform whole pose:   dest_local = T_dest_inv · T_src · cam
                dest_cam = self.T_inv[p.dest_block] @ self.T[block_id] @ start_cam
                dest_cam = dest_cam[:3, :4] # compress back to 3x4

                self.curr_idx = self.block_to_idx[p.dest_block]
                new_snapshot = self.get_current_snapshot_path()
                print("Curr block: " + str(block_id) + " Dest block: " + str(p.dest_block))
                return new_snapshot, dest_cam
        return None