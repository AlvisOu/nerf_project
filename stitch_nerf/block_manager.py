class BlockManager:
    def __init__(self, snapshots):
        self.snapshots = snapshots
        self.curr_snapshot_idx = 0

    def check_switch(self, x, y, z):
        if x > 5:
            return self.snapshots[1]
        return False
