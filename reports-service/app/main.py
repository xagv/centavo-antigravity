from fastapi import FastAPI

from .db import Base, engine
from .routes import router

Base.metadata.create_all(engine)
app = FastAPI(title="Centavo reports-service")
app.include_router(router)
