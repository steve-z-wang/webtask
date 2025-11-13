
from pydantic import BaseModel, Field
from typing import Optional


class SelectorResponse(BaseModel):

    element_id: Optional[str] = Field(None, description="Matching element ID")
    error: Optional[str] = Field(None, description="Error if no match found")
