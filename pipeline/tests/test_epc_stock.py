import zipfile

import numpy as np
import pytest

from atlas.datasets.countries.gb import epc

HEADER = (
    "certificate_number,address1,address2,address3,postcode,current_energy_efficiency,"
    "construction_age_band,tenure,property_type,lodgement_date,uprn"
)


def stock_zip(tmp_path, files: dict[str, list[str]]):
    path = tmp_path / "domestic-csv.zip"
    with zipfile.ZipFile(path, "w") as archive:
        for name, rows in files.items():
            archive.writestr(name, "\n".join([HEADER, *rows]) + "\n")
        archive.writestr("recommendations-2024.csv", "certificate_number,improvement_item\n1,2\n")
    return path


def test_each_home_is_read_once_from_its_latest_certificate(tmp_path):
    path = stock_zip(
        tmp_path,
        {
            "certificates-2015.csv": [
                "A,Flat 3,12 Broad Street,,W1F 9AA,45,England and Wales: 1900-1929,"
                "rented (private),Flat,2015-01-02,100",
            ],
            "certificates-2024.csv": [
                "B,Flat 3,12 Broad Street,,W1F 9AA,72,England and Wales: 1900-1929,"
                "rented (private),Flat,2024-03-04,100",
                "C,14 Broad Street,,,W1F 9AB,60,2014,owner-occupied,House,2024-05-06,",
            ],
        },
    )
    stock = epc.read_stock(path, {"W1F9AA", "W1F9AB"}).sort_values("postcode")
    assert list(stock["postcode"]) == ["W1F9AA", "W1F9AB"]
    assert list(stock["efficiency"]) == [72, 60]  # the newer certificate of the first home
    assert list(stock["built"]) == [1914.5, 2014.0]


def test_a_home_without_a_uprn_is_told_apart_by_its_address(tmp_path):
    path = stock_zip(
        tmp_path,
        {
            "certificates-2024.csv": [
                "A,1 Road,,,N1 1AA,50,2000,unknown,House,2024-01-01,",
                "B,2 Road,,,N1 1AA,70,2000,unknown,House,2024-01-01,",
                "C,2 Road,,,N1 1AA,80,2000,unknown,House,2024-06-01,",
            ]
        },
    )
    stock = epc.read_stock(path, {"N11AA"})
    assert sorted(stock["efficiency"]) == [50, 80]


def test_only_the_postcodes_asked_for_are_read(tmp_path):
    path = stock_zip(
        tmp_path,
        {
            "certificates-2024.csv": [
                "A,1 Road,,,N1 1AA,50,2000,unknown,House,2024-01-01,1",
                "B,1 Road,,,M1 1AA,70,2000,unknown,House,2024-01-01,2",
            ]
        },
    )
    assert list(epc.read_stock(path, {"N11AA"})["postcode"]) == ["N11AA"]


@pytest.mark.parametrize(
    ("text", "year"),
    [
        ("England and Wales: 1950-1966", 1958.0),
        ("England and Wales: before 1900", 1880.0),
        ("England and Wales: 2007 onwards", 2010.0),
        ("England and Wales: 2012-2021", 2016.5),
        ("2014", 2014.0),
        ("NO DATA!", np.nan),
        ("INVALID!", np.nan),
        (None, np.nan),
    ],
)
def test_a_construction_age_band_is_a_year(text, year):
    assert epc.built_year(text) == pytest.approx(year, nan_ok=True)


@pytest.mark.parametrize(
    ("text", "tenure"),
    [
        ("Owner-occupied", "owner"),
        ("owner-occupied", "owner"),
        ("Rented (social)", "social"),
        ("rented (private)", "private"),
        ("unknown", None),
        ("Unknown", None),
        (None, None),
    ],
)
def test_a_tenure_is_one_of_three(text, tenure):
    assert epc.tenure_of(text) == tenure


def test_the_stock_is_kept_by_the_checksum_and_read_once(tmp_path, monkeypatch):
    path = stock_zip(
        tmp_path,
        {"certificates-2024.csv": ["A,1 Road,,,N1 1AA,50,2000,unknown,House,2024-01-01,1"]},
    )
    path.with_name(path.name + ".sha256").write_text("abcdef0123456789\n", encoding="utf-8")
    monkeypatch.setattr(epc, "fetch", lambda data_dir: path)
    first = epc.stock(tmp_path, "london", {"N11AA"})
    monkeypatch.setattr(epc, "read_stock", lambda *a: pytest.fail("read again"))
    assert epc.stock(tmp_path, "london", {"N11AA"}).equals(first)
