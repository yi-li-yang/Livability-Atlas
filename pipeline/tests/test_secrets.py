import pytest

from atlas import secrets


def test_a_secret_comes_from_the_environment_first(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text("EPC_TOKEN=from-file\n", encoding="utf-8")
    monkeypatch.setenv("EPC_TOKEN", "from-environment")
    assert secrets.secret("EPC_TOKEN", root=tmp_path) == "from-environment"


def test_a_secret_is_read_from_the_env_file_otherwise(tmp_path, monkeypatch):
    monkeypatch.delenv("EPC_TOKEN", raising=False)
    (tmp_path / ".env").write_text(
        '# keys\nOTHER=1\nEPC_TOKEN = "abc=="\nexport LAST=2\n', encoding="utf-8"
    )
    assert secrets.secret("EPC_TOKEN", root=tmp_path) == "abc=="
    assert secrets.secret("LAST", root=tmp_path) == "2"


def test_a_missing_secret_says_which_one_and_where_it_goes(tmp_path, monkeypatch):
    monkeypatch.delenv("EPC_TOKEN", raising=False)
    with pytest.raises(RuntimeError, match=r"EPC_TOKEN.*\.env"):
        secrets.secret("EPC_TOKEN", root=tmp_path)


def test_the_error_never_shows_another_secrets_value(tmp_path, monkeypatch):
    monkeypatch.delenv("EPC_TOKEN", raising=False)
    (tmp_path / ".env").write_text("OTHER=do-not-print\n", encoding="utf-8")
    with pytest.raises(RuntimeError) as error:
        secrets.secret("EPC_TOKEN", root=tmp_path)
    assert "do-not-print" not in str(error.value)
