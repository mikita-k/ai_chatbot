"""
Stage 4: LangGraph Core Graph Definition

Defines the state schema, node definitions, and conditional routing for the complete
parking reservation workflow orchestration. Combines:
- Stage 1: RAG Chatbot (answers info queries)
- Stage 2: Admin Agent (handles approvals)
- Stage 3: Storage (persists approved reservations)
"""

from typing import Literal, Optional, TypedDict, List, Any, Dict
from datetime import datetime
import uuid
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from langgraph.graph import StateGraph, START, END

from src.stage1.rag_chatbot import DocumentStore, SimpleRAGChatbot
from src.stage2.chatbot_with_approval import Stage2Chatbot
from src.stage2.admin_agent import AdminAgent
from src.stage3.storage import ReservationStorage


# ============================================================================
# STATE SCHEMA - Typed state for the workflow
# ============================================================================

class UserInput(TypedDict, total=False):
    """User input to the system"""
    user_id: str  # Unique user identifier
    message: str  # User's input message
    timestamp: str  # When the user submitted the request


class RAGResponse(TypedDict, total=False):
    """Response from RAG chatbot"""
    answer: str  # The answer from RAG
    sources: List[str]  # Source documents used
    confidence: float  # Confidence score


class ReservationDetails(TypedDict, total=False):
    """Parking reservation details"""
    request_id: str  # Unique request ID
    name: str  # User's name
    surname: str  # User's surname
    car_number: str  # Vehicle registration
    period: str  # Period (e.g., "2026-02-26 10:00 - 2026-02-26 12:00")
    start_date: str  # Start date (e.g., "2026-02-26")
    end_date: str  # End date (e.g., "2026-02-26")


class ApprovalResult(TypedDict, total=False):
    """Admin approval decision"""
    status: str  # "approved" or "rejected"
    admin_feedback: str  # Admin's comment
    response_time: str  # When admin responded


class WorkflowState(TypedDict, total=False):
    """
    Complete state for the LangGraph workflow.

    Tracks all information through the workflow pipeline.
    """
    # Input
    user_input: UserInput

    # Classification
    request_type: Literal["info", "reservation", "status_check", "unknown"]

    # RAG response (for info requests)
    rag_response: Optional[RAGResponse]

    # Reservation details (for reservation requests)
    reservation_details: Optional[ReservationDetails]

    # Status check (for status_check requests)
    request_id_lookup: Optional[str]  # Request ID to look up

    # Admin approval (for reservation requests)
    approval_result: Optional[ApprovalResult]

    # Storage result
    storage_success: bool
    storage_message: str

    # Final response to user
    final_response: str

    # Metadata & error handling
    request_id: str  # Unique workflow ID
    errors: List[str]  # Any errors encountered
    state_history: List[str]  # Track which nodes were visited


# ============================================================================
# GRAPH BUILDER FUNCTION
# ============================================================================

