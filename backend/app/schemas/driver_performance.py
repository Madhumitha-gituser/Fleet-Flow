from pydantic import BaseModel


class DriverPerformanceResponse(BaseModel):
    """Response schema for GET /drivers/{driver_id}/performance (Task 6).

    All values are calculated dynamically from the Trip table and are
    never stored in the database.
    """

    driver_id: int
    driver_name: str
    total_trips: int
    completed_trips: int
    active_trips: int
    cancelled_trips: int

    class Config:
        from_attributes = True
