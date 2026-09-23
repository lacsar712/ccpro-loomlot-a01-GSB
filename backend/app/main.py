from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.routers import (
    auth,
    dye_houses,
    vats,
    dye_lots,
    fixation_windows,
    fabric_weights,
    fastness_checks,
    dashboard,
)

app = FastAPI(title="LoomLot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    messages = []
    for err in errors:
        loc = ".".join(str(x) for x in err.get("loc", []) if x != "body")
        msg = err.get("msg", "校验失败")
        if msg.startswith("Value error, "):
            msg = msg[len("Value error, ") :]
        messages.append(f"{loc}: {msg}" if loc else msg)
    detail = "; ".join(messages) if messages else "请求参数校验失败"
    return JSONResponse(status_code=400, content={"detail": detail})


app.include_router(auth.router)
app.include_router(dye_houses.router)
app.include_router(vats.router)
app.include_router(dye_lots.router)
app.include_router(fixation_windows.router)
app.include_router(fabric_weights.router)
app.include_router(fastness_checks.router)
app.include_router(dashboard.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "LoomLot"}
