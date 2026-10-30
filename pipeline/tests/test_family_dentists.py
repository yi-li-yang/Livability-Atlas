from atlas.datasets.countries.gb import nhs_ods
from atlas.families import discover


def test_the_dental_practices_are_the_active_ones_with_a_postcode(tmp_path):
    path = tmp_path / "egdpprac.csv"
    row = [""] * 26
    rows = []
    for code, postcode, status in (
        ("V1", "N1 1AA", "ACTIVE"),
        ("V2", "N1 1AB", "INACTIVE"),
        ("V3", "", "ACTIVE"),
    ):
        r = list(row)
        r[0], r[9], r[12] = code, postcode, status
        rows.append(r)
    import csv

    with path.open("w", encoding="utf-8", newline="") as file:
        csv.writer(file, quoting=csv.QUOTE_ALL).writerows(rows)
    sites = nhs_ods.read_dental_sites(path)
    assert list(sites["Postcode"]) == ["N1 1AA"]


def test_the_dental_register_is_fetched_once_beside_the_gp_registers(tmp_path, monkeypatch):
    asked = []
    monkeypatch.setattr(nhs_ods, "download", lambda url, target: asked.append((url, target)))
    path = nhs_ods.fetch_dental(tmp_path)
    assert path == tmp_path / "raw" / "ods" / "egdpprac.csv"
    assert asked[0][0].endswith("report=egdpprac")


def test_the_family_is_found():
    assert "dentists" in {f.name for f in discover()}
