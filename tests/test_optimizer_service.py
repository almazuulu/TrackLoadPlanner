import pytest
from datetime import date, timedelta

from app.models.request import Truck, Order, OptimizeRequest
from app.services.optimizer import OptimizerService, optimize_load


class TestOptimizerService:
    """Test cases for the OptimizerService class."""

    def test_optimize_empty_orders(self, sample_truck: Truck):
        """Test optimization with empty orders list returns empty result."""
        request = OptimizeRequest(truck=sample_truck, orders=[])
        result = optimize_load(request)

        assert result.truck_id == sample_truck.id
        assert result.selected_order_ids == []
        assert result.total_payout_cents == 0
        assert result.total_weight_lbs == 0
        assert result.total_volume_cuft == 0
        assert result.utilization_weight_percent == 0.0
        assert result.utilization_volume_percent == 0.0

    def test_optimize_single_order_fits(self, sample_truck: Truck, sample_orders: list[Order]):
        """Test optimization with a single order that fits."""
        request = OptimizeRequest(truck=sample_truck, orders=[sample_orders[0]])
        result = optimize_load(request)

        assert result.truck_id == sample_truck.id
        assert len(result.selected_order_ids) == 1
        assert sample_orders[0].id in result.selected_order_ids
        assert result.total_payout_cents == sample_orders[0].payout_cents
        assert result.total_weight_lbs == sample_orders[0].weight_lbs
        assert result.total_volume_cuft == sample_orders[0].volume_cuft

    def test_optimize_single_order_exceeds_weight(self, sample_truck: Truck, oversized_order: Order):
        """Test optimization with an order exceeding weight capacity."""
        request = OptimizeRequest(truck=sample_truck, orders=[oversized_order])
        result = optimize_load(request)

        assert result.selected_order_ids == []
        assert result.total_payout_cents == 0

    def test_optimize_multiple_orders_same_lane(self, sample_truck: Truck, sample_orders: list[Order]):
        """Test optimization with multiple orders on the same lane."""
        request = OptimizeRequest(truck=sample_truck, orders=sample_orders)
        result = optimize_load(request)

        assert result.truck_id == sample_truck.id
        # Should select some orders
        assert len(result.selected_order_ids) > 0
        # Total payout should be positive
        assert result.total_payout_cents > 0
        # Should not exceed truck capacity
        assert result.total_weight_lbs <= sample_truck.max_weight_lbs
        assert result.total_volume_cuft <= sample_truck.max_volume_cuft

    def test_optimize_maximizes_payout(self, sample_truck: Truck):
        """Test that optimizer maximizes payout."""
        today = date.today()
        orders = [
            Order(
                id="LOW",
                payout_cents=50000,
                weight_lbs=20000,
                volume_cuft=1000,
                origin="Chicago, IL",
                destination="Dallas, TX",
                pickup_date=today,
                delivery_date=today + timedelta(days=2),
                is_hazmat=False
            ),
            Order(
                id="HIGH",
                payout_cents=200000,
                weight_lbs=20000,
                volume_cuft=1000,
                origin="Chicago, IL",
                destination="Dallas, TX",
                pickup_date=today,
                delivery_date=today + timedelta(days=2),
                is_hazmat=False
            ),
        ]
        
        request = OptimizeRequest(truck=sample_truck, orders=orders)
        result = optimize_load(request)

        # Should select both if they fit, otherwise the higher payout one
        assert "HIGH" in result.selected_order_ids

    def test_optimize_respects_weight_capacity(self, sample_truck: Truck):
        """Test that optimizer respects weight capacity."""
        today = date.today()
        orders = [
            Order(
                id="ORD-1",
                payout_cents=100000,
                weight_lbs=30000,
                volume_cuft=500,
                origin="Chicago, IL",
                destination="Dallas, TX",
                pickup_date=today,
                delivery_date=today + timedelta(days=2),
                is_hazmat=False
            ),
            Order(
                id="ORD-2",
                payout_cents=100000,
                weight_lbs=30000,
                volume_cuft=500,
                origin="Chicago, IL",
                destination="Dallas, TX",
                pickup_date=today,
                delivery_date=today + timedelta(days=2),
                is_hazmat=False
            ),
        ]
        
        request = OptimizeRequest(truck=sample_truck, orders=orders)
        result = optimize_load(request)

        # Combined weight (60000) exceeds truck capacity (45000)
        # Should only select one order
        assert len(result.selected_order_ids) == 1
        assert result.total_weight_lbs <= sample_truck.max_weight_lbs

    def test_optimize_respects_volume_capacity(self):
        """Test that optimizer respects volume capacity."""
        today = date.today()
        small_truck = Truck(id="small-truck", max_weight_lbs=100000, max_volume_cuft=1000)
        orders = [
            Order(
                id="ORD-1",
                payout_cents=100000,
                weight_lbs=5000,
                volume_cuft=800,
                origin="Chicago, IL",
                destination="Dallas, TX",
                pickup_date=today,
                delivery_date=today + timedelta(days=2),
                is_hazmat=False
            ),
            Order(
                id="ORD-2",
                payout_cents=100000,
                weight_lbs=5000,
                volume_cuft=800,
                origin="Chicago, IL",
                destination="Dallas, TX",
                pickup_date=today,
                delivery_date=today + timedelta(days=2),
                is_hazmat=False
            ),
        ]
        
        request = OptimizeRequest(truck=small_truck, orders=orders)
        result = optimize_load(request)

        # Combined volume (1600) exceeds truck capacity (1000)
        # Should only select one order
        assert len(result.selected_order_ids) == 1
        assert result.total_volume_cuft <= small_truck.max_volume_cuft

    def test_optimize_hazmat_isolation(self, sample_truck: Truck, sample_orders: list[Order], sample_hazmat_orders: list[Order]):
        """Test that hazmat orders are isolated from non-hazmat orders."""
        all_orders = sample_orders + sample_hazmat_orders
        request = OptimizeRequest(truck=sample_truck, orders=all_orders)
        result = optimize_load(request)

        selected_ids = set(result.selected_order_ids)
        
        # Get selected orders
        selected_orders = [o for o in all_orders if o.id in selected_ids]
        
        if len(selected_orders) > 1:
            # All selected orders should have the same hazmat status
            hazmat_statuses = set(o.is_hazmat for o in selected_orders)
            assert len(hazmat_statuses) == 1, "Mixed hazmat and non-hazmat orders selected"

    def test_optimize_same_lane_required(self, sample_truck: Truck, sample_orders: list[Order], sample_different_route_order: Order):
        """Test that only orders on the same lane are combined."""
        orders = sample_orders[:2] + [sample_different_route_order]
        request = OptimizeRequest(truck=sample_truck, orders=orders)
        result = optimize_load(request)

        selected_ids = set(result.selected_order_ids)
        
        # Get selected orders
        selected_orders = [o for o in orders if o.id in selected_ids]
        
        if len(selected_orders) > 1:
            # All selected orders should have the same origin and destination
            origins = set(o.origin for o in selected_orders)
            destinations = set(o.destination for o in selected_orders)
            assert len(origins) == 1, "Mixed origins in selected orders"
            assert len(destinations) == 1, "Mixed destinations in selected orders"

    def test_optimize_time_window_compatibility(self, sample_truck: Truck):
        """Test that orders with incompatible time windows are not combined."""
        today = date.today()
        orders = [
            Order(
                id="EARLY",
                payout_cents=100000,
                weight_lbs=10000,
                volume_cuft=500,
                origin="Chicago, IL",
                destination="Dallas, TX",
                pickup_date=today,
                delivery_date=today + timedelta(days=1),  # Delivers on day 1
                is_hazmat=False
            ),
            Order(
                id="LATE",
                payout_cents=100000,
                weight_lbs=10000,
                volume_cuft=500,
                origin="Chicago, IL",
                destination="Dallas, TX",
                pickup_date=today + timedelta(days=5),  # Picks up on day 5
                delivery_date=today + timedelta(days=7),
                is_hazmat=False
            ),
        ]
        
        request = OptimizeRequest(truck=sample_truck, orders=orders)
        result = optimize_load(request)

        # These orders are not time-compatible, so only one should be selected
        assert len(result.selected_order_ids) == 1

    def test_optimize_utilization_calculation(self, sample_truck: Truck):
        """Test that utilization percentages are calculated correctly."""
        today = date.today()
        order = Order(
            id="ORD-1",
            payout_cents=100000,
            weight_lbs=22500,  # 50% of 45000
            volume_cuft=1250,  # 50% of 2500
            origin="Chicago, IL",
            destination="Dallas, TX",
            pickup_date=today,
            delivery_date=today + timedelta(days=2),
            is_hazmat=False
        )
        
        request = OptimizeRequest(truck=sample_truck, orders=[order])
        result = optimize_load(request)

        assert result.utilization_weight_percent == 50.0
        assert result.utilization_volume_percent == 50.0

    def test_optimize_multiple_hazmat_orders(self, sample_truck: Truck, sample_hazmat_orders: list[Order]):
        """Test that multiple hazmat orders on the same lane can be combined."""
        request = OptimizeRequest(truck=sample_truck, orders=sample_hazmat_orders)
        result = optimize_load(request)

        # If both hazmat orders fit, they should be combined
        total_weight = sum(o.weight_lbs for o in sample_hazmat_orders)
        total_volume = sum(o.volume_cuft for o in sample_hazmat_orders)
        
        if total_weight <= sample_truck.max_weight_lbs and total_volume <= sample_truck.max_volume_cuft:
            assert len(result.selected_order_ids) == len(sample_hazmat_orders)

    def test_optimize_chooses_best_group(self, sample_truck: Truck):
        """Test optimizer chooses the best group when multiple lanes exist."""
        today = date.today()
        orders = [
            # Low payout lane
            Order(
                id="LOW-1",
                payout_cents=50000,
                weight_lbs=10000,
                volume_cuft=500,
                origin="Chicago, IL",
                destination="Dallas, TX",
                pickup_date=today,
                delivery_date=today + timedelta(days=2),
                is_hazmat=False
            ),
            # High payout lane
            Order(
                id="HIGH-1",
                payout_cents=300000,
                weight_lbs=20000,
                volume_cuft=1000,
                origin="New York, NY",
                destination="Los Angeles, CA",
                pickup_date=today,
                delivery_date=today + timedelta(days=5),
                is_hazmat=False
            ),
        ]
        
        request = OptimizeRequest(truck=sample_truck, orders=orders)
        result = optimize_load(request)

        # Should choose the higher payout order
        assert "HIGH-1" in result.selected_order_ids
        assert result.total_payout_cents == 300000


