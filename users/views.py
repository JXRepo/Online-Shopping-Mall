from django.shortcuts import render

# Create your views here.
"""
Demand analysis: According to the functions of the page (from top to bottom, from left to right), which functions need to be completed with the backend
How to determine which functions need to interact with the backend? ? ?
1. Experience
2. Pay attention to similar functions of similar URLs

"""

"""
Function to determine whether the username is repeated.

Front-end (understanding): When the user enters the username, it loses focus and sends an axios (ajax) request

Back-end (idea):
Request: Receive username
Business logic:
Query the database according to the username. If the number of query results is equal to 0, it means that there is no registration
If the number of query results is equal to 1, it means that there is registration
Response JSON
{code:0,count:0/1,errmsg:ok}

Route GET usernames/<username>/count/
Steps:
1. Receive username
2. Query the database according to the username
3. Return response         
    
"""
from django.views import View
from apps.users.models import User
from django.http import JsonResponse
import re
class UsernameCountView(View):

    def get(self,request,username):
        # 1.  Receive the user name and make a judgment on the user name
        # if not re.match('[a-zA-Z0-9_-]{5,20}',username):
        #     return JsonResponse({'code':200,'errmsg':'Username does not meet requirements'})
        # 2.  Query the database by username
        count=User.objects.filter(username=username).count()
        # 3.  Return Response
        return JsonResponse({'code':0,'count':count,'errmsg':'ok'})

"""
We don't trust any data submitted by the front end! ! ! !

Front end: When the user enters the username, password, confirm password, mobile phone number, and whether they agree to the agreement, they will click the registration button
The front end will send an axios request

Back end:
Request: Receive request (JSON). Get data
Business logic: Verify data. Data storage
Response: JSON {'code':0,'errmsg':'ok'}
Response code 0 means success 400 means failure

Route: POST register/

Steps:

1. Receive request (POST------JSON)
2. Get data
3. Verify data
3.1 Username, password, confirm password, mobile phone number, whether to agree to the agreement are all required
3.2 Username meets the rules and cannot be repeated
3.3 Password meets the rules
3.4 Confirm password and password must be consistent
3.5 Mobile phone number meets the rules and cannot be repeated
3.6 Need to agree to the agreement
4. Data storage
5. Return response


"""
import json

class RegisterView(View):

    def post(self,request):
        # 1. Receiving Requests（POST------JSON）
        body_bytes=request.body
        body_str=body_bytes.decode()
        body_dict=json.loads(body_str)

        # 2. retrieve data
        username=body_dict.get('username')
        password=body_dict.get('password')
        password2=body_dict.get('password2')
        mobile=body_dict.get('mobile')
        allow=body_dict.get('allow')

        # 3. verify the data
        #     3.1 Username, password, confirm password, mobile phone number, whether you agree to the agreement, all required
        # all([xxx,xxx,xxx])
        # As long as the element in all is None,False
        # All returns False, otherwise returns True
        if not all([username,password,password2,mobile,allow]):
            return JsonResponse({'code':400,'errmsg':'Incomplete parameters'})
        #     3.2 The username meets the rules and cannot be repeated
        if not re.match('[a-zA-Z_-]{5,20}',username):
            return JsonResponse({'code': 400, 'errmsg': 'Username does not meet the rules'})
        #     3.3 Password meets the rules
        #     3.4 Confirm password and password must be the same
        #     3.5 The mobile phone number meets the rules and cannot be repeated
        #     3.6 Need to agree to the agreement
        # 4. Data storage
        # user=User(username=username,password=password,moble=mobile)
        # user.save()

        # User.objects.create(username=username,password=password,mobile=mobile)

        # The above two methods can both store data
        # But there is a problem. The password is not encrypted.

        # Password is encrypted
        user=User.objects.create_user(username=username,password=password,mobile=mobile)

        # How to set session information
        # request.session['user_id']=user.id

        # The system (Django) provides us with a way to maintain state
        from django.contrib.auth import login
        # request, user,
        # Status retention -- Logged-in user status retention
        # user Logged in user information
        login(request,user)

        # 5. Return Response
        return JsonResponse({'code':0,'errmsg':'ok'})

"""
If the requirement is that a successful registration means that the user has passed authentication, 
then the status can be maintained after the registration is successful (successful registration means that the user has logged in) v
If the requirement is that a successful registration does not mean that the user has passed authentication, 
then there is no need to maintain the status after the registration is successful (successful registration, separate login)

There are two main ways to maintain the status:
Use Cookies to store information on the client
Use Session to store information on the server

"""

