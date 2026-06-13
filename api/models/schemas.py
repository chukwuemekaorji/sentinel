# where we define the pydantic models for the API responses

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# this is the model for the account information that we will return in the API response
class AccountOut(BaseModel):
    id: str
    username: str
    follower_count: int
    following_count: int
    post_count: int
    risk_score: float
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# request body for updating an account's status
class StatusUpdate(BaseModel):
    status: str


# the model for the flag information in the API response
class FlagOut(BaseModel):
    id: int
    account_id: str
    source: str
    reason: str
    score: float
    created_at: datetime

    class Config:
        from_attributes = True
        

# the model for the graph information in the API response
class GraphNode(BaseModel):
    id: str
    risk_score: float
    status: str
    community: Optional[str] = None # which community the node belongs to, if any
    

class GraphEdge(BaseModel):
    source: str
    target: str
    weight: float
    

class GraphOut(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               