def build_orchestration_graph(
    use_llm: bool = False,
    use_telegram: bool = False,
    llm: Optional[Any] = None,
) -> tuple:
    """
    Build the complete LangGraph orchestration graph.

    The graph has the following structure:

    ```
    START
      ↓
    [Router Node] - Classify request type
      ├─→ INFO REQUEST
      │     ↓
      │   [RAG Node] - Answer using RAG
      │     ↓
      │   [Response Node] - Send to user
      │     ↓
      │    END
      │
      └─→ RESERVATION REQUEST
            ↓
          [Collection Node] - Gather reservation details (interactive)
            ↓
          [Approval Node] - Submit to admin + wait for decision
            ↓
          [Storage Node] - Save approved reservations to DB
            ↓
          [Response Node] - Send outcome to user
            ↓
            END
    ```

    Args:
        use_llm: Whether to use OpenAI LLM for better answers
        use_telegram: Whether to use Telegram for admin notifications

    Returns:
        tuple: (StateGraph, AdminAgent) - The graph and admin agent for resource cleanup
    """

    # Initialize Stage 2 Chatbot (which internally uses Stage 1)
    # This gives us both RAG and Admin functionality
    doc_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "static_docs.txt")
    doc_path = os.path.abspath(doc_path)

    if os.path.exists(doc_path):
        doc_store = DocumentStore.from_file(doc_path, db_path="./faiss_db")
    else:
        # Fallback to sample docs if file not found
        sample_docs = [
            "Parking is available 24/7",
            "Hourly rate: $2 per hour. Daily maximum: $20",
            "Location: 123 Main Street",
            "Reservation process: provide name, surname, car number, period",
        ]
        doc_store = DocumentStore(docs=sample_docs, db_path="./faiss_db")

    # Create Stage 2 Chatbot (includes Stage 1 RAG + Admin Agent)
    stage2_chatbot = Stage2Chatbot(doc_store, use_telegram=use_telegram, use_llm=use_llm)
    admin_agent = stage2_chatbot.admin_agent  # Get the admin agent from Stage 2

    # Initialize Stage 3: Storage
    storage = ReservationStorage()

    # Create the graph
    graph = StateGraph(WorkflowState)

    # ========================================================================
    # NODE DEFINITIONS
    # ========================================================================

    def node_initialize(state: WorkflowState) -> WorkflowState:
        """Initialize workflow state with default values"""
        if "request_id" not in state or not state["request_id"]:
            state["request_id"] = f"FLOW-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"
        if "errors" not in state:
            state["errors"] = []
        if "state_history" not in state:
            state["state_history"] = []

        state["state_history"].append("initialize")
        return state


    def node_router(state: WorkflowState) -> WorkflowState:
        """
        Route the request based on its type.
        Classifies user input into: info, reservation, or status_check.

        Simple priority:
        1. status_check - if contains: check, status, статус, проверь
        2. reservation - if contains: reserve, book, бронь, резерв
        3. info - everything else (any question/information request)
        """
        message = state.get("user_input", {}).get("message", "").lower().strip()
        state["state_history"].append("router")

        # 1. Check for status_check FIRST
        if any(keyword in message for keyword in ["status", "check", "pending", "approved", "rejected", "статус", "проверь", "проверка"]):
            state["request_type"] = "status_check"
            # Try to extract request ID from message (e.g., "REQ-20260225225539-001")
            import re
            match = re.search(r'(REQ-\d{14}-\d{3})', message)
            if match:
                state["request_id_lookup"] = match.group(1)

        # 2. Check for RESERVATION keywords
        elif any(keyword in message for keyword in ["reserve", "book", "reservation", "зарезервировать", "бронь", "резерв"]):
            state["request_type"] = "reservation"

        # 3. DEFAULT: Everything else is INFO (any question or information request)
        else:
            state["request_type"] = "info"

        return state


    def node_rag(state: WorkflowState) -> WorkflowState:
        """
        RAG Node: Answer information queries using Stage 2's RAG Chatbot (from Stage 1).
        """
        state["state_history"].append("rag")

        try:
            user_message = state.get("user_input", {}).get("message", "")

            # Get RAG response from Stage 2 (which uses Stage 1)
            answer = stage2_chatbot.answer_question(user_message)

            state["rag_response"] = {
                "answer": answer,
                "sources": [],  # Could extract from rag_chatbot if available
                "confidence": 0.8,
            }

            state["final_response"] = f"🤖 {answer}"

        except Exception as e:
            state["errors"].append(f"RAG error: {str(e)}")
            state["final_response"] = "Sorry, I couldn't retrieve information about that. Please try again."

        return state


    def node_status_check(state: WorkflowState) -> WorkflowState:
        """
        Status Check Node: Look up the status of a reservation request.
        Delegates to Stage2Chatbot to check request status.
        """
        state["state_history"].append("status_check")

        try:
            # Small delay to allow Telegram bot to process recent messages
            import time
            time.sleep(0.5)

            # Get request ID from router's extraction or ask user
            request_id = state.get("request_id_lookup", "")

            if not request_id:
                # If no ID extracted, try to extract from raw message
                message = state.get("user_input", {}).get("message", "")
                import re
                match = re.search(r'(REQ-\d{14}-\d{3})', message)
                if match:
                    request_id = match.group(1)

            if not request_id:
                state["final_response"] = (
                    "❌ I couldn't find a request ID. "
                    "Please provide a request ID like: 'status REQ-20260225225539-001'"
                )
                return state

            # Check status using Stage2Chatbot (which uses admin_agent internally)
            status_info = stage2_chatbot.check_request_status(request_id)

            # Format response
            if status_info.get("status") == "not_found":
                state["final_response"] = f"❌ Request {request_id} not found. Please check the ID and try again."
            else:
                status = status_info.get("status", "unknown").upper()
                approved = status_info.get("approved", False)
                reason = status_info.get("reason", "")

                response_parts = [
                    f"📋 **Request Status: {request_id}**",
                    f"Status: {status} {'✅' if approved else '❌'}",
                ]

                if reason:
                    response_parts.append(f"Details: {reason}")

                if status_info.get("response_time"):
                    response_parts.append(f"Response time: {status_info['response_time']}")

                state["final_response"] = "\n".join(response_parts)

        except Exception as e:
            state["errors"].append(f"Status check error: {str(e)}")
            state["final_response"] = f"Error checking status: {str(e)}"

        return state


    def node_collection(state: WorkflowState) -> WorkflowState:
        """
        Collection Node: Parse reservation details from user input.
        Delegates to Stage2Chatbot - no duplication of parsing logic.
        """
        state["state_history"].append("collection")

        try:
            user_message = state.get("user_input", {}).get("message", "").strip()

            # Use Stage2's parser directly
            from src.stage2.reservation_parser import parse_reservation
            parsed = parse_reservation(user_message)

            if not parsed:
                # Parsing failed - set error message and return
                state["errors"].append("Collection: Could not parse reservation")
                state["final_response"] = (
                    "❌ Could not parse reservation. Use format:\n"
                    "  reserve <Name> <Surname> <Car> <Dates>\n\n"
                    "Examples:\n"
                    "  • reserve John Smith ABC123 from 5 march to 12 march 2026\n"
                    "  • reserve Иван Петров RS1234 с 5 по 12 июля 2026"
                )
                return state

            # Success - store reservation details for approval node
            request_id = f"REQ-{datetime.now().strftime('%Y%m%d%H%M%S')}-001"
            period = parsed["period"]
            start_date = period.split(" ")[0]
            end_date = period.split(" - ")[1].split(" ")[0]

            state["reservation_details"] = {
                "request_id": request_id,
                "name": parsed["name"],
                "surname": parsed["surname"],
                "car_number": parsed["car_number"],
                "period": period,
                "start_date": start_date,
                "end_date": end_date,
            }

        except Exception as e:
            state["errors"].append(f"Collection error: {str(e)}")
            state["final_response"] = f"Error: {str(e)}"

        return state


    def node_approval(state: WorkflowState) -> WorkflowState:
        """
        Approval Node: Submit to admin and wait for approval.
        COMPLETELY DELEGATES to Stage2Chatbot - no reimplementation.
        This ensures Stage 4 behaves exactly like Stage 2.
        """
        state["state_history"].append("approval")

        try:
            if not state.get("reservation_details"):
                state["errors"].append("Approval error: No valid reservation details")
                state["approval_result"] = {
                    "status": "error",
                    "admin_feedback": "No reservation details available",
                    "response_time": datetime.now().isoformat(),
                }
                return state

            details = state.get("reservation_details", {})

            # Use Stage2Chatbot methods - complete delegation, no duplication
            result = stage2_chatbot.initiate_reservation(details)

            if not result.get("success"):
                state["errors"].append(f"Submission failed: {result['message']}")
                state["approval_result"] = {
                    "status": "error",
                    "admin_feedback": result['message'],
                    "response_time": datetime.now().isoformat(),
                }
                return state

            # Wait for approval using Stage2's exact same logic
            request_id = result["request_id"]
            status = stage2_chatbot.wait_for_approval(request_id, timeout_sec=2)

            state["approval_result"] = {
                "status": status.get("status", "pending"),
                "admin_feedback": status.get("reason", ""),
                "response_time": datetime.now().isoformat(),
            }

        except Exception as e:
            state["errors"].append(f"Approval error: {str(e)}")
            state["approval_result"] = {
                "status": "error",
                "admin_feedback": str(e),
                "response_time": datetime.now().isoformat(),
            }

        return state


    def node_storage(state: WorkflowState) -> WorkflowState:
        """
        Storage Node: Save approved reservations to database (Stage 3).
        Only saves if approval status is 'approved'.
        """
        state["state_history"].append("storage")

        state["storage_success"] = False
        state["storage_message"] = ""

        try:
            approval_status = state.get("approval_result", {}).get("status", "")

            if approval_status == "approved":
                details = state.get("reservation_details", {})

                reservation = {
                    "reservation_id": details.get("request_id", ""),
                    "user_name": f"{details.get('name', '')} {details.get('surname', '')}",
                    "car_number": details.get("car_number", ""),
                    "start_date": details.get("start_date", ""),
                    "end_date": details.get("end_date", ""),
                    "approval_time": state.get("approval_result", {}).get("response_time", ""),
                }

                # Save to database
                if storage.save(reservation):
                    state["storage_success"] = True
                    state["storage_message"] = f"✅ Reservation saved to database: {reservation.get('reservation_id')}"
                else:
                    state["storage_message"] = "⚠️ Could not save to database"

            elif approval_status == "rejected":
                state["storage_message"] = "⚠️ Reservation was rejected by admin, not saved"

            else:
                state["storage_message"] = "⚠️ Approval status unknown"

        except Exception as e:
            state["errors"].append(f"Storage error: {str(e)}")
            state["storage_message"] = f"❌ Storage error: {str(e)}"

        return state


    def node_response(state: WorkflowState) -> WorkflowState:
        """
        Response Node: Format final response to user.
        For reservations, response comes directly from Stage2Chatbot approval result.
        """
        state["state_history"].append("response")

        request_type = state.get("request_type", "unknown")

        if request_type == "info":
            # Info response already set by RAG node
            pass

        elif request_type == "reservation":
            # Check if there were errors during collection/approval
            if state.get("errors"):
                # Error message already set by collection node
                pass
            else:
                # Reservation submitted - will always be pending (2 sec timeout is too short)
                request_id = state.get("reservation_details", {}).get('request_id')
                state["final_response"] = (
                    f"✅ Reservation request submitted!\n"
                    f"Request ID: {request_id}\n"
                    f"Your request has been sent to the administrator for review.\n\n"
                    f"⏳ YOUR REQUEST IS PENDING ADMIN REVIEW\n"
                    f"   Request ID: {request_id}\n"
                    f"   Use 'status {request_id}' to check status anytime"
                )

        elif request_type == "status_check":
            # Status check response already set by status_check node
            pass

        else:  # unknown
            state["final_response"] = (
                "I didn't understand your request. Try:\n"
                "- Ask about parking info\n"
                "- 'reserve <Name> <Surname> <Car> <Dates>' to make a reservation"
            )

        return state


    def route_request(state: WorkflowState) -> str:
        """
        Conditional routing: Choose path based on request type.

        Returns: Next node name
        """
        request_type = state.get("request_type", "unknown")

        if request_type == "info":
            return "rag"
        elif request_type == "reservation":
            return "collection"
        elif request_type == "status_check":
            return "status_check"
        else:
            return "response"


    def route_after_approval(state: WorkflowState) -> str:
        """
        After approval, check if we should save to storage.

        Returns: Next node name
        """
        approval_status = state.get("approval_result", {}).get("status", "")

        if approval_status == "approved":
            return "storage"
        else:
            return "response"


    # Add nodes to graph
    graph.add_node("initialize", node_initialize)
    graph.add_node("router", node_router)
    graph.add_node("rag", node_rag)
    graph.add_node("status_check", node_status_check)
    graph.add_node("collection", node_collection)
    graph.add_node("approval", node_approval)
    graph.add_node("storage", node_storage)
    graph.add_node("response", node_response)

    # Add edges
    graph.add_edge(START, "initialize")
    graph.add_edge("initialize", "router")

    # Conditional routing after router
    graph.add_conditional_edges(
        "router",
        route_request,
        {
            "rag": "rag",
            "status_check": "status_check",
            "collection": "collection",
            "response": "response",
        }
    )

    # Info request path: RAG → Response → END
    graph.add_edge("rag", "response")

    # Status check path: Status Check → Response → END
    graph.add_edge("status_check", "response")

    # Reservation request path: Collection → Approval → (conditional) Storage → Response → END
    graph.add_edge("collection", "approval")
    graph.add_conditional_edges(
        "approval",
        route_after_approval,
        {
            "storage": "storage",
            "response": "response",
        }
    )
    graph.add_edge("storage", "response")

    # All paths end at response, then to END
    graph.add_edge("response", END)

    return graph, admin_agent


