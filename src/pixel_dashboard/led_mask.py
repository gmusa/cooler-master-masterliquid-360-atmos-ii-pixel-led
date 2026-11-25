"""Boolean LED topology derived from cmpixel/layout.json (cm-pixel 0.1.0).

Copyright (c) 2026 Feiko, MIT license; see LICENSE-cmpixel.txt in this package.
Rows encode contiguous nonzero LED positions from the indexed 32×32 layout.
"""

ROW_BOUNDS = (
    (0, 0), (0, 0), (14, 18), (13, 19), (11, 21), (9, 23), (7, 25), (6, 26),
    (4, 28), *((3, 29),) * 14, (4, 28), (6, 26), (7, 25), (9, 23),
    (11, 21), (13, 19), (14, 18), (0, 0), (0, 0),
)
assert len(ROW_BOUNDS) == 32
