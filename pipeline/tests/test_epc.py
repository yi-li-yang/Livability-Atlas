import io

import pandas as pd
import pyarrow.csv as pacsv
import pytest

from atlas.datasets.countries.gb import epc
from atlas.datasets.countries.gb.addresses import address_key


class Reply:
    def __init__(self, status: int, location: str | None = None):
        self.status_code = status
        self.headers = {"location": location} if location else {}
        self.text = ""


def test_the_full_file_is_fetched_through_the_redirect_without_sending_the_token_on(
    tmp_path, monkeypatch
):
    calls, saved = [], []

    def fake_get(url, headers, allow_redirects, timeout):
        calls.append((url, headers, allow_redirects))
        return Reply(302, "https://s3.example/full-load/domestic-csv.zip?signed=1")

    monkeypatch.setattr(epc.requests, "get", fake_get)
    monkeypatch.setattr(epc, "token", lambda: "secret-token")
    monkeypatch.setattr(epc, "download", lambda url, target: saved.append((url, target.name)))
    path = epc.fetch(tmp_path)
    assert path.name == "domestic-csv.zip"
    assert calls[0][1]["Authorization"] == "Bearer secret-token"
    assert calls[0][2] is False  # the signed address is read, not followed with our token
    assert saved == [("https://s3.example/full-load/domestic-csv.zip?signed=1", "domestic-csv.zip")]


def test_a_file_already_kept_is_not_asked_for_again(tmp_path, monkeypatch):
    kept = tmp_path / "raw" / "epc" / "domestic-csv.zip"
    kept.parent.mkdir(parents=True)
    kept.write_bytes(b"zip")
    kept.with_name(kept.name + ".sha256").write_text("abc\n", encoding="utf-8")
    monkeypatch.setattr(epc.requests, "get", lambda *a, **k: pytest.fail("asked again"))
    assert epc.fetch(tmp_path) == kept


def test_a_refusal_says_what_to_check_and_never_shows_the_token(tmp_path, monkeypatch):
    monkeypatch.setattr(epc.requests, "get", lambda *a, **k: Reply(401))
    monkeypatch.setattr(epc, "token", lambda: "secret-token")
    with pytest.raises(RuntimeError) as error:
        epc.fetch(tmp_path)
    assert "401" in str(error.value) and "EPC_TOKEN" in str(error.value)
    assert "secret-token" not in str(error.value)


HEADER = (
    "certificate_number,address1,address2,address3,postcode,total_floor_area,lodgement_date,uprn"
)


def certificates_zip(tmp_path, files: dict[str, list[str]]):
    import zipfile

    path = tmp_path / "domestic-csv.zip"
    with zipfile.ZipFile(path, "w") as archive:
        for name, rows in files.items():
            archive.writestr(name, "\n".join([HEADER, *rows]) + "\n")
        archive.writestr("recommendations-2024.csv", "certificate_number,improvement_item\n1,2\n")
    return path


