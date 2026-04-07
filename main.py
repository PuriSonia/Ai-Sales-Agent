from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.chat import router as chat_router
from routes.auth import router as auth_router
from learning import init

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

init()

app.include_router(chat_router)
app.include_router(auth_router)

@app.get("/")
def root():
    return {"status": "AI Sales backend is running"}
