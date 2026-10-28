import hashlib
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from atlas.fetch import download

BODY = b"a grid of points"


class Handler(BaseHTTPRequestHandler):
    requests = 0

    def do_GET(self):
        Handler.requests += 1
        if self.path == "/missing":
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Length", str(len(BODY)))
        self.end_headers()
        self.wfile.write(BODY)

    def log_message(self, format: str, *args: object) -> None:
        pass


@pytest.fixture
def server():
    Handler.requests = 0
    httpd = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{httpd.server_port}"
    httpd.shutdown()


def test_a_download_is_saved_with_its_checksum(server, tmp_path):
    target = tmp_path / "raw" / "ptal.zip"
    digest = download(f"{server}/ptal.zip", target)
    assert target.read_bytes() == BODY
    assert digest == hashlib.sha256(BODY).hexdigest()
    assert (tmp_path / "raw" / "ptal.zip.sha256").read_text(encoding="utf-8").strip() == digest


def test_a_file_that_is_already_there_is_not_fetched_again(server, tmp_path):
    target = tmp_path / "ptal.zip"
    download(f"{server}/ptal.zip", target)
    again = download(f"{server}/ptal.zip", target)
    assert Handler.requests == 1
    assert again == hashlib.sha256(BODY).hexdigest()


def test_a_file_that_no_longer_matches_its_checksum_is_fetched_again(server, tmp_path):
    target = tmp_path / "ptal.zip"
    download(f"{server}/ptal.zip", target)
    target.write_bytes(b"damaged")
    download(f"{server}/ptal.zip", target)
    assert target.read_bytes() == BODY
    assert Handler.requests == 2


def test_a_failed_download_leaves_nothing_behind(server, tmp_path):
    target = tmp_path / "gone.zip"
    with pytest.raises(Exception, match="404"):
        download(f"{server}/missing", target)
    assert not target.exists()
    assert list(tmp_path.iterdir()) == []
