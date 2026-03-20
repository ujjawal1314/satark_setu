from pydantic import BaseModel, Field


class BorrowerActionRequest(BaseModel):
    reason: str = Field(default="Borrower risk exceeded monitoring threshold")
    performed_by: str = Field(default="portfolio_manager")


class InterventionSimulationRequest(BaseModel):
    borrower_id: str
    support_type: str = Field(default="RESTRUCTURE_REVIEW")
    expected_impact: float = Field(default=8.0)
