import h3
import numpy as np
import pandas as pd
import pytest

from atlas.datasets.countries.gb import nhs_ae
from atlas.indicators import health
from atlas.spatial.grid import cell_centres_bng


def item(n: int, code: str, name: str, address: str, hours: str = "Open 24 hours", ages="all ages"):
    status = f"Open for {'people of all ages' if ages == 'all ages' else ages}"
    return f"""
    <li id="result_item_{n}" class="results__item">
      <p id="item_id_{n}" class="nhsuk-u-visually-hidden" aria-hidden="true">{code}</p>
      <p id="item_org_type_id_{n}" class="nhsuk-u-visually-hidden" aria-hidden="true">HOS</p>
      <h3 id="orgname_{n}" class="nhsuk-card__heading">
          {name}
      </h3>
      <p id="opening_hour_status_mesg_{n}" class="callout">{status}</p>
      <ul class="nhsuk-list nhsuk-u-margin-top-0" id="opening_times_list_{n}_0">
          <li class="nhsuk-u-margin-bottom-0">{hours}</li>
      </ul>
      <p id="address_{n}" class="nhsuk-list">
          {address}
      </p>
    </li>"""


PAGE = (
    "<html><ol>"
    + "".join(
        [
            item(0, "RJ122", "St Thomas&#x27;", "Westminster Bridge Road, London, SE1 7EH"),
            item(
                1, "RAL79", "University College London Hospital", "235 Euston Road, London, NW1 2BU"
            ),
            item(
                2,
                "RALWA",
                "Watford General Hospital",
                "60 Vicarage Road, Watford, WD18 0HB",
                "midnight to 2am",
            ),
            item(
                3,
                "RAJ32",
                "Mid Essex Hospital",
                "Court Road, Chelmsford, CM1 7ET",
                ages="anyone under 16 years",
            ),
            item(4, "XX999", "No Postcode Hospital", "Somewhere, Nowhere"),
        ]
    )
    + "</ol></html>"
)


class TestParse:
    def test_each_result_has_its_code_name_address_and_postcode(self):
        found = nhs_ae.parse_results(PAGE)
        assert [f["code"] for f in found] == ["RJ122", "RAL79", "RALWA", "RAJ32", "XX999"]
        first = found[0]
        assert first["name"] == "St Thomas'"  # the page's HTML escapes are undone
        assert first["postcode"] == "SE1 7EH" and first["hours"] == "Open 24 hours"
        assert found[4]["postcode"] == ""

    def test_a_page_with_no_results_has_none(self):
        assert nhs_ae.parse_results("<html>We cannot find your location</html>") == []


class TestFetch:
    def test_the_sites_found_from_every_seed_are_kept_once_each(self, tmp_path, monkeypatch):
        asked = []

        def fake_page(postcode):
            asked.append(postcode)
            return PAGE

        monkeypatch.setattr(nhs_ae, "_page", fake_page)
        monkeypatch.setattr(nhs_ae, "PAUSE", 0)
        path = nhs_ae.fetch(tmp_path, "london", ["SW1A 1AA", "E1 6AN"])
        assert asked == ["SW1A 1AA", "E1 6AN"]
        assert len(pd.read_csv(path)) == 5  # the same five from both seeds

    def test_it_is_fetched_once_per_region(self, tmp_path, monkeypatch):
        calls = []
        monkeypatch.setattr(nhs_ae, "_page", lambda postcode: calls.append(postcode) or PAGE)
        monkeypatch.setattr(nhs_ae, "PAUSE", 0)
        nhs_ae.fetch(tmp_path, "london", ["SW1A 1AA"])
        nhs_ae.fetch(tmp_path, "london", ["SW1A 1AA"])
        assert calls == ["SW1A 1AA"]


class TestReadSites:
    def test_only_departments_open_all_day_with_a_postcode_are_sites(self, tmp_path, monkeypatch):
        monkeypatch.setattr(nhs_ae, "_page", lambda postcode: PAGE)
        monkeypatch.setattr(nhs_ae, "PAUSE", 0)
        sites = nhs_ae.read_sites(nhs_ae.fetch(tmp_path, "london", ["SW1A 1AA"]))
        assert sites["code"].tolist() == ["RJ122", "RAL79", "RAJ32"]
        assert sites["Postcode"].tolist() == ["SE1 7EH", "NW1 2BU", "CM1 7ET"]


class TestDistance:
    cell = h3.latlng_to_cell(51.5136, -0.1337, 9)

    def test_it_is_the_straight_line_to_the_nearest_site_in_kilometres(self):
        x, y = cell_centres_bng([self.cell])[0]
        sites = np.array([[x + 3000, y + 4000], [x + 20000, y]])  # 5 km and 20 km away
        km = health.ae_distance(sites, [self.cell])
        assert km[self.cell] == pytest.approx(5.0)

    def test_the_sites_are_found_from_their_postcodes_and_one_without_a_place_is_left_out(self):
        sites = pd.DataFrame({"Postcode": ["SE1 7EH", "ZZ9 9ZZ"]})
        postcodes = pd.DataFrame({"Easting": [531000], "Northing": [179000]}, index=["SE17EH"])
        assert health.site_places(sites, postcodes).tolist() == [[531000.0, 179000.0]]


class TestSeeds:
    def test_a_postcode_near_the_middle_of_each_part_of_the_region_asks_for_its_sites(self):
        cells = list(h3.grid_disk(h3.latlng_to_cell(51.5136, -0.1337, 9), 30))
        x, y = cell_centres_bng(cells[:1])[0]
        postcodes = pd.DataFrame(
            {"Easting": [x, x + 50000], "Northing": [y, y]}, index=["W1F9AA", "N11AA"]
        )
        seeds = health.ae_seed_postcodes(cells, postcodes)
        assert seeds == ["W1F 9AA"]  # the far postcode is nobody's nearest, and spaced for the form
