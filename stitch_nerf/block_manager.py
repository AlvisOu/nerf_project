import os
import glob
import sqlite3
from dataclasses import dataclass
from collections import defaultdict
from typing import List, Dict

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
            portals[block_b].append(Portal(xb, zb, block_a, xa, za, r_sq))
    
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

    def get_current_block_id(self):
        return self.snapshots[self.curr_idx][0]

    def get_current_snapshot_path(self):
        return self.snapshots[self.curr_idx][1]

    def check_switch(self, x, y, z):
        """
        Returns (new_snapshot, new_x, new_z) if a portal is triggered,
        or None otherwise.
        """
        block_id = self.get_current_block_id()
        for p in self.portals_by_block.get(block_id, ()):
            print(p)
            dx = x - p.cx
            dz = z - p.cz
            # If radius is smaller, teleport
            if dx*dx + dz*dz <= p.radius_sq:
                self.curr_idx = self.block_to_idx[p.dest_block]
                new_snapshot = self.get_current_snapshot_path()
                return new_snapshot, p.dest_x, p.dest_z
        return None
        



# class BlockManager:
#     def __init__(self, snapshots):
#         self.snapshots = snapshots
#         self.curr_idx = 0
#         self.portals_by_block = load_portals("metadata.sqlite") # load the portals

#     def check_switch(self, x, y, z):
#         if x > 5:
#             return snapshots[1]
#         return None
        