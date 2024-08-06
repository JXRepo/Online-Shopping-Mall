from django.shortcuts import render

# Create your views here.
"""
1. Register as a developer on the corresponding open platform.

2. Create an application.

3. Develop according to the documentation.

We do not need to create an application (for testing and learning purposes). Alipay provides us with a sandbox (testing) environment.

1. Set up the public and private keys.
   
   - One pair for Meidu Mall (we handle it).
   - One pair for Alipay (they handle it).

During the entire payment process, we (Meidu Mall) need to do just two things:
① Generate the link to redirect to Alipay.
② Save the transaction serial number returned by Alipay after the transaction is completed.

"""


"""
Sure, here is the translation:

---

**Requirement:**
When the user clicks the "Go to Pay" button, the backend needs to generate a redirect link.

**Frontend:**
- Send an axios request with the order ID.

**Backend:**

- **Request:** Obtain the order ID
- **Business Logic:**
  1. Generate the Alipay link (refer to the documentation)
  2. Retrieve the application's private key and Alipay public key
  3. Create an Alipay instance and call the Alipay method
  4. Construct the link
- **Response:**
- **Route:** GET `payment/order_id/`

**Steps:**
1. Obtain the order ID
2. Verify the order ID (query order information based on the order ID)
3. Retrieve the application's private key and Alipay public key
4. Create an Alipay instance
5. Call the Alipay payment method
6. Construct the link
7. Return the response
    
"""
from django.views import View
from apps.orders.models import OrderInfo
from utils.views import LoginRequiredJSONMixin
from django.http import JsonResponse
from meiduo_mall import settings
from alipay import AliPay,AliPayConfig

class PayUrlView(LoginRequiredJSONMixin,View):

    def get(self,request,order_id):
        user=request.user
        # 1. **Obtain the Order ID**
        # 2. **Verify the Order ID (Query order information based on the Order ID)**
        try:
            # **For the accuracy of business logic**,
            # Check the orders to be paid
            order=OrderInfo.objects.get(order_id=order_id,
                                        status=OrderInfo.ORDER_STATUS_ENUM['UNPAID'],
                                        user=user)
        except OrderInfo.DoesNotExist:
            return JsonResponse({'code':400,'errmsg':'No such order'})
        # 3. Read the application private key and Alipay public key

        app_private_key_string = open(settings.APP_PRIVATE_KEY_PATH).read()
        alipay_public_key_string = open(settings.ALIPAY_PUBLIC_KEY_PATH).read()
        # 4. Create an Alipay instance
        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,  # Default callback url
            app_private_key_string=app_private_key_string,
            # Alipay's public key is used to verify Alipay's return message, not your own public key.
            alipay_public_key_string=alipay_public_key_string,
            sign_type="RSA2",  # RSA or RSA2
            debug = settings.ALIPAY_DEBUG,  # Default: False
            config = AliPayConfig(timeout=15)  # Optional, request timeout
        )
        # 5. Calling Alipay payment method
        # If you are a Python 3 user, just use the default string
        subject = "Mido Mall Test Order"

        # For website payment, you need to jump to https://openapi.alipay.com/gateway.do? + order_string
        # https://openapi.alipay.com/gateway.do This is online
        # 'https://openapi.alipaydev.com/gateway.do' This is a sandbox.
        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id,
            total_amount=str(order.total_amount),       # Type conversion must be performed because decimal is not a basic data type
            subject=subject,
            return_url=settings.ALIPAY_RETURN_URL,           # After successful payment, the page you will be redirected to
            notify_url="https://example.com/notify"  # Optional, if not filled, the default notify url will be used
        )
        # 6.  Splicing connection
        pay_url = 'https://openapi.alipaydev.com/gateway.do?'+order_string
        # 7. Return Response
        return JsonResponse({'code':0,'errmsg':'ok','alipay_url':pay_url})


"""
Front-end:
When the user completes the payment, it will jump to the specified product page
The request query string in the page contains payment related information
The front-end just submits this data to the back-end
Back-end:
Request: Receive data
Business logic: Convert the query string to a dictionary, verify the data, and obtain the Alipay transaction serial number if there is no problem
Change the order status
Response:
Route: PUT payment/status/
Steps:
1. Receive data
2. Convert the query string to a dictionary and verify the data
3. Verify that there is no problem and obtain the Alipay transaction serial number
4. Change the order status
5. Return the response

Buyer account axirmj7487@sandbox.com
Login password 111111
Payment password 111111
"""
from apps.pay.models import Payment
class PaymentStatusView(View):

    def put(self,request):
        # 1. Receive data
        data=request.GET
        # 2. Query string converted to dictionary Validation data
        data=data.dict()

        # 3. Verify that there is no problem and obtain the Alipay transaction serial number
        signature = data.pop("sign")

        app_private_key_string = open(settings.APP_PRIVATE_KEY_PATH).read()
        alipay_public_key_string = open(settings.ALIPAY_PUBLIC_KEY_PATH).read()
        # Create an Alipay instance
        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,  # Default callback url
            app_private_key_string=app_private_key_string,
            # Alipay's public key is used to verify Alipay's return message, not your own public key.
            alipay_public_key_string=alipay_public_key_string,
            sign_type="RSA2",  # RSA or RSA2
            debug=settings.ALIPAY_DEBUG,  # Default: False
            config=AliPayConfig(timeout=15)  # Optional, request timeout
        )
        success = alipay.verify(data, signature)
        if success:
            # Get trade_no String Required 64 Alipay transaction number
            trade_no=data.get('trade_no')
            order_id=data.get('out_trade_no')
            Payment.objects.create(
                trade_id=trade_no,
                order_id=order_id
            )
            # 4. Change order status

            OrderInfo.objects.filter(order_id=order_id).update(status=OrderInfo.ORDER_STATUS_ENUM['UNSEND'])

            return JsonResponse({'code':0,'errmsg':'ok','trade_id':trade_no})
        else:

            return JsonResponse({'code':400,'errmsg':'Please check the order status in the order in the personal center'})
