from sqlalchemy import (
    Column, String, Float, Integer,
    DateTime, ForeignKey, Text, JSON
)
from sqlalchemy.orm import  declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class Account(Base):
    __tablename__ = "accounts"
    
    id = Column(String, primary_key=True) # e.g "acc_4821"
    username = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    follower_count = Column(Integer, default=0)
    following_count = Column(Integer, default=0)
    post_count = Column(Integer, default=0)
    
    # this is the rolled up score across all flags for this account
    risk_score = Column(Float, default=0.0)
    
    # where the account sits in the investigation workflow
    status = Column(String, default="clean") # clean | flagged | reviewing | confirmed | dismissed
    
class Event(Base):
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, autoincrement=True) 
    account_id = Column(String, ForeignKey("accounts.id"), nullable=False)
    event_type = Column(String, nullable=False) # follow, unfollow, post, like
    target_id = Column(String, nullable=True) # the account being followed/ post being liked
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    event_metadata = Column("metadata", JSON, default=dict)
    
class Flag(Base):
    __tablename__ = "flags"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(String, ForeignKey("accounts.id"), nullable=False)
    
    # which detection layer caught this
    source = Column(String, nullable=False) # rule_engine | graph_analyzer | anomaly detector
    
    reason = Column(Text, nullable=False) # human readable explanation of why it was flagged
    score = Column(Float, nullable=False) # 0.0 - 1.0 score, higher meaning mre suspicious
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
class FeatureVector(Base):
    __tablename__ = "feature_vectors"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(String, ForeignKey("accounts.id"), nullable=False)
    
    # storing the raw vector so we can track how account behavior evolves over time
    features = Column(JSON, nullable=False)
    captured_at = Column(DateTime(timezone=True), server_default=func.now())
    
