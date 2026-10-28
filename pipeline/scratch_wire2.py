import pathlib


def edit(path, old, new):
    p = pathlib.Path(path)
    s = p.read_text(encoding="utf-8")
    assert old in s, (path, old[:60])
    p.write_text(s.replace(old, new, 1), encoding="utf-8")


b = "src/atlas/build.py"
edit(b, "    ea_flood_risk,\n    naptan,", "    ea_flood_risk,\n    gias,\n    naptan,")
edit(
    b,
    "from atlas.indicators import crime, flood, transport",
    "from atlas.indicators import crime, education, flood, transport",
)
edit(
    b,
    '    return {"station-proximity": [None if pd.isna(m) else float(m) for m in minutes]}',
    """    columns: dict[str, Sequence[Any]] = {
        "station-proximity": [None if pd.isna(m) else float(m) for m in minutes]
    }
    schools = gias.read_schools(gias.fetch(data_dir))
    for indicator, walk in education.school_minutes(network, schools, cells).items():
        columns[indicator] = [None if pd.isna(m) else float(m) for m in walk]
    return columns""",
)
edit(
    b,
    "the minutes to the nearest station.",
    "the minutes to the nearest station, primary school and secondary school.",
)

t = "tests/test_build.py"
edit(
    t,
    '    monkeypatch.setattr(build_module.naptan, "fetch", lambda data_dir: stations)\n',
    '    monkeypatch.setattr(build_module.naptan, "fetch", lambda data_dir: stations)\n'
    "    schools = synthetic_schools(tmp_path)\n"
    '    monkeypatch.setattr(build_module.gias, "fetch", lambda data_dir: schools)\n',
)
edit(
    t,
    "def use_synthetic_data(monkeypatch, tmp_path):",
    '''def synthetic_schools(tmp_path: Path) -> Path:
    """A primary school in the west of AREA and a secondary school in the east, in the register's
    columns and in metres of British National Grid."""
    west = TO_BNG.transform(-0.1495, 51.5120)
    east = TO_BNG.transform(-0.1255, 51.5120)
    rows = [
        "URN,EstablishmentStatus (name),EstablishmentTypeGroup (name),TypeOfEstablishment (name),"
        "PhaseOfEducation (name),Easting,Northing",
        f"1,Open,Academies,Academy converter,Primary,{west[0]:.0f},{west[1]:.0f}",
        f"2,Open,Academies,Academy converter,Secondary,{east[0]:.0f},{east[1]:.0f}",
    ]
    path = tmp_path / "edubasealldata20261028.csv"
    path.write_text("\n".join(rows) + "\n", encoding="cp1252")
    return path


def use_synthetic_data(monkeypatch, tmp_path):''',
)
with open(t, "a", encoding="utf-8") as f:
    f.write(
        """

def test_the_bundle_holds_the_walk_to_the_nearest_primary_and_secondary_school(
    monkeypatch, tmp_path
):
    use_synthetic_data(monkeypatch, tmp_path)
    bundle = build_region("london", data_dir=tmp_path / "data")
    table = pq.read_table(bundle / "cells.parquet").to_pandas()
    lng = pd.Series([h3.cell_to_latlng(c)[1] for c in table["cell"]], index=table.index)
    west, east = table[lng < -0.145], table[lng > -0.130]
    # The primary school is in the west and the secondary school in the east.
    assert west["primary_schools"].median() < east["primary_schools"].median()
    assert east["secondary_schools"].median() < west["secondary_schools"].median()
    assert table[["primary_schools", "secondary_schools"]].notna().all().all()
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    ids = {i["id"] for i in manifest["indicators"]}
    assert {"primary-schools", "secondary-schools"} <= ids
"""
    )
