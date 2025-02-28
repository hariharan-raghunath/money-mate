from fastapi import FastAPI, HTTPException, Depends, status
import psycopg2
import psycopg2.extensions
import configparser
from passlib.context import CryptContext
import secrets
from datetime import datetime
import os
import json

app = FastAPI()

from logger import logger

logger = logger.setlogger()
# parser = argparse.ArgumentParser()
# parser.add_argument('--env', type=str, default='default')
# args = parser.parse_args()
#
# config_file_path = 'config/{0}.json'.format(args.env)

env = os.environ.get('APP_ENV', 'default')
config_file_path = f'config/{env}.json'
with open(config_file_path, 'r') as temp:
    config = json.load(temp)


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_db():
    global conn
    try:
        conn = psycopg2.connect(
            host=config['database']['host'],
            database=config['database']['database'],
            user=config['database']['user'],
            password=config['database']['password']
        )
        yield conn
    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        if conn:
            conn.close()


def read_query(filename):
    with open(f"queries/{filename}", "r") as f:
        return f.read()


@app.post("/users/")
def create_user(username: str, email: str, password: str, initial_balance: float = 0.0,
                db: psycopg2.extensions.connection = Depends(get_db)):
    try:
        cur = db.cursor()
        hashed_password = get_password_hash(password)
        query = read_query("create_user.sql")
        cur.execute(query, (username, email, hashed_password, initial_balance))
        user_id = cur.fetchone()[0]
        db.commit()
        cur.close()
        return {"id": user_id, "username": username, "email": email, "initial_balance": initial_balance}
    except psycopg2.Error as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Database error: {e}")


@app.post("/login/")
def login_for_access_token(email: str, password: str, db: psycopg2.extensions.connection = Depends(get_db)):
    try:
        cur = db.cursor()
        query = read_query("get_user_by_email.sql")
        cur.execute(query, (email,))
        user = cur.fetchone()
        cur.close()
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
        if not verify_password(password, user[1]):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
        token = secrets.token_hex(16)
        return {"access_token": token, "token_type": "bearer"}
    except psycopg2.Error as e:
        raise HTTPException(status_code=400, detail=f"Database error: {e}")


@app.post("/expenses/")
def create_expense(user_id: int, amount: float, category: str, description: str, date: datetime,
                   db: psycopg2.extensions.connection = Depends(get_db)):
    try:
        cur = db.cursor()
        query = read_query("create_expense.sql")
        cur.execute(query, (user_id, amount, category, description, date))
        expense_id = cur.fetchone()[0]
        db.commit()
        cur.close()
        return {"id": expense_id, "user_id": user_id, "amount": amount, "category": category,
                "description": description, "date": date}
    except psycopg2.Error as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Database error: {e}")


@app.get("/expenses/{expense_id}")
def read_expense(expense_id: int, db: psycopg2.extensions.connection = Depends(get_db)):
    try:
        cur = db.cursor()
        query = read_query("get_expense_by_id.sql")
        cur.execute(query, (expense_id,))
        expense = cur.fetchone()
        cur.close()
        if not expense:
            raise HTTPException(status_code=404, detail="Expense not found")
        return {"id": expense[0], "user_id": expense[1], "amount": expense[2], "category": expense[3],
                "description": expense[4], "date": expense[5]}
    except psycopg2.Error as e:
        raise HTTPException(status_code=400, detail=f"Database error: {e}")

