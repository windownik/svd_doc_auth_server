import datetime
import hashlib

from fastapi_asyncpg import configure_asyncpg
from app_init import app
from fastapi import Depends

# Создаем новую таблицу
data_b = configure_asyncpg(app, 'postgres://postgres:102015@localhost:5432/svd_api')


async def create_all_users_table(db):
    await db.execute(f'''CREATE TABLE IF NOT EXISTS all_users (
 id SERIAL PRIMARY KEY,
 phone BIGINT UNIQUE DEFAULT 0,
 email TEXT DEFAULT '0',
 name TEXT DEFAULT '0',
 surname TEXT DEFAULT '0',
 status TEXT DEFAULT '0',
 password_hash TEXT DEFAULT 'active',
 last_active timestamp,
 create_date timestamp)''')


# Создаем новую таблицу
async def create_token_table(db):
    await db.execute(f'''CREATE TABLE IF NOT EXISTS token (
 id SERIAL PRIMARY KEY,
 user_id BIGINT DEFAULT 0,
 token TEXT DEFAULT '0',
 token_type TEXT DEFAULT 'access',
 change_password INTEGER DEFAULT 0,
 create_date timestamp,
 death_date timestamp
 )''')


# Создаем новую таблицу
async def create_user(db: Depends, phone, email, name, surname, status, password_hash):
    last_active = datetime.datetime.now()
    user_id = await db.fetch(f"INSERT INTO all_users (phone, email, name, surname, status, password_hash, last_active, "
                             f"create_date) "
                             f"VALUES ($1, $2, $3, $4, $5, $6, $7, $8) "
                             f"ON CONFLICT DO NOTHING RETURNING id;", phone, email, name, surname, status,
                             password_hash,
                             last_active, last_active)
    return user_id


# Создаем новую таблицу
async def create_token(db: Depends, user_id, token_type):
    create_date = datetime.datetime.now()
    if token_type == 'access':
        death_date = create_date + datetime.timedelta(minutes=30)
    else:
        death_date = create_date + datetime.timedelta(days=30)
    now = datetime.datetime.now()
    token = hashlib.shake_256(f"{now}".encode('utf-8'))
    await db.execute(f"INSERT INTO token (user_id, token, token_type, create_date, death_date) "
                     f"VALUES ($1, $2, $3, $4) "
                     f"ON CONFLICT DO NOTHING];", user_id, token, token_type,
                     create_date, death_date)
    return token


# Создаем новую таблицу
async def read_data(db: Depends, table: str, id_name: str, id_data, name: str):
    data = await db.fetch(f"SELECT {name} FROM {table} WHERE {id_name} = $1;", id_data)
    return data


# Создаем новую таблицу
async def read_data_2_were(db: Depends, table: str, id_name1: str, id_name2: str, id_data1, id_data2, name: str):
    data = await db.fetch(f"SELECT {name} FROM {table} WHERE {id_name1} = $1 AND  {id_name2} = $1;", id_data1, id_data2)
    return data


# Создаем новую таблицу
async def get_token(db: Depends, token_type: str, token: str):
    create_date = datetime.datetime.now()
    if token_type == 'access':
        death_date = create_date + datetime.timedelta(minutes=30)
    else:
        death_date = create_date + datetime.timedelta(days=30)
    data = await db.fetch(f"SELECT user_id FROM token "
                          f"WHERE token_type = $1 "
                          f"AND token = $2 "
                          f"AND death_date > $3 "
                          f"AND change_password = 0;",
                          token_type, token, death_date)
    return data
