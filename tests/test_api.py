import pytest
from datetime import date, timedelta
from httpx import AsyncClient


@pytest.mark.asyncio
class TestHealthEndpoint:
    """Test cases for the health check endpoint."""

    async def test_health_check_returns_200(self, async_client: AsyncClient):
        """Test that health check returns 200 OK."""
        response = await async_client.get("/healthz")
        
        assert response.status_code == 200

    async def test_health_check_response_format(self, async_client: AsyncClient):
        """Test that health check returns correct format."""
        response = await async_client.get("/healthz")
        data = response.json()
        
        assert "status" in data
        assert "service" in data
        assert "version" in data
        assert data["status"] == "healthy"


@pytest.mark.asyncio
class TestRootEndpoint:
    """Test cases for the root endpoint."""

    async def test_root_returns_200(self, async_client: AsyncClient):
        """Test that root endpoint returns 200 OK."""
        response = await async_client.get("/")
        
        assert response.status_code == 200

    async def test_root_response_contains_links(self, async_client: AsyncClient):
        """Test that root endpoint contains documentation links."""
        response = await async_client.get("/")
        data = response.json()
        
        assert "message" in data
        assert "docs" in data
        assert "health" in data


@pytest.mark.asyncio
class TestOptimizeEndpoint:
    """Test cases for the optimize endpoint."""

    async def test_optimize_returns_200(self, async_client: AsyncClient):
        """Test that optimize returns 200 OK for valid request."""
        today = date.today().isoformat()
        delivery = (date.today() + timedelta(days=2)).isoformat()
        
        request_data = {
            "truck": {
                "id": "truck-001",
                "max_weight_lbs": 45000,
                "max_volume_cuft": 2500
            },
            "orders": [
                {
                    "id": "ORD-001",
                    "payout_cents": 125000,
                    "weight_lbs": 12000,
                    "volume_cuft": 600,
                    "origin": "Chicago, IL",
                    "destination": "Dallas, TX",
                    "pickup_date": today,
                    "delivery_date": delivery,
                    "is_hazmat": False
                }
            ]
        }
        
        response = await async_client.post("/api/v1/load-optimizer/optimize", json=request_data)
        
        assert response.status_code == 200

    async def test_optimize_response_format(self, async_client: AsyncClient):
        """Test that optimize returns correct response format."""
        today = date.today().isoformat()
        delivery = (date.today() + timedelta(days=2)).isoformat()
        
        request_data = {
            "truck": {
                "id": "truck-001",
                "max_weight_lbs": 45000,
                "max_volume_cuft": 2500
            },
            "orders": [
                {
                    "id": "ORD-001",
                    "payout_cents": 125000,
                    "weight_lbs": 12000,
                    "volume_cuft": 600,
                    "origin": "Chicago, IL",
                    "destination": "Dallas, TX",
                    "pickup_date": today,
                    "delivery_date": delivery,
                    "is_hazmat": False
                }
            ]
        }
        
        response = await async_client.post("/api/v1/load-optimizer/optimize", json=request_data)
        data = response.json()
        
        assert "truck_id" in data
        assert "selected_order_ids" in data
        assert "total_payout_cents" in data
        assert "total_weight_lbs" in data
        assert "total_volume_cuft" in data
        assert "utilization_weight_percent" in data
        assert "utilization_volume_percent" in data

    async def test_optimize_empty_orders(self, async_client: AsyncClient):
        """Test optimize with empty orders list."""
        request_data = {
            "truck": {
                "id": "truck-001",
                "max_weight_lbs": 45000,
                "max_volume_cuft": 2500
            },
            "orders": []
        }
        
        response = await async_client.post("/api/v1/load-optimizer/optimize", json=request_data)
        data = response.json()
        
        assert response.status_code == 200
        assert data["selected_order_ids"] == []
        assert data["total_payout_cents"] == 0

    async def test_optimize_selects_best_orders(self, async_client: AsyncClient):
        """Test that optimizer selects the best combination of orders."""
        today = date.today().isoformat()
        delivery = (date.today() + timedelta(days=2)).isoformat()
        
        request_data = {
            "truck": {
                "id": "truck-001",
                "max_weight_lbs": 45000,
                "max_volume_cuft": 2500
            },
            "orders": [
                {
                    "id": "ORD-001",
                    "payout_cents": 125000,
                    "weight_lbs": 12000,
                    "volume_cuft": 600,
                    "origin": "Chicago, IL",
                    "destination": "Dallas, TX",
                    "pickup_date": today,
                    "delivery_date": delivery,
                    "is_hazmat": False
                },
                {
                    "id": "ORD-002",
                    "payout_cents": 98000,
                    "weight_lbs": 8500,
                    "volume_cuft": 450,
                    "origin": "Chicago, IL",
                    "destination": "Dallas, TX",
                    "pickup_date": today,
                    "delivery_date": delivery,
                    "is_hazmat": False
                }
            ]
        }
        
        response = await async_client.post("/api/v1/load-optimizer/optimize", json=request_data)
        data = response.json()
        
        assert response.status_code == 200
        # Both orders should fit
        assert len(data["selected_order_ids"]) == 2
        assert data["total_payout_cents"] == 223000  # 125000 + 98000


