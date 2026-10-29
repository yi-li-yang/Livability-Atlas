import json

import pytest

from atlas.datasets.countries.gb import arcgis

BOUNDS = (500000.0, 150000.0, 560000.0, 200000.0)


class Reply:
    def __init__(self, body: dict):
        self.body = body

    def raise_for_status(self):
        pass

    def json(self):
        return self.body


def feature(code: str) -> dict:
    return {"type": "Feature", "properties": {"CODE": code}, "geometry": None}


def serve(monkeypatch, pages: list[dict]) -> list[dict]:
    asked: list[dict] = []

    def fake_get(url, params, timeout):
        asked.append({"url": url, **params})
        return Reply(pages.pop(0))

    monkeypatch.setattr(arcgis.requests, "get", fake_get)
    return asked


def test_it_follows_the_pages_until_the_service_has_sent_everything(tmp_path, monkeypatch):
    asked = serve(
        monkeypatch,
        [
            {
                "features": [feature("A"), feature("B")],
                "properties": {"exceededTransferLimit": True},
            },
            {"features": [feature("C")]},
        ],
    )
    path = arcgis.fetch_features(tmp_path, "msoa", "https://example/query", "CODE", BOUNDS)
    found = json.loads(path.read_text(encoding="utf-8"))["features"]
    assert [f["properties"]["CODE"] for f in found] == ["A", "B", "C"]
    assert [q["resultOffset"] for q in asked] == [0, 2]
    assert asked[0]["geometry"] == "500000,150000,560000,200000"
    assert asked[0]["outFields"] == "CODE" and asked[0]["inSR"] == 27700


def test_a_file_already_kept_is_not_fetched_again(tmp_path, monkeypatch):
    serve(monkeypatch, [{"features": [feature("A")]}])
    first = arcgis.fetch_features(tmp_path, "msoa", "https://example/query", "CODE", BOUNDS)
    monkeypatch.setattr(arcgis.requests, "get", lambda *a, **k: pytest.fail("asked again"))
    assert arcgis.fetch_features(tmp_path, "msoa", "https://example/query", "CODE", BOUNDS) == first


def test_different_bounds_keep_different_files_and_each_kind_its_own_name(tmp_path, monkeypatch):
    serve(monkeypatch, [{"features": []}, {"features": []}, {"features": []}])
    one = arcgis.fetch_features(tmp_path, "msoa", "https://example/query", "CODE", BOUNDS)
    two = arcgis.fetch_features(tmp_path, "msoa", "https://example/query", "CODE", (0, 0, 1, 1))
    three = arcgis.fetch_features(tmp_path, "output-areas", "https://example/query", "CODE", BOUNDS)
    assert len({one, two, three}) == 3
    assert one.name.startswith("msoa-") and three.name.startswith("output-areas-")


def test_a_failed_download_leaves_no_file(tmp_path, monkeypatch):
    def broken(url, params, timeout):
        raise RuntimeError("the service is down")

    monkeypatch.setattr(arcgis.requests, "get", broken)
    with pytest.raises(RuntimeError):
        arcgis.fetch_features(tmp_path, "msoa", "https://example/query", "CODE", BOUNDS)
    assert not list((tmp_path / "raw" / "census").glob("*"))
