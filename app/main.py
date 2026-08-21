"""FastAPI entry point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse

from app import __version__
from app.api import approvals, auth, evaluations, executions, projects, requirements, workflows
from app.dependencies import get_container
from app.observability.tracing import configure_tracing


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    get_container()
    configure_tracing()
    yield


app = FastAPI(
    title="Agentic Quality Engineering Platform",
    version=__version__,
    description="Human-governed multi-agent QE workflow with deterministic gates.",
    lifespan=lifespan,
)


@app.exception_handler(PermissionError)
def permission_denied(_: Request, exc: PermissionError) -> JSONResponse:
    return JSONResponse(status_code=403, content={"detail": str(exc)})


for router in (
    auth.router,
    projects.router,
    requirements.router,
    workflows.router,
    approvals.router,
    executions.router,
    evaluations.router,
):
    app.include_router(router, prefix="/api/v1")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy", "version": __version__}


@app.get("/", response_class=HTMLResponse)
def dashboard() -> str:
    return """<!doctype html><html lang='en'><head><meta charset='utf-8'>
<meta name='viewport' content='width=device-width,initial-scale=1'>
<title>Agentic QE Platform</title><style>
:root{color-scheme:dark;--bg:#08111f;--card:#111f33;--accent:#36d399;--text:#e6eef8;--muted:#9eb0c6}
*{box-sizing:border-box}body{margin:0;font:16px system-ui;background:linear-gradient(135deg,#08111f,#102642);color:var(--text)}
main{max-width:1100px;margin:auto;padding:48px 24px}header{display:flex;justify-content:space-between;align-items:center}
.pill{color:#06150f;background:var(--accent);padding:8px 14px;border-radius:999px;font-weight:700}
h1{font-size:clamp(2rem,5vw,4rem);max-width:850px;line-height:1.05;margin:64px 0 18px}
.lead{color:var(--muted);max-width:760px;font-size:1.15rem}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px;margin-top:42px}
.card{background:color-mix(in srgb,var(--card) 88%,transparent);border:1px solid #29415f;padding:22px;border-radius:16px}
.card b{color:var(--accent);font-size:1.4rem}.flow{margin-top:36px;padding:18px;border-left:3px solid var(--accent);color:var(--muted)}
a{color:var(--accent)}</style></head><body><main><header><strong>AQE // Reference Platform</strong><span class='pill'>Human Governed</span></header>
<h1>Agentic AI across the quality engineering lifecycle.</h1><p class='lead'>Specialised agents propose. Deterministic gates verify. Humans approve. Every decision retains evidence.</p>
<section class='grid'><div class='card'><b>9</b><p>Specialised QE agents</p></div><div class='card'><b>100%</b><p>Required traceability gate</p></div><div class='card'><b>0</b><p>Paid APIs required offline</p></div><div class='card'><b>2</b><p>Human approval gates</p></div></section>
<div class='flow'>Requirement → Risk → Test Design → Coverage → Regression → Automation → Approval → Execution → Triage → Release</div>
<p>Explore <a href='/docs'>OpenAPI</a> or run the password-reset demonstration.</p></main></body></html>"""
