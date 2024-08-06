from django.http import HttpResponse, JsonResponse
from django.shortcuts import render

"""
Front-end
Splice a url. Then give it to img. img will initiate a request
url=http://mp-meiduo-python.itheima.net/image_codes/ca732354-08d0-416d-823b-14b1d77746d2/

url=http://ip:port/image_codes/uuid/

Back-end
Request Receive uuid in the route
Business logic Generate image verification code and image binary. Save the image verification code through redis
Response Return image binary

Route: GET image_codes/uuid/
Steps:
1. Receive uuid in the route
2. Generate image verification code and image binary
3. Save the image verification code through redis
4. Return image binary
"""

# Create your views here.
from django.views import View


class ImageCodeView(View):

    def get(self,request,uuid):
        # 1. Receive the uuid in the route
        # 2. Generate image verification code and image binary
        from libs.captcha.captcha import captcha
        # text is the content of the image verification code, for example: xyzz
        # image is the image binary
        text,image=captcha.generate_captcha()

        # 3. Save the image verification code through redis
        # 3.1 Connect to redis
        from django_redis import get_redis_connection
        redis_cli = get_redis_connection('code')
        # 3.2 Command Operation
        # name, time, value
        redis_cli.setex(uuid,100,text)
        # 4. Returns the image binary
        # Because images are binary, we cannot return JSON data
        # content_type = Response body data type
        # The grammatical form of content_type is: major category/minor category
        # content_type (MIME type)
        # Image： image/jpeg , image/gif, image/png
        return HttpResponse(image,content_type='image/jpeg')

"""
1. Registration
We provide free development testing. [Before free development testing, please register to become a platform user].

2. Bind test number
Free development testing requires binding a test number in "Console-Management-Number Management-Test Number".

3. Development testing
For the development testing process, please refer to the SMS service interface and Demo example / SDK reference (new version) example. 
For Java environment installation, please refer to "New SDK".

4. Notes on free development testing
4.1. Free development testing requires the use of the "Console Homepage" and developer master account related information, 
such as the master account, application ID, etc.

4.2. The template ID used for free development testing is 1. Specific content: [Cloud Communication] Your verification code is {1}, 
please enter it correctly within {2} minutes. Among them, {1} and {2} are SMS template parameters.

4.3. After the test is successful, you can apply for the SMS template and use it officially.

"""

"""

Front-end
When the user enters the mobile phone number and the picture verification code, the front-end sends an axios request
sms_codes/18310820644/?image_code=knse&image_code_id=b7ef98bb-161b-437a-9af7-f434bb050643

Back-end

Request: Receive the request and get the request parameters (the route has the mobile phone number, the user's picture 
verification code and UUID are in the query string)
Business logic: Verify parameters, verify the picture verification code, generate the SMS verification code, save the 
SMS verification code, and send the SMS verification code
Response: Return the response
{'code':0,'errmsg':'ok'}

Route: GET sms_codes/18310820644/?image_code=knse&image_code_id=b7ef98bb-161b-437a-9af7-f434bb050643

Steps:

1. Get request parameters

2. Verify parameters

3. Verify image verification code

4. Generate SMS verification code

5. Save SMS verification code

6. Send SMS verification code

7. Return response

Requirements --》 Ideas --》 Steps --》 Code

debug mode is the debugging mode (bug)

debug + breakpoints are used together. We see the process of program execution

Add breakpoints Add to the first line of the function body! ! ! ! !
"""

class SmsCodeView(View):

    def get(self,request,mobile):
        # 1. Get request parameters
        image_code=request.GET.get('image_code')
        uuid=request.GET.get('image_code_id')
        # 2. Verify Parameters
        if not all([image_code,uuid]):
            return JsonResponse({'code':400,'errmsg':'Incomplete parameters'})
        # 3. Verify the picture verification code
        # 3.1 Connect to redis
        from django_redis import get_redis_connection
        redis_cli=get_redis_connection('code')
        # 3.2 Get redis data
        redis_image_code=redis_cli.get(uuid)
        if redis_image_code is None:
            return JsonResponse({'code':400,'errmsg':'The image verification code has expired'})
        # 3.3 Compared
        if redis_image_code.decode().lower() != image_code.lower():
            return JsonResponse({'code':400,'errmsg':'Image verification code error'})

        # Extract the tag of sending SMS and see if there is any
        send_flag=redis_cli.get('send_flag_%s'%mobile)

        if send_flag is not None:
            return JsonResponse({'code':400,'errmsg':"Don't send text messages too frequently"})

        # 4. Generate SMS verification code
        from  random import randint
        sms_code= '%06d'%randint(0,999999)

        # Pipeline 3 steps
        # ① Create a new pipeline
        pipeline=redis_cli.pipeline()
        # ② Pipeline Collection Instructions
        # 5. Save SMS verification code
        pipeline.setex(mobile, 300, sms_code)
        # Add a send tag. Valid for 60 seconds. The content can be anything.
        pipeline.setex('send_flag_%s' % mobile, 60, 1)
        # ③ Pipeline execution instructions
        pipeline.execute()

        # # 5. Save SMS verification code
        # redis_cli.setex(mobile,300,sms_code)
        # # Add a send tag. Valid for 60 seconds. The content can be anything.
        # redis_cli.setex('send_flag_%s'%mobile,60,1)

        # 6. Send SMS verification code
        # from libs.yuntongxun.sms import CCP
        # CCP().send_template_sms(mobile,[sms_code,5],1)

        from celery_tasks.sms.tasks import celery_send_sms_code
        # The parameters of delay are equivalent to the parameters of task (function)
        celery_send_sms_code.delay(mobile,sms_code)

        # 7. Return Response
        return JsonResponse({'code':0,'errmsg':'ok'})

