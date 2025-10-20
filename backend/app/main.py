from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.logging import configure_logging
from app.api.v1.routes import api_router


def create_app() -> FastAPI:
	configure_logging()
	app = FastAPI(
		title="IR RAG Backend",
		version="0.1.0",
		default_response_class=ORJSONResponse,
	)
	app.add_middleware(
		CORSMiddleware,
		allow_origins=settings.cors_allow_origins,
		allow_credentials=True,
		allow_methods=["*"],
		allow_headers=["*"],
	)
	app.include_router(api_router, prefix="/api/v1")
	# serve templates for download (copied into /app/samples)
	app.mount("/samples", StaticFiles(directory="/app/samples/import_templates"), name="samples")
	return app


app = create_app()
