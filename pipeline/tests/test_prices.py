from pathlib import Path

import h3
import numpy as np
import pandas as pd
import pytest

from atlas.datasets.countries.gb import hm_land_registry
from atlas.datasets.countries.gb.addresses import address_key
from atlas.indicators import prices

ROW = (
    '"{{{id}}}","{price}","{date} 00:00","{postcode}","{type}","N","F","{paon}","{saon}",'
    '"{street}","","LONDON","CAMDEN","GREATER LONDON","{category}","A"'
)


def sale_row(
    n: int,
    price: int = 500000,
    date: str = "2026-06-01",
    postcode: str = "W1F 9AA",
    kind: str = "F",
    paon: str = "12",
    saon: str = "",
    street: str = "BROAD STREET",
    category: str = "A",
) -> str:
    return ROW.format(
        id=f"ID{n}", price=price, date=date, postcode=postcode, type=kind, paon=paon,
        saon=saon, street=street, category=category,
    )  # fmt: skip


def write_year(tmp_path: Path, year: int, rows: list[str]) -> Path:
    path = tmp_path / f"pp-{year}.csv"
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return path


class TestReadSales:
    def test_it_reads_the_standard_sales_of_the_last_months_of_the_data(self, tmp_path):
        path = write_year(
            tmp_path,
            2026,
            [
                sale_row(1, date="2026-06-01"),
                sale_row(2, date="2024-03-31"),  # more than 24 months before the latest
                sale_row(3, date="2024-11-30"),
                sale_row(4, category="B"),  # repossessions and the like are not standard sales
                sale_row(5, kind="O"),  # a type of property that is not a home
            ],
        )
        sales = hm_land_registry.read_sales([path], months=24)
        assert sorted(sales["price"]) == [500000, 500000]
        assert "O" not in set(sales["type"])

    def test_it_gives_the_postcode_and_the_address_parts(self, tmp_path):
        path = write_year(tmp_path, 2026, [sale_row(1, saon="FLAT 3", paon="PETTIFOR COURT, 101")])
        sale = hm_land_registry.read_sales([path], months=24).iloc[0]
        assert (sale["postcode"], sale["saon"], sale["paon"]) == (
            "W1F 9AA",
            "FLAT 3",
            "PETTIFOR COURT, 101",
        )
        assert sale["street"] == "BROAD STREET"

    def test_the_years_are_fetched_once_each(self, tmp_path, monkeypatch):
        asked = []
        monkeypatch.setattr(hm_land_registry, "download", lambda url, target: asked.append(url))
        paths = hm_land_registry.fetch(tmp_path, [2025, 2026])
        assert [p.name for p in paths] == ["pp-2025.csv", "pp-2026.csv"]
        assert all(u.endswith(p.name) for u, p in zip(asked, paths, strict=True))


def sales_frame(rows):
    return pd.DataFrame(rows, columns=["postcode", "saon", "paon", "street", "price"])


def certificates_frame(rows):
    """Certificates as the register keeps them: the fingerprint of the address and the area."""
    return pd.DataFrame(
        {
            "key": [address_key(postcode, address) for postcode, address, _ in rows],
            "floor_area": [area for _, _, area in rows],
        }
    )


class TestMatch:
    def test_a_sale_takes_the_floor_area_of_the_certificate_at_its_address(self):
        sales = sales_frame([("W1F 9AA", "FLAT 3", "PETTIFOR COURT, 101", "BRADGATE ROAD", 1)])
        certificates = certificates_frame(
            [("W1F 9AA", "Flat 3, Pettifor Court, 101 Bradgate Road", 55.0)]
        )
        assert prices.floor_areas(sales, certificates).tolist() == [55.0]

    def test_the_order_of_the_parts_and_punctuation_do_not_matter(self):
        sales = sales_frame([("W1F 9AA", "", "12", "BROAD STREET", 1)])
        certificates = certificates_frame([("w1f9aa", "12, BROAD ST.", 80.0)])
        assert prices.floor_areas(sales, certificates).tolist() == [80.0]

    def test_a_different_house_number_or_postcode_does_not_match(self):
        sales = sales_frame([("W1F 9AA", "", "12", "BROAD STREET", 1)] * 2)
        sales.loc[1, "postcode"] = "W1F 9AB"
        certificates = certificates_frame(
            [("W1F 9AA", "14 Broad Street", 70.0), ("W1F 9AA", "12 Broad Street", 80.0)]
        )
        areas = prices.floor_areas(sales, certificates)
        assert areas[0] == 80.0 and np.isnan(areas[1])

    def test_a_flat_does_not_take_the_area_of_another_flat_in_the_building(self):
        sales = sales_frame([("W1F 9AA", "FLAT 3", "12", "BROAD STREET", 1)])
        certificates = certificates_frame([("W1F 9AA", "Flat 4, 12 Broad Street", 40.0)])
        assert np.isnan(prices.floor_areas(sales, certificates)[0])

    def test_when_a_home_has_several_certificates_the_median_area_is_used(self):
        sales = sales_frame([("W1F 9AA", "", "12", "BROAD STREET", 1)])
        certificates = certificates_frame(
            [("W1F 9AA", "12 Broad Street", a) for a in (60.0, 62.0, 90.0)]
        )
        assert prices.floor_areas(sales, certificates).tolist() == [62.0]


class TestPricePerMetre:
    def test_a_price_over_an_area_that_is_a_home_size(self):
        price = pd.Series([300000.0, 300000.0, 300000.0, 300000.0])
        area = pd.Series([60.0, 5.0, 900.0, np.nan])
        result = prices.per_metre(price, area)
        assert result.iloc[0] == pytest.approx(5000.0)
        assert result.iloc[1:].isna().all()  # a floor area under 10 m² or over 500 m² is a typo


class TestPooledMedian:
    centre = h3.latlng_to_cell(51.5136, -0.1337, 9)

    def test_a_cell_takes_the_median_over_the_sales_of_itself_and_its_neighbours(self):
        ring = h3.grid_disk(self.centre, 1)
        sold = pd.DataFrame(
            {"cell": [c for c in ring for _ in range(3)], "per_metre": np.arange(21.0) * 100}
        )
        median = prices.pooled_median(sold, [self.centre], steps=2, minimum=20)
        assert median[self.centre] == pytest.approx(1000.0)

    def test_a_cell_with_too_few_sales_has_no_value(self):
        sold = pd.DataFrame({"cell": [self.centre] * 5, "per_metre": [1.0] * 5})
        assert np.isnan(prices.pooled_median(sold, [self.centre], steps=2, minimum=20)[self.centre])

    def test_sales_beyond_the_steps_do_not_count(self):
        far = h3.grid_disk(self.centre, 3)
        far = [c for c in far if h3.grid_distance(self.centre, c) == 3]
        sold = pd.DataFrame({"cell": [far[0]] * 30, "per_metre": [1.0] * 30})
        assert np.isnan(prices.pooled_median(sold, [self.centre], steps=2, minimum=20)[self.centre])
