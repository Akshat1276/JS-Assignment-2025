# backend/main.py
from fastapi import FastAPI
from db import get_db_connection

app = FastAPI()

@app.get("/")
def read_root():
    return {"msg": "LLM Chat Backend is running"}

@app.get("/db-test")
def db_test():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        result = cur.fetchone()
        cur.close()
        conn.close()
        return {"db_connection": "success", "result": result}
    except Exception as e:
        return {"db_connection": "failed", "error": str(e)}