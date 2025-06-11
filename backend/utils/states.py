# states.py
# New idea for more targeted information gathering and analysis

from __future__ import annotations
from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from datetime import date

class Source(BaseModel):
    url: str
    source_score: float  # 0–1 quality score
    extractor: str       # which agent / tool produced it


class Claim(BaseModel):
    claim: str
    attribution_score: float  # 0–1
    supporting_sources: List[Source]
    language: str


class AgentMeta(BaseModel):
    confidence_score: float | None = None
    source_count: int = 0
    source_quality_avg: float | None = None
    fallback_mode: bool = False
    error: Optional[str] = None


# background_state.py
from shared import AgentMeta, Source
class BackgroundData(BaseModel):
    executive_id: str
    name: str
    aliases: List[str] = []
    headline: Optional[str] = None
    current_role_title: Optional[str] = None
    current_org: Optional[str] = None
    current_start_date: Optional[date] = None
    # ...anything else used by downstream agents

class BackgroundState(AgentMeta):
    data: Optional[BackgroundData] = None
    sources: List[Source] = []


# leadership_state.py
from shared import AgentMeta, Claim, Source
class LeadershipImpact(BaseModel):
    metric: str
    value: str
    peer_delta: Optional[str] = None  # e.g. "+6 pp vs peers"
    claim: Claim

class LeadershipState(AgentMeta):
    impact_summary: Optional[str] = None
    business_impacts: List[LeadershipImpact] = []
    sources: List[Source] = []


# strategy_state.py
class StrategicMove(BaseModel):
    initiative: str
    year: int
    claim: Claim

class StrategyState(AgentMeta):
    strategic_moves: List[StrategicMove] = []
    sources: List[Source] = []


# reputation_state.py
class ReputationTrendPoint(BaseModel):
    month: date
    score: int  # 0-100

class ReputationState(AgentMeta):
    reputation_index: Optional[int] = None
    sentiment_trend: List[ReputationTrendPoint] = []
    notable_mentions: List[str] = []
    sources: List[Source] = []


# performance_state.py
class PerformanceMetric(BaseModel):
    type: str
    value: str
    note: Optional[str] = None
    claim: Optional[Claim] = None

class PerformanceState(AgentMeta):
    metrics: List[PerformanceMetric] = []
    sources: List[Source] = []


# network_state.py  (optional agent)
class Connection(BaseModel):
    person: str
    relationship: str  # board, co-founder, co-author, etc.
    since: Optional[int]

class NetworkState(AgentMeta):
    connections: List[Connection] = []
    centrality_score: Optional[float] = None
    sources: List[Source] = []


# main_state.py
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
import datetime as dt

class MainState(BaseModel):
    # --- root-level identifiers ------------
    executive_id: Optional[str] = None
    name: Optional[str] = None

    # --- high-level artefacts -------------
    profile_confidence: Optional[str] = None  # Gold / Silver / Bronze
    confidence_rationale: List[str] = []

    fallback_mode: bool = False
    profile_summary: Optional[str] = None
    last_updated: dt.datetime = Field(default_factory=dt.datetime.utcnow)

    # --- agent data blocks ----------------
    background: BackgroundState = Field(default_factory=BackgroundState)
    leadership: LeadershipState = Field(default_factory=LeadershipState)
    strategy: StrategyState = Field(default_factory=StrategyState)
    reputation: ReputationState = Field(default_factory=ReputationState)
    performance: PerformanceState = Field(default_factory=PerformanceState)
    network: NetworkState = Field(default_factory=NetworkState)

    # --- orchestration helpers ------------
    completed_agents: List[str] = []
    errors: Dict[str, str] = {}  # {agent_name: error}
