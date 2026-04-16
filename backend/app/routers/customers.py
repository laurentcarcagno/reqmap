"""Customer list endpoint."""

from fastapi import APIRouter, HTTPException

from app.config import get_settings
from app.schemas.customer import CustomerListResponse
from app.services.customer_config import list_customers

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("", response_model=CustomerListResponse)
async def get_customers() -> CustomerListResponse:
    """List all configured customers."""
    settings = get_settings()
    try:
        customers = list_customers(str(settings.customers_config_path))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return CustomerListResponse(data=customers)
