"""Response models for the Load Optimizer API."""

from typing import List

from pydantic import BaseModel, Field


class OptimizeResponse(BaseModel):
    """Response model for the load optimization endpoint."""

    truck_id: str = Field(..., description="ID of the truck used for optimization")
    selected_order_ids: List[str] = Field(
        default_factory=list,
        description="List of selected order IDs"
    )
    total_payout_cents: int = Field(
        default=0,
        ge=0,
        description="Total payout in cents for selected orders"
    )
    total_weight_lbs: int = Field(
        default=0,
        ge=0,
        description="Total weight in pounds for selected orders"
    )
    total_volume_cuft: int = Field(
        default=0,
        ge=0,
        description="Total volume in cubic feet for selected orders"
    )
    utilization_weight_percent: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Weight utilization percentage"
    )
    utilization_volume_percent: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Volume utilization percentage"
    )


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""

    status: str = Field(default="healthy", description="Health status")
    service: str = Field(default="truck-load-planner", description="Service name")
    version: str = Field(..., description="API version")
