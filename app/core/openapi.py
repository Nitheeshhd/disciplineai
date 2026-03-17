from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


def build_custom_openapi(app: FastAPI):
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        openapi_schema = get_openapi(
            title="DisciplineAI Enterprise API",
            version="2.0.0",
            description=(
                "Enterprise SaaS Analytics platform for Telegram bot productivity, "
                "behavioral insights, and operational intelligence."
            ),
            routes=app.routes,
        )
        openapi_schema["components"]["securitySchemes"] = {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
            }
        }
        openapi_schema["security"] = [{"BearerAuth": []}]
        openapi_schema["info"]["x-logo"] = {"url": "https://dummyimage.com/300x80/18c987/ffffff&text=DisciplineAI"}
        app.openapi_schema = openapi_schema
        return app.openapi_schema

    return custom_openapi
