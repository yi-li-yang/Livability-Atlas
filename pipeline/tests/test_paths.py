from atlas.paths import REPO_ROOT, data_dir


def test_data_dir_defaults_to_data_in_the_repository(monkeypatch):
    monkeypatch.delenv("ATLAS_DATA_DIR", raising=False)
    assert data_dir() == REPO_ROOT / "data"


def test_data_dir_follows_atlas_data_dir(monkeypatch, tmp_path):
    monkeypatch.setenv("ATLAS_DATA_DIR", str(tmp_path))
    assert data_dir() == tmp_path
