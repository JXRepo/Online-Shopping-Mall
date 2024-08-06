from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from meiduo_mall import settings
from itsdangerous import BadData,BadTimeSignature,SignatureExpired

# encryption
def generic_openid(openid):


    s = Serializer(secret_key=settings.SECRET_KEY, expires_in=3600)
    access_token = s.dumps({'openid': openid})

    # Convert bytes to str
    return access_token.decode()


# Decryption
def check_access_token(token):
    s = Serializer(secret_key=settings.SECRET_KEY, expires_in=3600)
    try:
        result=s.loads(token)
    except Exception:
        return None
    else:
        return result.get('openid')

