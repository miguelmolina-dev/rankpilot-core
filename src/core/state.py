import operator
from typing import Annotated, TypedDict, List
from src.core.schemas import Legal500Submission


class AgentState(TypedDict):
    """
    Represents the state of our agent for LangGraph.
    """
    # The main structured data we are extracting and building
    submission: Legal500Submission

    # Optional fields for tracking process
    messages: Annotated[list, operator.add]
    current_step: str
    errors: List[str]
