"""FastAPI server."""

from typing import Any, Dict, List, Optional

try:
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
    FASTAPI_AVAILABLE = True
except ImportError:  # optional extra: pip install ncp[api]
    FASTAPI_AVAILABLE = False

    class BaseModel:  # minimal stand-in so module-level classes still define
        pass

    class HTTPException(Exception):
        def __init__(self, status_code: int = 500, detail: str = ""):
            super().__init__(detail)
            self.status_code = status_code
            self.detail = detail

    class FastAPI:
        """Import-safe stand-in: route decorators are no-ops; serving raises."""

        def __init__(self, *args, **kwargs):
            pass

        def _decorator(self, *args, **kwargs):
            def wrap(fn):
                return fn
            return wrap

        get = post = put = delete = on_event = _decorator

from ncp.core.entities import Goal
from ncp.runtime.container import Container
from ncp.runtime.runtime import Runtime
from ncp.utils.config import Config

app = FastAPI(title="NCP API", version="0.1.0")

runtime: Optional[Runtime] = None


class GoalRequest(BaseModel):
    name: str
    description: str = ""


class GoalResponse(BaseModel):
    status: str
    results: List[Dict[str, Any]]


class StatsResponse(BaseModel):
    status: str
    tasks_processed: int
    tasks_failed: int
    uptime_seconds: float


def create_app(config: Config) -> FastAPI:
    """Create FastAPI app with config."""
    global runtime
    if not FASTAPI_AVAILABLE:
        raise ImportError("FastAPI is not installed; install the [api] extra: pip install ncp[api]")
    container = Container(config=config).build()
    runtime = container.get_runtime()
    runtime.initialize()
    return app


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/goals", response_model=GoalResponse)
def execute_goal(request: GoalRequest):
    if not runtime:
        raise HTTPException(status_code=503, detail="Runtime not initialized")

    goal = Goal(name=request.name, description=request.description)
    results = runtime.execute_goal(goal)

    return GoalResponse(
        status="success",
        results=[r.to_dict() for r in results],
    )


@app.get("/stats", response_model=StatsResponse)
def get_stats():
    if not runtime:
        raise HTTPException(status_code=503, detail="Runtime not initialized")

    state = runtime.state
    return StatsResponse(
        status=state.status.name,
        tasks_processed=state.tasks_processed,
        tasks_failed=state.tasks_failed,
        uptime_seconds=state.uptime_seconds,
    )


@app.on_event("shutdown")
def shutdown():
    if runtime:
        runtime.shutdown()