# ============================================================================
# COMPILED GRAPH CREATION
# ============================================================================

class GraphWithResources:
    """Wrapper for compiled graph that also stores resource references."""

    def __init__(self, compiled_graph: Any, admin_agent: Any = None):
        self.compiled_graph = compiled_graph
        self._admin_agent = admin_agent

    def invoke(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke the compiled graph."""
        return self.compiled_graph.invoke(state)

    def compile(self):
        """For compatibility - return self since already compiled."""
        return self

    def __getattr__(self, name: str):
        """Forward other attributes to compiled graph."""
        return getattr(self.compiled_graph, name)


def create_orchestration_graph(
    use_llm: bool = False,
    use_telegram: bool = False,
    llm: Optional[Any] = None,
) -> GraphWithResources:
    """
    Create and compile the orchestration graph.

    Args:
        use_llm: Whether to use OpenAI LLM
        use_telegram: Whether to use Telegram for admin notifications
        llm: Optional LangChain LLM instance

    Returns:
        GraphWithResources with compiled graph and admin_agent reference
    """
    # build_orchestration_graph now returns (graph, admin_agent)
    graph_builder, admin_agent = build_orchestration_graph(use_llm, use_telegram, llm)
    compiled = graph_builder.compile()

    # Return wrapper that contains both the compiled graph and admin_agent reference
    return GraphWithResources(compiled, admin_agent)

