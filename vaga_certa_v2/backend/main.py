"""
Ponto de entrada principal da aplicação.
"""
import uvicorn
from config import settings

if __name__ == "__main__":
    # Quando reload=True, uvicorn precisa da app como string de importação
    if settings.environment == "development":
        uvicorn.run(
            "api.main:app",
            host=settings.api_host,
            port=settings.api_port,
            reload=True,
            log_level=settings.log_level.lower()
        )
    else:
        # Em produção, importamos diretamente
        from api.main import app
        uvicorn.run(
            app,
            host=settings.api_host,
            port=settings.api_port,
            log_level=settings.log_level.lower()
        )

