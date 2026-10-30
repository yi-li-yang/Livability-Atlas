import h3
import pandas as pd
from pyproj import Transformer

from atlas.catalogue.load import load_catalogue
from atlas.datasets.countries.gb import ofsted_childcare
from atlas.families import Context, discover
from atlas.families import nurseries as family
from atlas.paths import CATALOGUE_DIR

TO_BNG = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)
CENTRE = h3.latlng_to_cell(51.5133, -0.0886, 9)

HEADER = (
    "Provider URN,Provider Type,Provider Subtype,Provider Name,Provider Postcode,Places,"
    "Most Recent Full: Overall Effectiveness"
)


def write(tmp_path, rows: list[str]):
    path = tmp_path / "childcare.csv"
    text = "Latest inspections of all registered providers as at 31 December 2025,,,,,\n"
    text += "This worksheet contains one table.,,,,,\n" + HEADER + "\n" + "\n".join(rows) + "\n"
    path.write_text(text, encoding="latin-1")
    return path


def test_the_nurseries_are_day_care_on_non_domestic_premises_with_a_postcode(tmp_path):
    path = write(
        tmp_path,
        [
            "1,Childcare on non-domestic premises,Full day care,Zoë Day Nursery,N1 1AA,40,2",
            "2,Childcare on non-domestic premises,Sessional day care,Pre-school,N1 1AB,20,1",
            "3,Childcare on non-domestic premises,Out-of-school day care,Club,N1 1AC,30,2",
            "4,Childminder,,REDACTED,REDACTED,6,2",
            "5,Childcare on non-domestic premises,Full day care,Nursery,REDACTED,40,2",
            "6,Home childcarer,Home childcarer,x,N1 1AD,0,",
        ],
    )
    found = ofsted_childcare.read_nurseries(path)
    assert list(found["Postcode"]) == ["N1 1AA", "N1 1AB"]


def test_a_file_with_an_accented_letter_is_read(tmp_path):
    path = write(
        tmp_path, ["1,Childcare on non-domestic premises,Full day care,Zoë Day,N1 1AA,40,2"]
    )
    assert len(ofsted_childcare.read_nurseries(path)) == 1


def test_the_file_is_fetched_once_to_the_raw_folder(tmp_path, monkeypatch):
    asked = []
    monkeypatch.setattr(ofsted_childcare, "download", lambda url, target: asked.append(target))
    path = ofsted_childcare.fetch(tmp_path)
    assert path == tmp_path / "raw" / "ofsted-childcare" / "most-recent-inspections.csv"
    assert asked == [path]


def test_each_cell_gets_the_walk_to_the_nearest_nursery(tmp_path, monkeypatch):
    region = load_catalogue(CATALOGUE_DIR).regions["london"]
    x, y = TO_BNG.transform(*h3.cell_to_latlng(CENTRE)[::-1])
    postcodes = pd.DataFrame({"Easting": [x], "Northing": [y]}, index=["N11AA"])

    class Network:
        def minutes_to_nearest(self, places, origins):
            self.places = places
            return [4.5] * len(origins)

    network = Network()
    ctx = Context("london", region, [CENTRE], tmp_path, postcodes, network)  # type: ignore[arg-type]
    monkeypatch.setattr(ofsted_childcare, "fetch", lambda data_dir: tmp_path / "x.csv")
    monkeypatch.setattr(
        ofsted_childcare,
        "read_nurseries",
        lambda path: pd.DataFrame({"Postcode": ["N1 1AA", "ZZ9 9ZZ"]}),  # the second is unknown
    )
    assert family.columns(ctx) == {"nurseries": [4.5]}
    assert len(network.places) == 1  # type: ignore[attr-defined]


def test_the_family_is_found_and_its_indicator_is_in_the_catalogue():
    assert "nurseries" in {f.name for f in discover()}
    ids = {n.id for n in _leaves(load_catalogue(CATALOGUE_DIR).factors.factors)}
    assert "nurseries" in ids


def _leaves(nodes):
    for node in nodes:
        if node.children is None:
            yield node
        else:
            yield from _leaves(node.children)
