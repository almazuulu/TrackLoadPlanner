from fastapi import APIRouter, HTTPException, status

from app.core.config import settings
from app.models.request import OptimizeRequest
from app.models.response import OptimizeResponse
from app.services.optimizer import optimize_load

router = APIRouter(prefix="/load-optimizer", tags=["Load Optimizer"])


@router.post(
    "/optimize",
    response_model=OptimizeResponse,
    status_code=status.HTTP_200_OK,
    summary="Optimize Truck Load",
    description="Find the optimal combination of orders to maximize carrier revenue "
                "while respecting weight, volume, hazmat, and route constraints.",
    responses={
        200: {
            "description": "Successful optimization (may return empty selection if no feasible combination)",
            "model": OptimizeResponse
        },
        400: {
            "description": "Invalid input data or validation error"
        },
        413: {
            "description": "Too many orders in request"
        }
    }
)
async def optimize(request: OptimizeRequest) -> OptimizeResponse:
    """Optimize truck load to maximize payout.
    
    This endpoint accepts a truck with capacity constraints and a list of orders,
    then finds the optimal combination of orders to maximize carrier revenue
    """
    # Check order count limit
    if len(request.orders) > settings.max_orders_per_request:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Too many orders. Maximum allowed: {settings.max_orders_per_request}, "
                   f"received: {len(request.orders)}"
        )
    
    # Run optimization
    result = optimize_load(request)
    
    return result
