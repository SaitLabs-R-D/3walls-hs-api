from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError, HTTPException
from fastapi.responses import JSONResponse
from helpers.exceptions.redirect import RedirectException
from helpers.env import EnvVars
from api import v2

app = FastAPI(
    title="API",
    include_in_schema=not EnvVars.is_production,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    swagger_ui_parameters={"defaultModelsExpandDepth": 0},
)

from fastapi.middleware.cors import CORSMiddleware

origins = [EnvVars.SITE_URL]

if isinstance(EnvVars.CORS_ORIGINS, list):
    origins.extend(EnvVars.CORS_ORIGINS)
else:
    if EnvVars.CORS_ORIGINS:
        origins.extend(EnvVars.CORS_ORIGINS)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(v2.router, prefix="/api/v2")


@app.exception_handler(HTTPException)
def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail,
        headers=exc.headers,
    )


@app.exception_handler(RedirectException)
def handle_redirect_exception(request: Request, exc: RedirectException):
    """
    handle redirect exceptions by returning a json response with the route to redirect to
    """
    response = JSONResponse(
        status_code=exc.status_code, content={"route": exc.url, "data": exc.data}
    )

    for cookie in exc.remove_cookies:
        response.delete_cookie(cookie, domain=EnvVars.COOKIE_DOMAIN)

    return response


@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "message": "Validation Error",
            "content": exc.errors(),
            "success": False,
        },
    )


if __name__ == "__main__":

    # from db import migrations

    # migrations.add_lesson_part_type_and_gcp_path_for_draft_lessons()
    # migrations.add_lesson_part_type_and_gcp_path_for_published_lessons()
    # migrations.add_lesson_part_type_and_gcp_path_for_archive_lessons()

    if EnvVars.is_production:
        print("Running in production mode")

    # Things that should only run in the cloud
    if not EnvVars.IS_LOCAL:
        from services.cron import create_all_cron_tesks

        create_all_cron_tesks()

    import uvicorn

    import db
    from db import create_db

    # db.create_all_indexes()
    # create_db.create_all_roles()

    uvicorn.run(
        app="main:app",
        host="0.0.0.0",
        port=EnvVars.PORT,
        log_level="debug",
        reload=True,
    )
