from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import psycopg2
from psycopg2 import OperationalError
from starlette.staticfiles import StaticFiles

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")


class SQLRequest(BaseModel):
    host: str
    port: int
    username: str
    password: str
    database: str
    sql_command: str


@app.get("/")
async def read_root():
    raise HTTPException(status_code=302, detail="Redirecting...", headers={"Location": "/static/index.html"})


@app.post("/perform_request/")
async def perform_request(params: SQLRequest):
    try:
        conn = psycopg2.connect(
            host=params.host,
            port=params.port,
            user=params.username,
            password=params.password,
            database=params.database,
            connect_timeout=3,
        )
        message = "Connection established."
    except OperationalError as e:
        if "could not connect to server" in str(e):
            return {"error": "Host is not reachable.", "details": str(e)}
        elif "password authentication failed" in str(e):
            return {"error": "Username or password is incorrect.", "details": str(e)}
        else:
            return {"error": "Connection failed.", "details": str(e)}

    try:
        cur = conn.cursor()
        cur.execute(params.sql_command)
        results = cur.fetchall()
        fields = [desc[0] for desc in cur.description]
        cur.close()
        return {"message": message, "sql_result": results, "fields": fields}
    except Exception as e:
        return {"error": "Failed to execute SQL command.", "details": str(e)}
    finally:
        conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
