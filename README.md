# NeRF virtual tour project

## Alvis's notes
manual_initial_align.py allows us to first align blocks visually using camera
centers. It generates an .npy file that align_blocks.py takes to perform a
second pass using ICP to polish the transformation and stores the matrix,
flattened into 16 cells (it's 4 by 4), in transforms.sqlite.

populate_table.py then takes the transformation matrix for each block from
transforms.sqlite, as well as the boundary and neighbor information from
boundaries.txt and populate a blocks.sqlite table, which the block_manager.py
will use.

The table schema of blocks is:
```
CREATE TABLE blocks (
            block_name TEXT PRIMARY KEY,
            t00 REAL, t01 REAL, t02 REAL, t03 REAL,
            t10 REAL, t11 REAL, t12 REAL, t13 REAL,
            t20 REAL, t21 REAL, t22 REAL, t23 REAL,
            t30 REAL, t31 REAL, t32 REAL, t33 REAL,
            left_boundary REAL,
            left_neighbor TEXT,
            right_boundary REAL,
            right_neighbor TEXT,
            front_boundary REAL,
            front_neighbor TEXT,
            back_boundary REAL,
            back_neighbor TEXT
        )
```

Specifically for the block_manager.py, what happens is:
- It gets the current local coordinates from the renderer
- Check if they stepped out of any of the left, right, front, back boundaries
by reading in values from the blocks table: left_boundary, right_boundary,
front_boundary, back_boundary. 
- If they have, compute where the user is in global coordinates using the 
transformation matrix from the blocks table.
- Then, get from the sqlite table what the next scene should be based on which
boundary was crossed.
- Compute the local coordinates within the next scene based on the global
coordinates by taking the inverse of the transformation matrix of the next scene
from the blocks table.
- Give renderer the next scene and the local coordinates within the next scene.

