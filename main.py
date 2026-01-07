# main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from feature1 import router as feature1_router
from feature2 import router as feature2_router 
from feature3 import router as feature3_router
from feature4 import router as feature4_router
from auth_router import router as auth_router

from db import init_db

app = FastAPI(title="IntelliAvatar API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for development
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database and tables
init_db()

# Include routers
app.include_router(auth_router)
app.include_router(feature1_router)
app.include_router(feature2_router)
app.include_router(feature3_router)
app.include_router(feature4_router)