class TestOptimizerServiceOrderGroup:
    """Test cases for order grouping logic."""

    def test_group_by_lane_and_hazmat(self, sample_truck: Truck):
        """Test that orders are grouped correctly by lane and hazmat status."""
        today = date.today()
        orders = [
            Order(id="A1", payout_cents=100000, weight_lbs=5000, volume_cuft=200,
                  origin="A", destination="B", pickup_date=today, delivery_date=today + timedelta(days=1), is_hazmat=False),
            Order(id="A2", payout_cents=100000, weight_lbs=5000, volume_cuft=200,
                  origin="A", destination="B", pickup_date=today, delivery_date=today + timedelta(days=1), is_hazmat=False),
            Order(id="A3", payout_cents=100000, weight_lbs=5000, volume_cuft=200,
                  origin="A", destination="B", pickup_date=today, delivery_date=today + timedelta(days=1), is_hazmat=True),
            Order(id="B1", payout_cents=100000, weight_lbs=5000, volume_cuft=200,
                  origin="C", destination="D", pickup_date=today, delivery_date=today + timedelta(days=1), is_hazmat=False),
        ]
        
        request = OptimizeRequest(truck=sample_truck, orders=orders)
        optimizer = OptimizerService(request)
        groups = optimizer._group_compatible_orders()
        
        # Should have 3 groups:
        # 1. A->B non-hazmat (A1, A2)
        # 2. A->B hazmat (A3)
        # 3. C->D non-hazmat (B1)
        assert len(groups) == 3


class TestOptimizeLoadFunction:
    """Test cases for the optimize_load convenience function."""

    def test_optimize_load_returns_response(self, sample_request: OptimizeRequest):
        """Test that optimize_load returns a valid OptimizeResponse."""
        result = optimize_load(sample_request)
        
        assert result.truck_id == sample_request.truck.id
        assert isinstance(result.selected_order_ids, list)
        assert isinstance(result.total_payout_cents, int)
        assert isinstance(result.total_weight_lbs, int)
        assert isinstance(result.total_volume_cuft, int)
        assert isinstance(result.utilization_weight_percent, float)
        assert isinstance(result.utilization_volume_percent, float)
