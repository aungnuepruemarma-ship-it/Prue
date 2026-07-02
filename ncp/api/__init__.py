"""NCP API — stdlib task protocol; the FastAPI server is an optional extra."""

from . import server
from .protocol import TaskRequest, TaskResponse, handle_request

__all__ = ["TaskRequest", "TaskResponse", "handle_request", "server"]
