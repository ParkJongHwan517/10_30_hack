from fastapi import FastAPI

from .models import HealthResponse
from .routers import decide, observe

app = FastAPI(title="버려도 돼?")
app.include_router(observe.router, prefix="/api")
app.include_router(decide.router, prefix="/api")


@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(ok=True)
