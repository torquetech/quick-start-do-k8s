import os
import fastapi
import psycopg2
from datetime import datetime


app = fastapi.FastAPI()


def get_db_time():
    db_uri = os.environ.get("DB")
    db = psycopg2.connect(db_uri)
    cursor = db.cursor()
    cursor.execute("SELECT NOW();")
    return cursor.fetchone()[0]


@app.get("/backend-service2")
def api_endpoint():
    db_time = get_db_time()
    return f"Database time: {db_time.isoformat()}"
