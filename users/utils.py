from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from meiduo_mall import settings

def generic_email_verify_token(user_id):

    # 1. Create an instance
    s=Serializer(secret_key=settings.SECRET_KEY,expires_in=3600*24)
    # 2. Encrypting Data
    data=s.dumps({'user_id':user_id})
    # 3. Return data
    return data.decode()


def check_verify_token(token):

    # 1. Create an instance
    s = Serializer(secret_key=settings.SECRET_KEY, expires_in=3600 * 24)
    # 2. Decrypted data - there may be anomalies
    try:
        result = s.loads(token)
    except Exception as e:
        return None
    # 3. retrieve data
    # result = {'user_id':user_id}
    return result.get('user_id')
