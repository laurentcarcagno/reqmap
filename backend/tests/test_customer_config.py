"""Tests for customer extractor configuration."""

import json
import pytest
from pathlib import Path

from app.services.customer_config import load_customers_config, list_customers, get_customer


@pytest.fixture
def customers_config_path(tmp_path) -> str:
    cfg = {
        "customers": {
            "airbus": {
                "label": "Airbus",
                "req_id_pattern": "^(HAR\\s+SSOW-\\d+)\\s*/\\s*(.+)$",
                "noise_patterns": ["^\\s*AIRBUS\\s*$"]
            }
        }
    }
    p = tmp_path / "customers.json"
    p.write_text(json.dumps(cfg), encoding="utf-8")
    return str(p)


def test_load_customers_config_has_airbus(customers_config_path):
    config = load_customers_config(customers_config_path)
    assert "airbus" in config.customers
    assert config.customers["airbus"].label == "Airbus"


def test_list_customers_returns_airbus(customers_config_path):
    customers = list_customers(customers_config_path)
    ids = [c["id"] for c in customers]
    assert "airbus" in ids


def test_get_customer_returns_config(customers_config_path):
    customer = get_customer(customers_config_path, "airbus")
    assert customer is not None
    assert customer.req_id_pattern == "^(HAR\\s+SSOW-\\d+)\\s*/\\s*(.+)$"


def test_get_customer_returns_none_for_unknown(customers_config_path):
    assert get_customer(customers_config_path, "unknown_corp") is None


def test_load_config_raises_for_missing_file():
    with pytest.raises(FileNotFoundError):
        load_customers_config("/nonexistent/customers.json")


def test_load_config_raises_for_empty_customers(tmp_path):
    p = tmp_path / "empty.json"
    p.write_text(json.dumps({"customers": {}}), encoding="utf-8")
    with pytest.raises(Exception):
        load_customers_config(str(p))


def test_shipped_config_has_the_thales_alenia_space_format():
    config = Path(__file__).resolve().parents[2] / "config" / "customers.json"
    load_customers_config.cache_clear()
    try:
        tas = get_customer(str(config), "tas")
        assert tas is not None and tas.label == "Thales Alénia Space"
        assert list(tas.post_process) == ["Thales Alénia Space"]
        assert (config.parents[1] / tas.post_process["Thales Alénia Space"]).is_file()
        assert get_customer(str(config), "airbus").post_process == {}
    finally:
        load_customers_config.cache_clear()
