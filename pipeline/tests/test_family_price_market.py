from typing import cast

import h3
import numpy as np
import pandas as pd
import pytest
from pyproj import Transformer

from atlas.catalogue.load import load_catalogue
from atlas.datasets.countries.gb import epc, hm_land_registry
from atlas.datasets.countries.gb.addresses import address_key
from atlas.families import Context, discover
from atlas.families import price_market as family
from atlas.paths import CATALOGUE_DIR

TO_BNG = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)
CENTRE = h3.latlng_to_cell(51.5133, -0.0886, 9)


def day(text: str) -> pd.Timestamp:
    return cast(pd.Timestamp, pd.Timestamp(text))


ENDING = day("2026-04-30")
ROW = (
    '"{{ID{n}}}","500000","{date} 00:00","W1F 9AA","{kind}","N","F","12","","BROAD STREET",'
    '"","LONDON","CAMDEN","GREATER LONDON","{category}","A"'
)


def sale_row(n: int, date: str = "2026-04-01", kind: str = "F", category: str = "A") -> str:
    return ROW.format(n=n, date=date, kind=kind, category=category)


def write_year(tmp_path, year: int, rows: list[str]):
    path = tmp_path / f"pp-{year}.csv"
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return path


class TestTheWindowsOfSales:
    def test_the_latest_date_of_the_files_is_the_end_of_the_current_window(self, tmp_path):
        a = write_year(tmp_path, 2025, [sale_row(1, date="2025-12-31")])
        b = write_year(
            tmp_path, 2026, [sale_row(2, date="2026-04-17"), sale_row(3, date="2026-02-01")]
        )
        assert hm_land_registry.latest_date([a, b]) == day("2026-04-17")

    def test_a_window_is_the_months_before_its_end_and_no_sale_after_it(self, tmp_path):
        path = write_year(
            tmp_path,
            2021,
            [
                sale_row(1, date="2021-04-30"),  # the last day counts
                sale_row(2, date="2021-05-01"),  # after the end
                sale_row(3, date="2019-05-01"),  # inside the 24 months
                sale_row(4, date="2019-04-30"),  # 24 months before the end: out
            ],
        )
        sales = hm_land_registry.read_window([path], day("2021-04-30"), months=24)
        assert sorted(sales["date"].dt.strftime("%Y-%m-%d")) == ["2019-05-01", "2021-04-30"]

    def test_a_window_leaves_out_what_is_not_a_standard_sale_of_a_home(self, tmp_path):
        path = write_year(
            tmp_path, 2026, [sale_row(1), sale_row(2, category="B"), sale_row(3, kind="O")]
        )
        assert len(hm_land_registry.read_window([path], ENDING, months=24)) == 1

    def test_the_years_of_a_window_are_those_it_touches(self):
        assert hm_land_registry.years_of(day("2021-04-30"), 24) == [2019, 2020, 2021]
        assert hm_land_registry.years_of(day("2026-04-17"), 24) == [2024, 2025, 2026]


class TestTheChange:
    def test_it_is_the_percent_change_and_missing_where_either_end_is(self):
        now = pd.Series({"a": 15000.0, "b": 8000.0, "c": np.nan, "d": 9000.0})
        then = pd.Series({"a": 10000.0, "b": 10000.0, "c": 5000.0, "d": np.nan})
        change = family.change(now, then)
        assert change["a"] == pytest.approx(50.0) and change["b"] == pytest.approx(-20.0)
        assert np.isnan(change["c"]) and np.isnan(change["d"])


def context(tmp_path, cells) -> Context:
    region = load_catalogue(CATALOGUE_DIR).regions["london"]
    x, y = TO_BNG.transform(*h3.cell_to_latlng(CENTRE)[::-1])
    postcodes = pd.DataFrame({"Easting": [x], "Northing": [y]}, index=["EC3V3ND"])
    ctx = Context("london", region, cells, tmp_path, postcodes, network=None)  # type: ignore[arg-type]
    ctx.__dict__["residents"] = pd.Series(1000.0, index=cells)  # stands in for the cached property
    return ctx


