from fastapi import FastAPI
from app.routes import generate, web_ui, admin
from app.routes.auth import auth
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Text Assistant for freelancers")


app.include_router(auth.router, prefix="/api", tags=["Auth"])
app.include_router(generate.router, prefix="/api", tags=["Generate"])
app.include_router(web_ui.router, tags=["Web UI"])
app.include_router(admin.router, tags=["Admin"])

app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/")
def root():
    return {"message": "Text Assistant API is running"}