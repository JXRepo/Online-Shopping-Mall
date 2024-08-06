from django.shortcuts import render

# Create your views here.
"""
Steps for third-party login:
1. Apply to become a developer on the QQ Interconnection Development Platform (optional)
2. Create an application on QQ Interconnection (optional)
3. Develop according to the documentation (read the documentation)



3.1 Preparations ----------------------------------- Ready

    # QQ login parameters
    # The client id we applied for
    QQ_CLIENT_ID = '101474184'          appid
    # Our affectionate client key
    QQ_CLIENT_SECRET = 'c6ce949e04e12ecc909ae6a8b09b637c'   appkey
    # We added when applying: The callback path after successful login
    QQ_REDIRECT_URI = 'http://www.meiduo.site:8080/oauth_callback.html'


3.2 Place the QQ login icon (Purpose: Let us click the QQ icon to implement third-party login) ------------- The front end is ready

3.3 Get code and token according to oauth2.0 --------------What we need to do

    For applications, two steps are required:
        1. Get the Authorization Code; On the surface, it is a link, but in reality, it requires the user's consent and then obtains the code

        2. Get the Access Token through the Authorization Code

3.4 Exchange the token for openid ----------------What we need to do
Openid is the only identifier corresponding to the user's identity on this website. The website can store this ID to facilitate the user to identify his identity when logging in next time,
or bind it to the user's original account on the website.

Bind openid and user information one by one

Generate user binding link ----------》Get code ------------》Get token ------------》Get openid --------》Save openid

"""


"""
Generate user binding link

Front-end: When the user clicks the QQ login icon, the front-end should send an axios (Ajax) request

Back-end:
Request
Business logic Call QQLoginTool to generate a jump link
Response Return jump link {"code":0,"qq_login_url":"http://xxx"}
Route GET qq/authorization/
Steps
1. Generate QQLoginTool instance object
2. Call the object method to generate a jump link
3. Return response

404 Route does not match
405 Method is not allowed (you have not implemented the method corresponding to the request)
"""
from django.views import View
from QQLoginTool.QQtool import OAuthQQ
from meiduo_mall import settings
from django.http import JsonResponse
class QQLoginURLView(View):

    def get(self,request):
        # 1. Generate QQLoginTool instance object
        # client_id=None,               appid
        # client_secret=None,           appsecret
        # redirect_uri=None,            After the user agrees to log in, the page that jumps to
        # state=None                    I don't know what it means, so I just write it down. I will analyze the problem when something goes wrong.
        qq=OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                   client_secret=settings.QQ_CLIENT_SECRET,
                   redirect_uri=settings.QQ_REDIRECT_URI,
                   state='xxxxx')
        # 2. Calling an object's method generates a jump link
        qq_login_url=qq.get_qq_url()
        # 3. Return Response
        return JsonResponse({'code':0,'errmsg':'ok','login_url':qq_login_url})

"""

Requirements: Get code, exchange code for token, and then exchange token for openid

Front-end:
    The code that the user agrees to log in should be obtained. Send this code to the back-end
Back-end:
    Request Get code
Business logic Exchange code for token, and then exchange token for openid
Judge based on openid
If not bound, you need to bind
If bound, log in directly
Response
    Route GET oauth_callback/?code=xxxxx
Steps
1. Get code
2. Exchange code for token
3. Exchange token for openid
4. Judge based on openid
5. If not bound, you need to bind
6. If bound, log in directly

"""
from apps.oauth.models import OAuthQQUser
from django.contrib.auth import login
import json
from apps.users.models import User