def sales(n: int, price: float) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "price": [price] * n,
            "postcode": ["EC3V 3ND"] * n,
            "saon": [""] * n,
            "paon": [str(i + 1) for i in range(n)],
            "street": ["LEADENHALL STREET"] * n,
            "date": [ENDING] * n,
            "type": ["F"] * n,
        }
    )


def certificates(n: int) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "key": [address_key("EC3V 3ND", f"{i + 1} Leadenhall Street") for i in range(n)],
            "floor_area": [50.0] * n,
        }
    )


@pytest.fixture
def two_windows(monkeypatch):
    """25 sales at 500,000 now and 25 at 400,000 five years before, all of 50 m² homes."""
    asked = []

    def fake_fetch(data_dir, years):
        asked.append(list(years))
        return [data_dir / f"pp-{y}.csv" for y in years]

    def fake_window(paths, ending, months=24):
        return sales(25, 500000.0 if ending == ENDING else 400000.0)

    monkeypatch.setattr(hm_land_registry, "fetch", fake_fetch)
    monkeypatch.setattr(hm_land_registry, "latest_date", lambda paths: ENDING)
    monkeypatch.setattr(hm_land_registry, "read_window", fake_window)
    monkeypatch.setattr(
        epc, "certificates", lambda data_dir, region_id, postcodes: certificates(25)
    )
    return asked


def test_the_price_per_metre_five_years_before_is_the_base_of_the_trend(tmp_path, two_windows):
    out = family.columns(context(tmp_path, [CENTRE]))
    assert out["price-trend"][0] == pytest.approx(25.0)  # 10,000 against 8,000 a m²
    assert two_windows == [hm_land_registry.YEARS, [2019, 2020, 2021]]


def test_the_sales_of_a_year_are_counted_against_the_residents(tmp_path, two_windows):
    out = family.columns(context(tmp_path, [CENTRE]))
    # 25 sales in 24 months is 12.5 a year, over 1,000 residents plus the rate's floor of 3,000
    expected = 1000 * (12.5 + family.crime.FLOOR * (12.5 / 1000)) / (1000 + family.crime.FLOOR)
    assert out["sales-volume"][0] == pytest.approx(expected)


def test_a_cell_with_too_few_sales_around_it_has_no_trend(tmp_path, monkeypatch, two_windows):
    monkeypatch.setattr(hm_land_registry, "read_window", lambda *a, **k: sales(5, 500000.0))
    assert family.columns(context(tmp_path, [CENTRE]))["price-trend"][0] is None


def test_a_sale_in_a_postcode_outside_the_region_is_left_out(tmp_path, monkeypatch, two_windows):
    far = sales(25, 500000.0).assign(postcode="E1 6AN")
    monkeypatch.setattr(hm_land_registry, "read_window", lambda *a, **k: far)
    out = family.columns(context(tmp_path, [CENTRE]))
    assert out["price-trend"][0] is None
    assert out["sales-volume"][0] == pytest.approx(0.0)


def test_the_family_is_found_and_its_indicators_are_in_the_catalogue():
    assert "price_market" in {f.name for f in discover()}
    ids = {n.id for n in _leaves(load_catalogue(CATALOGUE_DIR).factors.factors)}
    assert {"price-trend", "sales-volume"} <= ids


def test_a_commercial_build_leaves_out_what_uses_the_sales_and_their_addresses():
    assert family.FAMILY.built_from == {
        "price-trend": ("hm-land-registry-price-paid", "epc-domestic"),
        "sales-volume": ("hm-land-registry-price-paid",),
    }


def _leaves(nodes):
    for node in nodes:
        if node.children is None:
            yield node
        else:
            yield from _leaves(node.children)
