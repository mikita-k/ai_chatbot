"""
Stage 4: LangGraph Orchestration

Complete orchestration of all previous stages using LangGraph:
- Stage 1: RAG Chatbot (information retrieval)
- Stage 2: Admin Agent (approval workflow)
- Stage 3: Storage (persistent database)

Main exports:
- LangGraphOrchestrator: Main orchestrator class
- create_orchestrator: Factory function
- WorkflowState: TypedDict for workflow state
"""

from src.stage4.orchestrator import LangGraphOrchestrator, create_orchestrator
from src.stage4.graph import WorkflowState, create_orchestration_graph

__version__ = "1.0.0"

__all__ = [
    "LangGraphOrchestrator",
    "create_orchestrator",
    "WorkflowState",
    "create_orchestration_graph",
]

