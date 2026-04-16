"""Customer extractor configuration loader."""

import json
import logging
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, field_validator

logger = logging.getLogger(__name__)


class CustomerConfig(BaseModel):
    label: str
    req_id_pattern: str
    title_pattern: str | None = None
    noise_patterns: list[str] = []


class CustomersConfig(BaseModel):
    customers: dict[str, CustomerConfig]

    @field_validator("customers")
    @classmethod
    def at_least_one(cls, v: dict) -> dict:
        if not v:
            raise ValueError("customers config must have at least one entry")
        return v


@lru_cache
def load_customers_config(config_path: str) -> CustomersConfig:
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Customers config not found: {path}")
    raw = json.loads(path.read_text(encoding="utf-8"))
    config = CustomersConfig.model_validate(raw)
    logger.info("Loaded %d customer(s) from %s", len(config.customers), path)
    return config


def list_customers(config_path: str) -> list[dict]:
    config = load_customers_config(config_path)
    return [{"id": cid, "label": c.label} for cid, c in config.customers.items()]


def get_customer(config_path: str, customer_id: str) -> CustomerConfig | None:
    config = load_customers_config(config_path)
    return config.customers.get(customer_id)
