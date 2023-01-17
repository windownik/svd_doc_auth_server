from hashlib import sha256

import asyncpg
import starlette.status as _status
import uvicorn
from fastapi import Depends
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse
from starlette.responses import Response

import sql_connect as conn
from response_examples import create_user_res, check_phone_res
from sql_connect import data_b, app


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Welcome to SVDdoc API",
        version="0.9",
        description="This is main API of project",
        routes=app.routes,
        tags=[{'name': 'System', 'description': "Checking login and password, as well as system settings."},
              {'name': 'Auth', 'description': "Auth user methods in server"},
              {'name': "User", 'description': "User's information. Checking login and password"}]
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


def generate_html_response():
    html_content = """
    <html>
        <head>
            <title>Start page</title>
        </head>
        <body>
            <h2>Documentation for Bot Admin API</h2>
            <p><a href="/docs">Documentation standart</a></p>
            <p><a href="/redoc">Documentation from reDoc</a></p>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=200)


@data_b.on_init
async def initialization(connect):
    # you can run your db initialization code here
    await connect.execute("SELECT 1")


@app.get('/', response_class=HTMLResponse, tags=['System'])
async def main_page():
    """main page"""
    return generate_html_response()


@app.get(path='/create_db', tags=['System'], )
async def init_database(db=Depends(data_b.connection)):
    """Here you can check your username and password"""
    await conn.create_all_users_table(db)
    await conn.create_token_table(db)
    return {"ok": True}


@app.get(path='/get_me', tags=['User'], responses=check_phone_res)
async def get_me(access_token: str, db=Depends(data_b.connection), ):
    """Here you can check your username and password. Get users information.
    access_token: This is access auth token. You can get it when create account, login or """
    user_id = await conn.get_token(db=db, token_type='access', token=access_token)
    if not user_id:
        return Response(content="bad access token",
                        status_code=_status.HTTP_401_UNAUTHORIZED)
    user = await conn.read_data(db=db, name='phone, email, name, surname, status, last_active', table='all_users',
                                id_name='id', id_data=user_id[0][0])
    print(user)
    if user:
        return Response(content="no user in database",
                        status_code=_status.HTTP_401_UNAUTHORIZED)
    return {"ok": True,
            'name': user[0]['name'],
            'surname': user[0]['surname'],
            'phone': user[0]['phone'],
            'email': user[0]['email'],
            'status': user[0]['status'],
            'last_active': user[0]['last_active'],
            }


@app.get(path='/check_phone', tags=['Auth'], responses=check_phone_res)
async def find_phone_in_db(phone: int, db=Depends(data_b.connection)):
    """Check user in database"""
    user = await conn.read_data(db=db, name='id', table='all_users', id_name='phone', id_data=phone)
    print(user)
    if user:
        return Response(content="have user with same phone",
                        status_code=_status.HTTP_226_IM_USED)
    return {"ok": True, 'desc': 'no phone in database'}


@app.put(path='/create_user', tags=['Auth'], responses=create_user_res)
async def new_user(name: str, surname: str, phone: int, email: str, password: str, status: str,
                   db=Depends(data_b.connection)):
    """Create new user in auth server, email """
    pass_hash = sha256(password.encode('utf-8')).hexdigest()
    user = await conn.read_data(db=db, name='id', table='all_users', id_name='phone', id_data=phone)
    if user:
        return Response(content="have user with same phone",
                        status_code=_status.HTTP_401_UNAUTHORIZED)
    user_id = \
        (await conn.create_user(db=db, phone=phone, email=email, status=status, password_hash=pass_hash, name=name,
                                surname=surname))[0][0]
    access = await conn.create_token(db=db, user_id=user_id, token_type='access')
    refresh = await conn.create_token(db=db, user_id=user_id, token_type='refresh')
    return {"ok": True,
            'user_id': user_id,
            'access_token': access[0][0],
            'refresh_token': refresh[0][0]}


if __name__ == '__main__':
    app.state.pgpool = asyncpg.create_pool()
    uvicorn.run("auth_server:app",
                host="127.0.0.1",
                port=10001)
