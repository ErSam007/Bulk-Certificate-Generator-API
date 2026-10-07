from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.database import engine, Base
from app.router import router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Bulk Certificate Generator API",
    description="Scalable background certificate generator with relational tracking, status reporting, and bulk download.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

static_dir = Path(__file__).resolve().parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

app.include_router(router)

@app.get("/", include_in_schema=False)
def serve_index():
    index_file = static_dir / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {
        "service": "Bulk Certificate Generator API",
        "documentation": "/docs"
    }