class TestReadCertificates:
    def test_it_reads_the_fingerprint_and_floor_area_of_each_home(self, tmp_path):
        path = certificates_zip(
            tmp_path,
            {
                "certificates-2023.csv": [
                    "A,Flat 3,12 Broad Street,,W1F 9AA,55.5,2023-01-02,1",
                    "B,14 Broad Street,,,W1F 9AB,80,2023-02-03,2",
                ],
                "certificates-2024.csv": ['C,"7, High Road",,,N1 1AA,100.25,2024-05-06,3'],
            },
        )
        found = epc.read_certificates(path, {"W1F9AA", "W1F9AB", "N11AA"})
        area = dict(zip(found["key"], found["floor_area"], strict=True))
        assert area[address_key("W1F 9AA", "Flat 3, 12 Broad Street")] == pytest.approx(55.5)
        assert area[address_key("W1F 9AB", "14 Broad Street")] == pytest.approx(80.0)
        assert area[address_key("N1 1AA", "7 High Road")] == pytest.approx(100.25)

    def test_no_address_is_kept(self, tmp_path):
        path = certificates_zip(
            tmp_path, {"certificates-2024.csv": ["A,12 Broad Street,,,W1F 9AA,55,2024-01-01,1"]}
        )
        found = epc.read_certificates(path, {"W1F9AA"})
        assert list(found.columns) == ["key", "floor_area"]
        assert "BROAD" not in " ".join(found["key"]).upper()

    def test_a_home_with_several_certificates_has_their_median_area(self, tmp_path):
        path = certificates_zip(
            tmp_path,
            {
                "certificates-2020.csv": ["A,12 Broad Street,,,W1F 9AA,60,2020-01-01,1"],
                "certificates-2022.csv": ["B,12 Broad Street,,,W1F 9AA,62,2022-01-01,1"],
                "certificates-2024.csv": ["C,12 Broad Street,,,W1F 9AA,90,2024-01-01,1"],
            },
        )
        found = epc.read_certificates(path, {"W1F9AA"})
        assert found["floor_area"].tolist() == [62.0]

    def test_it_keeps_only_the_postcodes_asked_for_whatever_their_spacing_or_case(self, tmp_path):
        path = certificates_zip(
            tmp_path,
            {
                "certificates-2024.csv": [
                    "A,1 A Road,,,w1f9aa,50,2024-01-01,1",
                    "B,2 A Road,,,W1F 9AB,50,2024-01-01,2",
                    "C,3 A Road,,,,50,2024-01-01,3",
                ]
            },
        )
        found = epc.read_certificates(path, {"W1F9AA"})
        assert found["key"].tolist() == [address_key("W1F9AA", "1 A Road")]

    def test_a_certificate_without_a_usable_floor_area_is_left_out(self, tmp_path):
        path = certificates_zip(
            tmp_path,
            {
                "certificates-2024.csv": [
                    "A,1 A Road,,,W1F 9AA,,2024-01-01,1",
                    "B,2 A Road,,,W1F 9AA,0,2024-01-01,2",
                    "C,3 A Road,,,W1F 9AA,n/a,2024-01-01,3",
                    "D,4 A Road,,,W1F 9AA,64,2024-01-01,4",
                ]
            },
        )
        found = epc.read_certificates(path, {"W1F9AA"})
        assert found["key"].tolist() == [address_key("W1F 9AA", "4 A Road")]

    def test_the_recommendations_files_are_not_read(self, tmp_path):
        path = certificates_zip(
            tmp_path, {"certificates-2024.csv": ["A,1 A Road,,,W1F 9AA,50,2024-01-01,1"]}
        )
        assert len(epc.read_certificates(path, {"W1F9AA"})) == 1

    def test_no_certificate_at_those_postcodes_gives_an_empty_table(self, tmp_path):
        path = certificates_zip(
            tmp_path, {"certificates-2024.csv": ["A,1 A Road,,,W1F 9AA,50,2024-01-01,1"]}
        )
        found = epc.read_certificates(path, {"ZZ99ZZ"})
        assert found.empty and list(found.columns) == ["key", "floor_area"]


class TestKept:
    def test_the_london_certificates_are_read_once_per_download(self, tmp_path, monkeypatch):
        archive = tmp_path / "raw" / "epc" / "domestic-csv.zip"
        archive.parent.mkdir(parents=True)
        archive.write_bytes(b"zip")
        archive.with_name(archive.name + ".sha256").write_text(
            "0123456789abcdef\n", encoding="utf-8"
        )
        reads = []

        def fake_read(path, postcodes):
            reads.append(1)
            return pd.DataFrame({"key": ["abc"], "floor_area": [50.0]})

        monkeypatch.setattr(epc, "read_certificates", fake_read)
        first = epc.certificates(tmp_path, "london", {"W1F9AA"})
        second = epc.certificates(tmp_path, "london", {"W1F9AA"})
        assert len(reads) == 1 and first.equals(second)
        assert (archive.parent / "certificates-london-0123456789ab.parquet").exists()


def csv_rows(block: bytes) -> list[str]:
    return pacsv.read_csv(io.BytesIO(block))["a"].to_pylist()


class TestBlocks:
    def test_each_block_ends_at_the_end_of_a_record_even_when_a_quoted_field_spans_lines(self):
        rows = [f'{i},"line one\nline two {i}",x' for i in range(50)]
        data = ("a,b,c\n" + "\n".join(rows) + "\n").encode("utf-8")
        blocks = list(epc._blocks(io.BytesIO(data), size=97))
        assert len(blocks) > 3
        for block in blocks:
            assert block.count(b'"') % 2 == 0
            # Every block starts with the header again, so each reads as a table of its own.
            assert block.startswith(b"a,b,c\n") and block.endswith(b"\n")
        records = [r for block in blocks for r in csv_rows(block)]
        assert sorted(records) == list(range(50))

    def test_a_record_longer_than_a_block_is_not_cut(self):
        data = b'a,b\n1,"' + b"x" * 300 + b'"\n2,y\n'
        blocks = list(epc._blocks(io.BytesIO(data), size=50))
        assert sorted(r for block in blocks for r in csv_rows(block)) == [1, 2]

    def test_a_file_that_fits_in_one_block_is_one_block(self):
        assert len(list(epc._blocks(io.BytesIO(b"a,b\n1,2\n"), size=1000))) == 1

    def test_a_file_that_is_exactly_whole_blocks_loses_nothing(self):
        data = b"a,b\n" + b"1,2\n" * 10
        blocks = list(epc._blocks(io.BytesIO(data), size=20))
        assert sum(len(csv_rows(block)) for block in blocks) == 10
