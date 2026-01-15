"""Pytest fixtures for the Truck Load Planner API tests."""

import pytest
import pytest_asyncio
from datetime import date, timedelta
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.models.request import Truck, Order, OptimizeRequest


@pytest.fixture
def sample_truck() -> Truck:
    """Create a sample truck for testing."""
    return Truck(
        id="truck-001",
        max_weight_lbs=45000,
        max_volume_cuft=2500
    )


@pytest.fixture
def sample_orders() -> list[Order]:
    """Create a list of sample orders for testing."""
    today = date.today()
    return [
        Order(
            id="ORD-001",
            payout_cents=125000,
            weight_lbs=12000,
            volume_cuft=600,
            origin="Chicago, IL",
            destination="Dallas, TX",
            pickup_date=today,
            delivery_date=today + timedelta(days=3),
            is_hazmat=False
        ),
        Order(
            id="ORD-002",
            payout_cents=98000,
            weight_lbs=8500,
            volume_cuft=450,
            origin="Chicago, IL",
            destination="Dallas, TX",
            pickup_date=today,
            delivery_date=today + timedelta(days=2),
            is_hazmat=False
        ),
        Order(
            id="ORD-003",
            payout_cents=145000,
            weight_lbs=15000,
            volume_cuft=800,
            origin="Chicago, IL",
            destination="Dallas, TX",
            pickup_date=today + timedelta(days=1),
            delivery_date=today + timedelta(days=4),
            is_hazmat=False
        ),
        Order(
            id="ORD-004",
            payout_cents=75000,
            weight_lbs=6000,
            volume_cuft=350,
            origin="Chicago, IL",
            destination="Dallas, TX",
            pickup_date=today,
            delivery_date=today + timedelta(days=2),
            is_hazmat=False
        ),
    ]


@pytest.fixture
def sample_hazmat_orders() -> list[Order]:
    """Create a list of hazmat orders for testing."""
    today = date.today()
    return [
        Order(
            id="HAZ-001",
            payout_cents=180000,
            weight_lbs=18000,
            volume_cuft=900,
            origin="Chicago, IL",
            destination="Dallas, TX",
            pickup_date=today,
            delivery_date=today + timedelta(days=3),
            is_hazmat=True
        ),
        Order(
            id="HAZ-002",
            payout_cents=120000,
            weight_lbs=10000,
            volume_cuft=500,
            origin="Chicago, IL",
            destination="Dallas, TX",
            pickup_date=today,
            delivery_date=today + timedelta(days=3),
            is_hazmat=True
        ),
    ]


@pytest.fixture
def sample_different_route_order() -> Order:
    """Create an order with a different route."""
    today = date.today()
    return Order(
        id="ORD-DIFF",
        payout_cents=200000,
        weight_lbs=20000,
        volume_cuft=1000,
        origin="New York, NY",
        destination="Miami, FL",
        pickup_date=today,
        delivery_date=today + timedelta(days=5),
        is_hazmat=False
    )


@pytest.fixture
def sample_request(sample_truck: Truck, sample_orders: list[Order]) -> OptimizeRequest:
    """Create a sample optimization request."""
    return OptimizeRequest(truck=sample_truck, orders=sample_orders)


@pytest.fixture
def oversized_order() -> Order:
    """Create an order that exceeds truck capacity."""
    today = date.today()
    return Order(
        id="ORD-BIG",
        payout_cents=500000,
        weight_lbs=50000,  # Exceeds max weight
        volume_cuft=3000,  # Exceeds max volume
        origin="Chicago, IL",
        destination="Dallas, TX",
        pickup_date=today,
        delivery_date=today + timedelta(days=3),
        is_hazmat=False
    )


@pytest_asyncio.fixture
async def async_client():
    """Create an async HTTP client for API testing."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
