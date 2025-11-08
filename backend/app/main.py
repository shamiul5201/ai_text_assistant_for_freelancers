from fastapi import FastAPI
from app.routes import generate
from app.routes.auth import auth

app = FastAPI(title="Text Assistant for freelancers")


app.include_router(generate.router, prefix="/api", tags=["Generate"])
app.include_router(auth.router, prefix="/api", tags=["Auth"])

@app.get("/")
def root():
    return {"message": "Text Assistant API is running"}