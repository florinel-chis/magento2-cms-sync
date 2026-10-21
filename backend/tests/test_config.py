"""Settings parsing: the values operators actually put in .env must work."""
import pytest

from config import Settings


def test_unknown_keys_in_env_file_are_ignored(tmp_path):
    env = tmp_path / ".env"
    env.write_text("API_PREFIX=/api\nSECRET_KEY=legacy\nMAGENTO_TIMEOUT=7\n")
    settings = Settings(_env_file=env)
    assert settings.magento_timeout == 7


@pytest.mark.parametrize("raw, expected", [
    ("http://localhost", ["http://localhost"]),
    ("http://a, http://b", ["http://a", "http://b"]),
    ('["http://a","http://b"]', ["http://a", "http://b"]),
])
def test_cors_origins_accepts_csv_and_json(raw, expected):
    assert Settings(_env_file=None, cors_origins=raw).cors_origin_list == expected