"""
Login

Front-end:
When the user completes entering the username and password, he will click the login button. At this time, the front-end should send an axios request

Back-end:
Request: Receive data, verify data
Business logic: Verify whether the username and password are correct, session
Response: Return JSON data 0 Success. 400 Failure

POST /login/
Steps:
1. Receive data
2. Verify data
3. Verify whether the username and password are correct
4. Session
5. Determine whether to remember the login
6. Return response

"""

class LoginView(View):

    def post(self,request):
        # 1. Receive data
        data=json.loads(request.body.decode())
        username=data.get('username')
        password=data.get('password')
        remembered=data.get('remembered')
        # 2. verify the data
        if not all([username,password]):
            return JsonResponse({'code':400,'errmsg':'Incomplete parameters'})


        # Confirm whether we are searching by mobile phone number or by username

        # USERNAME_FIELD We can modify the User. USERNAME_FIELD field according to
        # To affect the authenticate query
        # authenticate is to query based on USERNAME_FIELD
        if re.match('1[3-9]\d{9}',username):
            User.USERNAME_FIELD='mobile'
        else:
            User.USERNAME_FIELD='username'

        # 3. Verify that the username and password are correct
        # We can query by user name through the model
        # User.objects.get(username=username)


        # Method 2
        from django.contrib.auth import authenticate
        # authenticate passing username and password
        # If the username and password are correct, the User information is returned.
        # If the username and password are incorrect, it returns None
        user=authenticate(username=username,password=password)

        if user is None:
            return JsonResponse({'code':400,'errmsg':'Incorrect username or password'})

        # 4. session
        from django.contrib.auth import login
        login(request,user)

        # 5. Determine whether to remember the login
        if remembered:
            # Remember to log in -- 2 weeks or 1 month The specific duration is determined by the product
            request.session.set_expiry(None)

        else:
            # Do not remember login. Close the browser and the session expires.
            request.session.set_expiry(0)

        # 6. Return Response
        response = JsonResponse({'code':0,'errmsg':'ok'})
        # To display user information on the home page
        response.set_cookie('username',username)

        # Must be logged in to merge
        from apps.carts.utils import merge_cookie_to_redis
        response = merge_cookie_to_redis(request, response)

        return response

"""
Front-end:
When the user clicks the exit button, the front-end sends an axios delete request

Back-end:
Request
Business logic Exit
Response Return JSON data

"""
from django.contrib.auth import logout
class LogoutView(View):

    def get(self,request):
        # 1. Deleting session information
        logout(request)

        response = JsonResponse({'code':0,'errmsg':'ok'})
        # 2. Delete cookie information. Why do we need to delete it?
        # Because the front end uses cookie information to determine whether the user is logged in.
        response.delete_cookie('username')

        return response

# User Center, must also be a logged in user

"""

LoginRequiredMixin will return a redirect for unlogged users. Redirection is not JSON data

We need to return JSON data
"""


from utils.views import LoginRequiredJSONMixin
class CenterView(LoginRequiredJSONMixin,View):

    def get(self,request):
        # request.user is the logged-in user information
        # request.user comes from the middleware
        # the system will judge if we are indeed a logged-in user, we can get the model instance data corresponding to the logged-in user
        # if we are not a logged-in user, then request.user = AnonymousUser() anonymous user
        info_data = {
            'username':request.user.username,
            'email':request.user.email,
            'mobile':request.user.mobile,
            'email_active':request.user.email_active,
        }

        return JsonResponse({'code':0,'errmsg':'ok','info_data':info_data})

"""
Requirements: 1. Save email address 2. Send an activation email 3. User activation email

Front-end:
When the user enters the email address, click Save. At this time, an axios request will be sent.

Back-end:
Request Receive request, get data
Business logic Save email address Send an activation email
Response JSON code=0

Routing PUT
Steps
1. Receive request
2. Get data
3. Save email address
4. Send an activation email
5. Return response

Requirements (what function to achieve) --> Idea (Request. Business logic. Response) --> Steps --> Code implementation
"""

