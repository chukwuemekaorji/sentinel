from fastapi import APIRouter, Depends
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from db.orm import Account
from models.schemas import GraphOut, GraphNode, GraphEdge

router = APIRouter()


@router.get("/", response_model=GraphOut)
async def get_graph(db: AsyncSession = Depends(get_db)):
    """
    builds a graph snapshot from recent interaction events
    returns nodes(accounts) and edges(interactions) in a format that
    d3 graph can take to render the force directed graph
    """
    
    # get all accounts as nodes
    result = await db.execute(select(Account))
    accounts = result.scalars().all()
    
    
    nodes = [
        GraphNode(
            id=a.id,
            risk_score=a.risk_score,
            status=a.status,
        )
        for a in accounts
    ]
    
    # get recent interactions as edges, last 5 mins
    edge_result = await db.execute(text("""
        SELECT account_id, target_id, COUNT(*) as weight
        FROM events
        WHERE target_id IS NOT NULL
        AND timestamp >= NOW() - INTERVAL '5 minutes'
        GROUP BY account_id, target_id
    """))
    
    edges = [
        GraphEdge(
            source=row.account_id,
            target=row.target_id,
            weight=float(row.weight),
        )
        for row in edge_result.fetchall()
    ]
    
    return GraphOut(nodes=nodes, edges=edges)