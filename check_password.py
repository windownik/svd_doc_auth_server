import starlette.status as _status
from starlette.responses import Response


async def check_new_user_data(password: str, status: str, phone: int, conn, db):
    if len(password) < 6:
        return Response(content="min password length is 6",
                        status_code=_status.HTTP_226_IM_USED)
    if not check_password(password=password):
        return Response(content="bad letters in password",
                        status_code=_status.HTTP_226_IM_USED)
    if status not in ('simple', 'creator', 'admin', '0'):
        return Response(content="wrong status",
                        status_code=_status.HTTP_226_IM_USED)

    user = await conn.read_data(db=db, name='id', table='all_users', id_name='phone', id_data=phone)
    if user:
        return Response(content="have user with same phone",
                        status_code=_status.HTTP_401_UNAUTHORIZED)
    return 'good'


def check_password(password: str):
    good_letters = 'a b c d e f g h i j k l m n o p q r s t u v w x y z 1234567890'
    for i in password.lower():
        if i not in good_letters:
            return False
    return True
