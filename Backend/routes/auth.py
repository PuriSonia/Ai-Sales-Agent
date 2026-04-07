from fastapi import APIRouter
from pydantic import BaseModel
import jwt, os, psycopg2

router = APIRouter()
SECRET = os.getenv("JWT_SECRET", "change-me")

class User(BaseModel):
    email: str
    password: str

def conn():
    return psycopg2.connect(os.getenv("DATABASE_URL"))

@router.post("/signup")
def signup(u: User):
    c = conn()
    cur = c.cursor()
    cur.execute("INSERT INTO users (email,password) VALUES (%s,%s)", (u.email, u.password))
    c.commit()
    c.close()
    return {"msg": "ok"}

@router.post("/login")
def login(u: User):
    c = conn()
    cur = c.cursor()
    cur.execute("SELECT * FROM users WHERE email=%s AND password=%s", (u.email, u.password))
    r = cur.fetchone()
    c.close()
    if not r:
        return {"error": "bad"}
    token = jwt.encode({"email": u.email}, SECRET, algorithm="HS256")
    return {"token": token}
