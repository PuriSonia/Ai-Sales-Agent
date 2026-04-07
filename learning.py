import os
import psycopg2

DATABASE_URL = os.getenv("DATABASE_URL")

def get_conn():
    return psycopg2.connect(DATABASE_URL)

def init():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS learning (
        id SERIAL PRIMARY KEY,
        input TEXT,
        reply TEXT,
        score INT
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        email TEXT,
        password TEXT
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS leads (
        id SERIAL PRIMARY KEY,
        email TEXT,
        website TEXT,
        message TEXT,
        status TEXT DEFAULT 'new',
        opened BOOLEAN DEFAULT FALSE,
        replied BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.commit()
    conn.close()

def save_learning(e):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO learning (input,reply,score) VALUES (%s,%s,%s)",
        (e["input"], e["reply"], e["score"])
    )
    conn.commit()
    conn.close()

def best(n=5):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT input, reply, score FROM learning ORDER BY score DESC LIMIT %s", (n,))
    rows = cur.fetchall()
    conn.close()
    return rows

def save_lead(email, website, message, status="new"):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO leads (email, website, message, status) VALUES (%s,%s,%s,%s) RETURNING id",
        (email, website, message, status)
    )
    lead_id = cur.fetchone()[0]
    conn.commit()
    conn.close()
    return lead_id

def list_leads():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, email, website, message, status, opened, replied, created_at FROM leads ORDER BY id DESC"
    )
    rows = cur.fetchall()
    conn.close()
    return rows

def update_lead_opened(lead_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE leads SET opened=TRUE WHERE id=%s", (lead_id,))
    conn.commit()
    conn.close()

def update_lead_replied(lead_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE leads SET replied=TRUE, status='replied' WHERE id=%s", (lead_id,))
    conn.commit()
    conn.close()

def update_lead_status(lead_id, status):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE leads SET status=%s WHERE id=%s", (status, lead_id))
    conn.commit()
    conn.close()
