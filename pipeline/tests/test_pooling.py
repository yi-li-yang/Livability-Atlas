import h3
import numpy as np
import pandas as pd

from atlas.indicators.pooling import pooled_median

CENTRE = h3.latlng_to_cell(51.5133, -0.0886, 9)


def test_a_cell_takes_the_median_of_its_own_homes_and_the_cells_within_the_steps():
    ring = h3.grid_ring(CENTRE, 1)[0]
    far = h3.grid_ring(CENTRE, 3)[0]
    homes = pd.DataFrame(
        {"cell": [CENTRE, CENTRE, ring, far], "efficiency": [50.0, 60.0, 90.0, 5.0]}
    )
    out = pooled_median(homes, "efficiency", [CENTRE], steps=1, minimum=1)
    assert out[CENTRE] == 60.0  # 50, 60 and 90: the far home is out of reach


def test_a_cell_with_too_few_homes_around_it_has_no_value():
    homes = pd.DataFrame({"cell": [CENTRE] * 4, "efficiency": [50.0, 60.0, 70.0, 80.0]})
    assert np.isnan(pooled_median(homes, "efficiency", [CENTRE], steps=1, minimum=5)[CENTRE])
    assert pooled_median(homes, "efficiency", [CENTRE], steps=1, minimum=4)[CENTRE] == 65.0


def test_a_missing_value_is_not_counted():
    homes = pd.DataFrame({"cell": [CENTRE] * 3, "efficiency": [50.0, np.nan, 70.0]})
    assert np.isnan(pooled_median(homes, "efficiency", [CENTRE], steps=0, minimum=3)[CENTRE])
    assert pooled_median(homes, "efficiency", [CENTRE], steps=0, minimum=2)[CENTRE] == 60.0