class EmailView(LoginRequiredJSONMixin,View):

    def put(self,request):
        # 1. Receiving Requests
        #put post －－－　body
        data=json.loads(request.body.decode())
        # 2. retrieve data
        email=data.get('email')
        # verify the data
        # Regular　
        # 3. Save Email Address
        user=request.user
        # user / request.user is the instance object of the logged-in user
        # user --> User
        user.email=email
        user.save()
        # 4. Send an activation email
        from django.core.mail import send_mail
        # subject, message, from_email, recipient_list,
        # subject,      theme
        subject='Mall Activation Email'
        # message,      content of email
        message=""
        # from_email,   Sender
        from_email='Mall<qi_rui_hua@163.com>'
        # recipient_list, 收件人列表
        recipient_list = ['qi_rui_hua@126.com','qi_rui_hua@163.com']

        # If the content of the email is html, use html_message
        # 4.1 Encrypt the connection data of the a tag
        # user_id=1
        from apps.users.utils import generic_email_verify_token
        token=generic_email_verify_token(request.user.id)

        verify_url = "http://www.meiduo.site:8080/success_verify_email.html?token=%s"%token
        # 4.2 Organizing our activation emails
        html_message = '<p>Dear users, Hello!</p>' \
                       '<p>Thank you for using Mido Mall.</p>' \
                       '<p>Your email address is: %s. Please click this link to activate your email address:</p>' \
                       '<p><a href="%s">%s<a></p>' % (email, verify_url, verify_url)


        # html_message="Click the button to activate <a href='http://www.itcast.cn/?token=%s'>activation</a>"%token

        # send_mail(subject=subject,
        #           message=message,
        #           from_email=from_email,
        #           recipient_list=recipient_list,
        #           html_message=html_message)
        from celery_tasks.email.tasks import celery_send_email
        celery_send_email.delay(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=recipient_list,
            html_message=html_message
        )

        # 5. Return Response
        return JsonResponse({'code':0,'errmsg':'ok'})

"""
Django project
1. Strengthen the foundation of Django
2. Analyze requirements
3. Learn new knowledge
4. Master the ability to analyze and solve problems (debug)
"""

"""

1. Set up the mail server

We set up the 163 mail server
This is equivalent to enabling 163 to help us send mail. At the same time, set some information (especially the authorization code)

2. Set the configuration information for sending mail
# Which class of Django should send mails
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# The host and port number of the mail server
EMAIL_HOST = 'smtp.163.com'
EMAIL_PORT = 25

# Use my 163 server and authorization code
# Mailbox to send mail
EMAIL_HOST_USER = 'qi_rui_hua@163.com'
# Client authorization password set in the mailbox
EMAIL_HOST_PASSWORD = '123456abc'

3. Call the send_mail method
"""



"""
Requirements (know what we are going to do???):
Activate the user's email
Front-end (what the user did, what parameters were passed):
The user will click on the activation link. The activation link carries the token
Back-end:
Request: receive request, get parameters, verify parameters
Business logic: user_id, query data based on user id, modify data
Response: return response JSON

Route: PUT emails/verification/ Note: token is not in the body
Steps:

1. Receive request
2. Get parameters
3. Verify parameters
4. Get user_id
5. Query data based on user id
6. Modify data
7. Return response JSON

"""

class EmailVerifyView(View):

    def put(self,request):
        # 1. Receiving Requests
        params=request.GET
        # 2. Get Parameters
        token=params.get('token')
        # 3. Verify Parameters
        if token is None:
            return JsonResponse({'code':400,'errmsg':'Missing parameters'})
        # 4. Get user_id
        from apps.users.utils import check_verify_token
        user_id=check_verify_token(token)
        if user_id is None:
            return JsonResponse({'code':400,'errmsg':'Parameter error'})
        # 5. Query data based on user id
        user=User.objects.get(id=user_id)
        # 6. change the data
        user.email_active=True
        user.save()
        # 7. Return response JSON
        return JsonResponse({'code':0,'errmsg':'ok'})

"""
Request
Business logic (add, delete, modify, and query database)
Response
Add (register)
1. Receive data
2. Verify data
3. Store data
4. Return response
Delete
1. Query the specified record
2. Delete data (physical deletion, logical deletion)
3. Return response
Change (personal mailbox)
1. Query the specified record
2. Receive data
3. Verify data
4. Update data
5. Return response
Query (personal center data display, province, city, district)
1. Query the specified data
2. Convert object data to dictionary data
3. Return response
"""



"""
Requirements:
Add a new address

Front-end:
When the user completes the address information, the front-end should send an axios request with relevant information (POST--body)

Back-end:

Request: Receive request, get parameters, verify parameters
Business logic: Data storage
Response: Return response

Route: POST /addresses/create/
Steps:
1. Receive request
2. Get parameters, verify parameters
3. Data storage
4. Return response

"""
from apps.users.models import Address
class AddressCreateView(LoginRequiredJSONMixin,View):

    def post(self,request):
        # 1. Receiving Requests
        data=json.loads(request.body.decode())
        # 2. Get parameters and verify parameters
        receiver=data.get('receiver')
        province_id=data.get('province_id')
        city_id=data.get('city_id')
        district_id=data.get('district_id')
        place=data.get('place')
        mobile=data.get('mobile')
        tel=data.get('tel')
        email=data.get('email')

        user=request.user
        # Verification parameters (omitted)
        # 2.1 Required parameters for verification
        # 2.2 Is the ID of the province, city or district correct?
        # 2.3 Length of the detailed address
        # 2.4 Mobile phone number
        # 2.5 Landline number
        # 2.6 Email address
        # 3. Data storage
        address=Address.objects.create(
            user=user,
            title=receiver,
            receiver=receiver,
            province_id=province_id,
            city_id=city_id,
            district_id=district_id,
            place=place,
            mobile=mobile,
            tel=tel,
            email=email
        )

        address_dict = {
            'id':address.id,
            "title": address.title,
            "receiver": address.receiver,
            "province": address.province.name,
            "city": address.city.name,
            "district": address.district.name,
            "place": address.place,
            "mobile": address.mobile,
            "tel": address.tel,
            "email": address.email
        }

        # 4. Return Response
        return JsonResponse({'code':0,'errmsg':'ok','address':address_dict})


