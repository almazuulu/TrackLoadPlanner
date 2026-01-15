# Truck Load Planner API

A FastAPI-based REST API for optimal truck load planning that maximizes carrier revenue while respecting weight, volume, hazmat, and route constraints using bitmask dynamic programming.

## Features

- **Optimal Load Selection**: Uses bitmask DP algorithm to find the best combination of orders
- **Constraint Handling**: Respects weight, volume, hazmat isolation, and route constraints
- **Time Window Validation**: Ensures pickup and delivery dates are compatible
- **High Performance**: Handles up to 25 orders efficiently with O(2^n) complexity
- **RESTful API**: Clean API design with OpenAPI documentation

## Quick Start

### Using Docker Compose (Recommended)

```bash
# Clone the repository
git clone <your-repo>
cd TrackLoadPlanner

# Start the service
docker compose up --build

# The API will be available at http://localhost:8080
```

### Using Docker Compose (Development Mode)

```bash
# Start with hot reload enabled
docker compose --profile dev up api-dev --build
```

### Running Locally

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

## API Endpoints

### Health Check

```http
GET /healthz
```

Response:
```json
{
  "status": "healthy",
  "service": "Truck Load Planner API",
  "version": "1.0.0"
}
```

### Optimize Load

```http
POST /api/v1/load-optimizer/optimize
Content-Type: application/json
```

#### Request Body

```json
{
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
      "pickup_date": "2026-01-15",
      "delivery_date": "2026-01-18",
      "is_hazmat": false
    },
    {
      "id": "ORD-002",
      "payout_cents": 98000,
      "weight_lbs": 8500,
      "volume_cuft": 450,
      "origin": "Chicago, IL",
      "destination": "Dallas, TX",
      "pickup_date": "2026-01-15",
      "delivery_date": "2026-01-17",
      "is_hazmat": false
    }
  ]
}
```

#### Response

```json
{
  "truck_id": "truck-001",
  "selected_order_ids": ["ORD-001", "ORD-002"],
  "total_payout_cents": 223000,
  "total_weight_lbs": 20500,
  "total_volume_cuft": 1050,
  "utilization_weight_percent": 45.56,
  "utilization_volume_percent": 42.0
}
```

## Example Request with cURL

```bash
curl -X POST http://localhost:8080/api/v1/load-optimizer/optimize \
  -H "Content-Type: application/json" \
  -d '{
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
        "pickup_date": "2026-01-15",
        "delivery_date": "2026-01-18",
        "is_hazmat": false
      },
      {
        "id": "ORD-002",
        "payout_cents": 98000,
        "weight_lbs": 8500,
        "volume_cuft": 450,
        "origin": "Chicago, IL",
        "destination": "Dallas, TX",
        "pickup_date": "2026-01-15",
        "delivery_date": "2026-01-17",
        "is_hazmat": false
      }
    ]
  }'
```

Or use the sample request file:

```bash
curl -X POST http://localhost:8080/api/v1/load-optimizer/optimize \
  -H "Content-Type: application/json" \
  -d @sample-request.json
```

## API Documentation

Interactive API documentation is available when the service is running:

- **Swagger UI**: http://localhost:8080/docs
- **ReDoc**: http://localhost:8080/redoc
- **OpenAPI JSON**: http://localhost:8080/openapi.json

## Business Rules

### Compatibility Constraints

1. **Same Lane**: Orders must have the same origin AND destination to be combined
2. **Hazmat Isolation**: Hazmat orders cannot be mixed with non-hazmat orders
3. **Time Windows**: All orders must have compatible pickup/delivery dates
4. **Capacity Limits**: Combined weight and volume must not exceed truck capacity

### Optimization Strategy

The API uses bitmask dynamic programming to find the optimal subset of orders:

1. Groups orders by compatibility (same lane + same hazmat status)
2. Filters out orders that individually exceed truck capacity
3. Iterates through all valid subsets (2^n combinations)
4. Returns the subset that maximizes total payout

## Running Tests

```bash
# Install test dependencies
pip install -r requirements.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_optimizer_service.py -v
pytest tests/test_api.py -v
```

## Configuration

Environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_NAME` | Application name | Truck Load Planner API |
| `APP_VERSION` | API version | 1.0.0 |
| `DEBUG` | Enable debug mode | false |
| `MAX_ORDERS_PER_REQUEST` | Maximum orders allowed per request | 25 |

## Error Responses

| Status Code | Description |
|-------------|-------------|
| 200 | Successful optimization (may return empty selection) |
| 400 | Invalid input data or validation error |
| 413 | Too many orders in request |
| 500 | Internal server error |