class OauthQQView(View):

    def get(self,request):
        # 1. Get the code
        code=request.GET.get('code')
        if code is None:
            return JsonResponse({'code':400,'errmsg':'Incomplete parameters'})
        # 2. Exchange code for token
        qq = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                     client_secret=settings.QQ_CLIENT_SECRET,
                     redirect_uri=settings.QQ_REDIRECT_URI,
                     state='xxxxx')
        #'5D52C8BAB528D363DBCD3FC0CEDA0BA7'
        token=qq.get_access_token(code)
        # 3. Then exchange token for openid
        # 'CBCF1AA40E417CD73880666C3D6FA1D6'
        openid=qq.get_open_id(token)

        # 4. Query and judge based on openid
        try:
            qquser=OAuthQQUser.objects.get(openid=openid)
        except OAuthQQUser.DoesNotExist:
            # does not exist
            # 5. If you have not bound it, you need to bind it
            """
            The idea of encapsulation

            The so-called idea of encapsulation is actually to encapsulate some codes that implement specific functions into a function (method)

            The purpose of encapsulation

            Decoupling --- when the requirements change, the impact on the modification of the code is relatively small

            Encapsulation steps
            1. Define the code to be encapsulated into a function (method)
            2. Optimize the encapsulated code
            3. Verify the encapsulated code
            
            """


            from apps.oauth.utils import generic_openid
            access_token=generic_openid(openid)

            response = JsonResponse({'code':400,'access_token':access_token})
            return response
        else:
            # exist
            # 6. If bound, log in directly
            # 6.1 Setting up the session
            login(request,qquser.user)
            # 6.2 Setting cookies
            response = JsonResponse({'code':0,'errmsg':'ok'})

            response.set_cookie('username',qquser.user.username)

            return response

    def post(self,request):
        # 1. Receiving Requests
        data=json.loads(request.body.decode())
        # 2. Get request parameter openid
        mobile=data.get('mobile')
        password=data.get('password')
        sms_code=data.get('sms_code')
        access_token=data.get('access_token')
        # Need to verify the data (omitted)

        # Add access-token decryption
        from apps.oauth.utils import check_access_token
        openid=check_access_token(access_token)
        if openid is None:
            return JsonResponse({'code':400,'errmsg':'Missing parameters'})

        # 3. Query user information based on mobile phone number
        try:
            user=User.objects.get(mobile=mobile)
        except User.DoesNotExist:
            # Mobile number does not exist
            # 5. If we find that the user's mobile phone number is not registered, we will create a user information and then bind it.
            user=User.objects.create_user(username=mobile,mobile=mobile,password=password)

        else:
            # Phone number exists
            # 4. Query the user's mobile phone number and check if the password is correct.
            # If the password is correct, you can directly save (bind) the user and openid information
            if not user.check_password(password):
                return JsonResponse({'code':400,'errmsg':'Incorrect username or password'})

        OAuthQQUser.objects.create(user=user,openid=openid)

        # 6. Completion status retention
        login(request,user)
        # 7. Return Response
        response=JsonResponse({'code':0,'errmsg':'ok'})

        response.set_cookie('username',user.username)

        return response

"""
Requirements: Bind account information

QQ (openid) and Mall account information

Front-end:
    When the user enters the mobile phone number, password, and SMS verification code, an axios request is sent. The request needs to carry mobile, password, sms_code, access_token (openid)
Back-end:

Request: Receive request and get request parameters
Business logic: Bind, complete status retention
Response: Return code=0 to jump to the homepage
Route: POST oauth_callback/

Steps:

    1. Receive request
    2. Get request parameter openid
    3. Query user information based on mobile phone number
    4. Query the user's mobile phone number to be registered. Determine whether the password is correct. If the password is correct, you can directly save (bind) the user and openid information
    5. Query the user's mobile phone number to be not registered. We will create a user information. Then bind
    6. Complete status retention
    7. Return response

"""

##########Basic Uses of itsdangerous##############################################
# itsdangerous is for data encryption

# encryption
# 1. Import the itsdangerous class
# 2. Create an instance of the class
# 3. Encrypt data
from meiduo_mall import settings
# 1. Import itsdangerous classes
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

# TimedJSONWebSignatureSerializer This class can not only encrypt data, but also set a time limit for the data.
# 2. Create an instance object of the class
# secret_key,           Secret key
# expires_in=None       Data expiration time (in seconds)
s=Serializer(secret_key=settings.SECRET_KEY,expires_in=3600)
#
# 3. Encrypting Data
token=s.dumps({'openid':'1234567890'})
# b'eyJhbGciOiJIUzUxMiIsImlhdCI6MTYwMjE0Mzg3MCwiZXhwIjoxNjAyMTQ3NDcwfQ.eyJvcGVuaWQiOiIxMjM0NTY3ODkwIn0._O8UkkDSrETJUreKnfOKANLcAszEvFxBUYSG-Q8MogCJAOvoDxxwkAOKlEMB9yL46R_yS1ok1Rgw6HsO_hIjwg'


###############################################################
# Decryption

# 1. Import itsdangerous classes
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
# 2. Create an instance object of the class
s=Serializer(secret_key=settings.SECRET_KEY,expires_in=3600)
# 3. Decrypting Data
s.loads(token)