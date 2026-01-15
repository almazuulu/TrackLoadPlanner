"""Request models for the Load Optimizer API."""

from datetime import date
from typing import List

from pydantic import BaseModel, Field, field_validator


class Truck(BaseModel):
    """Truck model representing the vehicle capacity constraints."""

    id: str = Field(..., description="Unique identifier for the truck")
    max_weight_lbs: int = Field(
        ..., gt=0, description="Maximum weight capacity in pounds"
    )
    max_volume_cuft: int = Field(
        ..., gt=0, description="Maximum volume capacity in cubic feet"
    )


class Order(BaseModel):
    """Order model representing a shipment to be loaded."""

    id: str = Field(..., description="Unique identifier for the order")
    payout_cents: int = Field(
        ..., ge=0, description="Payout to carrier in cents (integer only)"
    )
    weight_lbs: int = Field(..., gt=0, description="Weight of the order in pounds")
    volume_cuft: int = Field(
        ..., gt=0, description="Volume of the order in cubic feet"
    )
    origin: str = Field(..., min_length=1, description="Origin city and state")
    destination: str = Field(..., min_length=1, description="Destination city and state")
    pickup_date: date = Field(..., description="Pickup date for the order")
    delivery_date: date = Field(..., description="Delivery date for the order")
    is_hazmat: bool = Field(default=False, description="Whether the order contains hazardous materials")

    @field_validator("delivery_date")
    @classmethod
    def validate_delivery_after_pickup(cls, v: date, info) -> date:
        """Ensure delivery date is not before pickup date."""
        pickup_date = info.data.get("pickup_date")
        if pickup_date and v < pickup_date:
            raise ValueError("delivery_date must be on or after pickup_date")
        return v


class OptimizeRequest(BaseModel):
    """Request model for the load optimization endpoint."""

    truck: Truck = Field(..., description="Truck with capacity constraints")
    orders: List[Order] = Field(
        default_factory=list,
        description="List of orders to optimize"
    )

    @field_validator("orders")
    @classmethod
    def validate_orders_not_empty_ids(cls, v: List[Order]) -> List[Order]:
        """Validate that all order IDs are unique."""
        if v:
            order_ids = [order.id for order in v]
            if len(order_ids) != len(set(order_ids)):
                raise ValueError("All order IDs must be unique")
        return v