@pytest.mark.asyncio
class TestValidationErrors:
    """Test cases for validation error handling."""

    async def test_missing_truck_id(self, async_client: AsyncClient):
        """Test that missing truck ID returns 400."""
        request_data = {
            "truck": {
                "max_weight_lbs": 45000,
                "max_volume_cuft": 2500
            },
            "orders": []
        }
        
        response = await async_client.post("/api/v1/load-optimizer/optimize", json=request_data)
        
        assert response.status_code == 400

    async def test_negative_weight(self, async_client: AsyncClient):
        """Test that negative weight returns 400."""
        request_data = {
            "truck": {
                "id": "truck-001",
                "max_weight_lbs": -1000,
                "max_volume_cuft": 2500
            },
            "orders": []
        }
        
        response = await async_client.post("/api/v1/load-optimizer/optimize", json=request_data)
        
        assert response.status_code == 400

    async def test_invalid_date_format(self, async_client: AsyncClient):
        """Test that invalid date format returns 400."""
        request_data = {
            "truck": {
                "id": "truck-001",
                "max_weight_lbs": 45000,
                "max_volume_cuft": 2500
            },
            "orders": [
                {
                    "id": "ORD-001",
                    "payout_cents": 125000,
                    "weight_lbs": 12000,
                    "volume_cuft": 600,
                    "origin": "Chicago, IL",
                    "destination": "Dallas, TX",
                    "pickup_date": "invalid-date",
                    "delivery_date": "2024-01-20",
                    "is_hazmat": False
                }
            ]
        }
        
        response = await async_client.post("/api/v1/load-optimizer/optimize", json=request_data)
        
        assert response.status_code == 400

    async def test_delivery_before_pickup(self, async_client: AsyncClient):
        """Test that delivery date before pickup returns 400."""
        today = date.today()
        
        request_data = {
            "truck": {
                "id": "truck-001",
                "max_weight_lbs": 45000,
                "max_volume_cuft": 2500
            },
            "orders": [
                {
                    "id": "ORD-001",
                    "payout_cents": 125000,
                    "weight_lbs": 12000,
                    "volume_cuft": 600,
                    "origin": "Chicago, IL",
                    "destination": "Dallas, TX",
                    "pickup_date": (today + timedelta(days=5)).isoformat(),
                    "delivery_date": today.isoformat(),  # Before pickup
                    "is_hazmat": False
                }
            ]
        }
        
        response = await async_client.post("/api/v1/load-optimizer/optimize", json=request_data)
        
        assert response.status_code == 400

    async def test_duplicate_order_ids(self, async_client: AsyncClient):
        """Test that duplicate order IDs returns 400."""
        today = date.today().isoformat()
        delivery = (date.today() + timedelta(days=2)).isoformat()
        
        request_data = {
            "truck": {
                "id": "truck-001",
                "max_weight_lbs": 45000,
                "max_volume_cuft": 2500
            },
            "orders": [
                {
                    "id": "ORD-001",
                    "payout_cents": 125000,
                    "weight_lbs": 12000,
                    "volume_cuft": 600,
                    "origin": "Chicago, IL",
                    "destination": "Dallas, TX",
                    "pickup_date": today,
                    "delivery_date": delivery,
                    "is_hazmat": False
                },
                {
                    "id": "ORD-001",  # Duplicate ID
                    "payout_cents": 98000,
                    "weight_lbs": 8500,
                    "volume_cuft": 450,
                    "origin": "Chicago, IL",
                    "destination": "Dallas, TX",
                    "pickup_date": today,
                    "delivery_date": delivery,
                    "is_hazmat": False
                }
            ]
        }
        
        response = await async_client.post("/api/v1/load-optimizer/optimize", json=request_data)
        
        assert response.status_code == 400


@pytest.mark.asyncio
class TestOrderLimit:
    """Test cases for order limit handling."""

    async def test_too_many_orders_returns_413(self, async_client: AsyncClient):
        """Test that exceeding order limit returns 413."""
        today = date.today().isoformat()
        delivery = (date.today() + timedelta(days=2)).isoformat()
        
        # Create 30 orders (exceeds default limit of 25)
        orders = [
            {
                "id": f"ORD-{i:03d}",
                "payout_cents": 100000,
                "weight_lbs": 1000,
                "volume_cuft": 50,
                "origin": "Chicago, IL",
                "destination": "Dallas, TX",
                "pickup_date": today,
                "delivery_date": delivery,
                "is_hazmat": False
            }
            for i in range(30)
        ]
        
        request_data = {
            "truck": {
                "id": "truck-001",
                "max_weight_lbs": 45000,
                "max_volume_cuft": 2500
            },
            "orders": orders
        }
        
        response = await async_client.post("/api/v1/load-optimizer/optimize", json=request_data)
        
        assert response.status_code == 413


@pytest.mark.asyncio
class TestOpenAPIDocumentation:
    """Test cases for OpenAPI documentation endpoints."""

    async def test_openapi_json_available(self, async_client: AsyncClient):
        """Test that OpenAPI JSON is available."""
        response = await async_client.get("/openapi.json")
        
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data

    async def test_docs_endpoint_available(self, async_client: AsyncClient):
        """Test that Swagger UI docs are available."""
        response = await async_client.get("/docs")
        
        assert response.status_code == 200

    async def test_redoc_endpoint_available(self, async_client: AsyncClient):
        """Test that ReDoc docs are available."""
        response = await async_client.get("/redoc")
        
        assert response.status_code == 200
