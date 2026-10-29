import pytest
import requests

from atlas.datasets.cities.london import tfl_api


class Reply:
    def __init__(self, status: int, body=None):
        self.status_code = status
        self._body = body if body is not None else {"ok": True}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code} Error", response=self)  # type: ignore[arg-type]

    def json(self):
        return self._body


def replies(monkeypatch, *statuses: int) -> list[str]:
    asked: list[str] = []
    queue = list(statuses)

    def fake_get(url, timeout):
        asked.append(url)
        return Reply(queue.pop(0))

    monkeypatch.setattr(tfl_api.requests, "get", fake_get)
    monkeypatch.setattr(tfl_api.time, "sleep", lambda seconds: None)
    return asked


def test_an_answer_is_its_json(monkeypatch):
    asked = replies(monkeypatch, 200)
    assert tfl_api.get("Line/Mode/bus") == {"ok": True}
    assert asked == ["https://api.tfl.gov.uk/Line/Mode/bus"]


@pytest.mark.parametrize("status", [429, 500, 502, 503, 504])
def test_a_request_that_is_refused_or_fails_at_the_server_is_tried_again(monkeypatch, status):
    asked = replies(monkeypatch, status, status, 200)
    assert tfl_api.get("Line/x") == {"ok": True}
    assert len(asked) == 3


def test_it_gives_up_after_the_retries_with_a_message_that_names_the_request(monkeypatch):
    replies(monkeypatch, *[504] * tfl_api.RETRIES)
    with pytest.raises(RuntimeError, match="Line/x"):
        tfl_api.get("Line/x")


def test_nothing_found_is_none_when_that_is_expected_and_an_error_otherwise(monkeypatch):
    replies(monkeypatch, 404)
    assert tfl_api.get("Journey/x", missing=True) is None
    replies(monkeypatch, 404)
    with pytest.raises(requests.HTTPError):
        tfl_api.get("Line/x")


def test_a_client_error_that_is_not_about_a_missing_answer_is_raised_at_once(monkeypatch):
    asked = replies(monkeypatch, 401)
    with pytest.raises(requests.HTTPError):
        tfl_api.get("Line/x", missing=True)
    assert len(asked) == 1