class AddressView(LoginRequiredJSONMixin,View):

    def get(self,request):
        # 1. Query specified data
        user=request.user
        # addresses=user.addresses

        addresses=Address.objects.filter(user=user,is_deleted=False)
            # 2. Convert object data to dictionary data
        address_list=[]
        for address in addresses:
            address_list.append({
                "id": address.id,
                "title": address.title,
                "receiver": address.receiver,
                "province": address.province.name,
                "city": address.city.name,
                "district": address.district.name,
                "place": address.place,
                "mobile": address.mobile,
                "tel": address.tel,
                "email": address.email
            })
        # 3. Return Response
        return JsonResponse({'code':0,'errmsg':'ok','addresses':address_list})


#################################################

"""
1. Analyze the requirements according to the page effect (careful + experience)
1. Recent browsing history can only be accessed by logged-in users. We only record the browsing history of logged-in users
2. Browsing history should be in order
3. No paging
2. Function
① When users visit product details, add browsing history
② Display browsing history in the personal center
3. Analysis
Question 1: What data is saved? User id, product id, order (access time)
Question 2: Where to save? Generally, it is saved in the database (disadvantages: ① Slow ② Frequent database operations) Teaching
It is best to save in redis

It can be. It depends on the specific arrangements of the company. The server memory is relatively large. mysql + redis

user_id,sku_id, order

key: value

redis:
string: x
hash: x
list: v
set: x
zset: v
weight: value
"""

"""
Add browsing history
Front-end:
When a logged-in user visits a specific SKU page, an axios request is sent. The request carries sku_id
Back-end:
Request: Receive request, get request parameters, and verify parameters
Business logic; Connect to redis, remove duplicates first, and save only 5 records in redsi
Response: Return JSON

Route: POST browse_histories
Steps:
1. Receive request
2. Get request parameters
3. Verify parameters
4. Connect to redis list
5. Remove duplicates
6. Save to redsi
7. Save only 5 records
8. Return JSON
Display browsing history
Front-end:
When the user accesses the browsing history, an axios request is sent. The request will carry session information
Backend:
Request:
Business logic; Connect to redis and get redis data ([1,2,3]). Query data based on product id and convert the object into a dictionary
Response: JSON

Route: GET
Steps:
1. Connect to redis
2. Get redis data ([1,2,3])
3. Query data based on product id
4. Convert the object into a dictionary
5. Return JSON
"""
from apps.goods.models import SKU
from django_redis import get_redis_connection
class UserHistoryView(LoginRequiredJSONMixin,View):

    def post(self,request):
        user=request.user

        # 1. Receiving Requests
        data=json.loads(request.body.decode())
        # 2. Get request parameters
        sku_id=data.get('sku_id')
        # 3. Verify Parameters
        try:
            sku=SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return JsonResponse({'code':400,'errmsg':'No such product'})
        # 4. Connect to redis    list
        redis_cli=get_redis_connection('history')
        # 5. Remove duplicates (delete the product ID data first, then add it)
        redis_cli.lrem('history_%s'%user.id,0,sku_id)
        # 6. Save to redsi
        redis_cli.lpush('history_%s'%user.id,sku_id)
        # 7. Only 5 records are saved
        redis_cli.ltrim("history_%s"%user.id,0,4)
        # 8. Return JSON
        return JsonResponse({'code':0,'errmsg':'ok'})


    def get(self,request):
        # 1. Connect to redis
        redis_cli=get_redis_connection('history')
        # 2. Get redis data ([1,2,3])
        ids=redis_cli.lrange('history_%s'%request.user.id,0,4)
        # [1,2,3]
        # 3. Query data based on product ID
        history_list=[]
        for sku_id in ids:
            sku=SKU.objects.get(id=sku_id)
            # 4. Convert an object to a dictionary
            history_list.append({
                'id':sku.id,
                'name':sku.name,
                'default_image_url': sku.default_image.url,
                'price': sku.price
            })

        # 5. Return JSON
        return JsonResponse({'code':0,'errmsg':'ok','skus':history_list})

