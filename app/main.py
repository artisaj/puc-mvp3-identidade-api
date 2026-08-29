"""Ponto de entrada da aplicação FastAPI."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.auth import router as auth_router
from app.api.routes.health import router as health_router
from app.api.routes.sessions import router as sessions_router
from app.api.routes.users import router as users_router
from app.core.config import get_settings


def create_application() -> FastAPI:
	"""Cria e configura a instância principal da API."""
	settings = get_settings()
	application = FastAPI(title=settings.app_name)

	application.add_middleware(
		CORSMiddleware,
		allow_origins=settings.cors_origins_list,
		allow_credentials=True,
		allow_methods=["*"],
		allow_headers=["*"],
	)
	application.include_router(auth_router)
	application.include_router(health_router)
	application.include_router(users_router)
	application.include_router(sessions_router)

	return application


app = create_application()
