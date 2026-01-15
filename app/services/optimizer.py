from dataclasses import dataclass
from typing import List, Tuple, Optional
from collections import defaultdict

from app.models.request import Order, Truck, OptimizeRequest
from app.models.response import OptimizeResponse


@dataclass
class OrderGroup:
    """Group of compatible orders for optimization."""
    
    orders: List[Order]
    is_hazmat: bool
    origin: str
    destination: str


class OptimizerService:
    """Service for optimizing truck load selection using bitmask DP."""
    
    def __init__(self, request: OptimizeRequest):
        """Initialize optimizer with request data.
        
        Args:
            request: The optimization request containing truck and orders.
        """
        self.truck = request.truck
        self.orders = request.orders
    
    def optimize(self) -> OptimizeResponse:
        """Find the optimal combination of orders to maximize payout.
        
        Returns:
            OptimizeResponse with selected orders and totals.
        """
        # Handle empty orders case
        if not self.orders:
            return self._create_response([], 0, 0, 0)
        
        # Group orders by compatibility (same lane, same hazmat status)
        order_groups = self._group_compatible_orders()
        
        # Find the best solution across all groups
        best_solution = self._find_best_solution(order_groups)
        
        return best_solution
    
    def _group_compatible_orders(self) -> List[OrderGroup]:
        """Group orders by compatibility: same origin/destination and hazmat status.
        
        Returns:
            List of OrderGroup objects, each containing compatible orders.
        """
        # Group by (origin, destination, is_hazmat)
        groups: dict = defaultdict(list)
        
        for order in self.orders:
            key = (order.origin, order.destination, order.is_hazmat)
            groups[key].append(order)
        
        return [
            OrderGroup(
                orders=orders,
                is_hazmat=key[2],
                origin=key[0],
                destination=key[1]
            )
            for key, orders in groups.items()
        ]
    
    def _find_best_solution(self, order_groups: List[OrderGroup]) -> OptimizeResponse:
        """Find the best solution across all compatible order groups.
        
        Args:
            order_groups: List of compatible order groups.
            
        Returns:
            The best OptimizeResponse across all groups.
        """
        best_payout = 0
        best_orders: List[Order] = []
        best_weight = 0
        best_volume = 0
        
        for group in order_groups:
            # Filter orders that individually fit in the truck
            feasible_orders = self._filter_feasible_orders(group.orders)
            
            if not feasible_orders:
                continue
            
            # Apply bitmask DP to find optimal subset
            selected_orders, payout, weight, volume = self._bitmask_dp(feasible_orders)
            
            if payout > best_payout:
                best_payout = payout
                best_orders = selected_orders
                best_weight = weight
                best_volume = volume
        
        return self._create_response(best_orders, best_payout, best_weight, best_volume)
    
    def _filter_feasible_orders(self, orders: List[Order]) -> List[Order]:
        """Filter out orders that individually exceed truck capacity.
        
        Args:
            orders: List of orders to filter.
            
        Returns:
            List of orders that individually fit in the truck.
        """
        return [
            order for order in orders
            if order.weight_lbs <= self.truck.max_weight_lbs
            and order.volume_cuft <= self.truck.max_volume_cuft
        ]
    
    def _check_time_window_compatibility(self, orders: List[Order]) -> bool:
        """Check if all orders have compatible time windows.
        
        For orders to be compatible, they must have overlapping or non-conflicting
        pickup and delivery windows.
        """
        if len(orders) <= 1:
            return True
        
        # For same-lane orders, check that pickup and delivery windows overlap
        # We need: max(pickup_dates) <= min(delivery_dates)
        max_pickup = max(order.pickup_date for order in orders)
        min_delivery = min(order.delivery_date for order in orders)
        
        return max_pickup <= min_delivery
    
    def _bitmask_dp(self, orders: List[Order]) -> Tuple[List[Order], int, int, int]:
        """Apply bitmask DP to find the optimal subset of orders.
        
        Uses bitmask dynamic programming where each bit represents whether
        an order is included in the selection. 
        Args:
            orders: List of feasible orders (each fits individually).
            
        Returns:
            Tuple of (selected_orders, total_payout, total_weight, total_volume).
        """
        n = len(orders)
        
        if n == 0:
            return [], 0, 0, 0
        
        best_payout = 0
        best_mask = 0
        best_weight = 0
        best_volume = 0
        
        max_weight = self.truck.max_weight_lbs
        max_volume = self.truck.max_volume_cuft
        
        # Iterate through all possible subsets (2^n combinations)
        for mask in range(1, 1 << n):
            # Calculate totals for this subset
            total_weight = 0
            total_volume = 0
            total_payout = 0
            selected = []
            
            for i in range(n):
                if mask & (1 << i):
                    order = orders[i]
                    total_weight += order.weight_lbs
                    total_volume += order.volume_cuft
                    total_payout += order.payout_cents
                    selected.append(order)
            
            # Early pruning: skip if exceeds capacity
            if total_weight > max_weight or total_volume > max_volume:
                continue
            
            # Check time window compatibility for selected orders
            if not self._check_time_window_compatibility(selected):
                continue
            
            # Update best if this is a better solution
            if total_payout > best_payout:
                best_payout = total_payout
                best_mask = mask
                best_weight = total_weight
                best_volume = total_volume
        
        # Reconstruct selected orders from best mask
        selected_orders = [
            orders[i] for i in range(n)
            if best_mask & (1 << i)
        ]
        
        return selected_orders, best_payout, best_weight, best_volume
    
    def _create_response(
        self,
        selected_orders: List[Order],
        total_payout: int,
        total_weight: int,
        total_volume: int
    ) -> OptimizeResponse:
        """Create an OptimizeResponse from the optimization results.
        
        Args:
            selected_orders: List of selected Order objects.
            total_payout: Total payout in cents.
            total_weight: Total weight in pounds.
            total_volume: Total volume in cubic feet.
            
        Returns:
            OptimizeResponse with all computed values.
        """
        # Calculate utilization percentages
        weight_util = (total_weight / self.truck.max_weight_lbs * 100) if total_weight > 0 else 0.0
        volume_util = (total_volume / self.truck.max_volume_cuft * 100) if total_volume > 0 else 0.0
        
        return OptimizeResponse(
            truck_id=self.truck.id,
            selected_order_ids=[order.id for order in selected_orders],
            total_payout_cents=total_payout,
            total_weight_lbs=total_weight,
            total_volume_cuft=total_volume,
            utilization_weight_percent=round(weight_util, 2),
            utilization_volume_percent=round(volume_util, 2)
        )


def optimize_load(request: OptimizeRequest) -> OptimizeResponse:
    """Convenience function to optimize a load request.
    
    Args:
        request: The optimization request.
        
    Returns:
        OptimizeResponse with the optimal solution.
    """
    optimizer = OptimizerService(request)
    return optimizer.optimize()
