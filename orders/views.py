from django.shortcuts import render

# Create your views here.
"""
**Requirement:**
    Display the order submission page

**Front-end:**
    Send an Axios request to get address information and information about selected products in the shopping cart

**Back-end:**
- **Request:** Must be logged-in users to access
- **Business Logic:** Address information, selected products in the shopping cart
- **Response:** JSON
- **Route:** 
  - `GET /orders/settlement/`

**Steps:**

1. **Get user information**

2. **Address information**
   - 2.1 Query the user’s address information `[Address, Address, ...]`
   - 2.2 Convert object data to dictionary data

3. **Information about selected products in the shopping cart**
   - 3.1 Connect to Redis
   - 3.2 Use hash: `{sku_id: count, sku_id: count}`
   - 3.3 Use set: `[1, 2]`
   - 3.4 Reorganize selected information
   - 3.5 Query detailed information about the products by their IDs `[SKU, SKU, SKU, ...]`
   - 3.6 Convert object data to dictionary data
"""
from django.views import View
from utils.views import LoginRequiredJSONMixin
from apps.users.models import Address
from django_redis import get_redis_connection
from apps.goods.models import SKU
from django.http import JsonResponse

class OrderSettlementView(LoginRequiredJSONMixin,View):

    def get(self,request):
        # 1. Get user information
        user=request.user
        # 2. Address information
        #     2.1 Query the user's address information [Address,Address,...]
        addresses=Address.objects.filter(is_deleted=False)
        #     2.2 Convert object data to dictionary data
        addresses_list=[]
        for address in addresses:
            addresses_list.append({
                'id': address.id,
                'province': address.province.name,
                'city': address.city.name,
                'district': address.district.name,
                'place': address.place,
                'receiver': address.receiver,
                'mobile': address.mobile
            })
        # 3. Information about selected products in the shopping cart
        #     3.1 Connect to Redis
        redis_cli=get_redis_connection('carts')
        pipeline=redis_cli.pipeline()
        #     3.2 hash        {sku_id:count,sku_id:count}
        # **Special Note:** Do not receive the Redis response here with
        # `all = pipeline.hgetall()`. The correct approach is to receive it inside `execute()`.
        pipeline.hgetall('carts_%s'%user.id)
        #     3.3 set         [1,2]
        pipeline.smembers('selected_%s'%user.id)
        # We receive the results after the pipeline is executed.
        result=pipeline.execute()
        # `result = [hash result, set result]`
        sku_id_counts=result[0]         #{sku_id:count,sku_id:count}
        selected_ids=result[1]          # [1,2]
        #     3.4 Reorganize the selected information
        #  selected_carts = {sku_id:count}
        selected_carts={}
        for sku_id in selected_ids:
            selected_carts[int(sku_id)]=int(sku_id_counts[sku_id])

        # {sku_id:count,sku_id:count}
        #     3.5 Query detailed information about the products based on their IDs [SKU,SKU,SKu...]
        sku_list=[]
        for sku_id,count in selected_carts.items():
            sku=SKU.objects.get(pk=sku_id)
            #     3.6 Need to convert object data to dictionary data
            sku_list.append({
                'id':sku.id,
                'name':sku.name,
                'count':count,
                'default_image_url': sku.default_image.url,
                'price': sku.price
            })

        # Shipping fee
        from decimal import Decimal
        freight=Decimal('10')
        # float double
        # decimal   -- Currency type

        # 01010101
        # Integer
        # Special handling for saving  decimal numbers
        # 12.5
        # 12  0.5
        # 1100  1

        # 12.33
        # 0.33

        # 100 / 3 = 33.33

        # 33.33   33.33     33.34


        context = {
            'skus':sku_list,
            'addresses':addresses_list,
            'freight':freight        # Shipping fee
        }

        return JsonResponse({'code':0,'errmsg':'ok','context':context})

"""
**Requirement:**
Generate an order upon clicking "Submit Order"

**Front-end:**
- Sends an Axios POST request with data: address ID, payment method, and user session information (cookie).
- Total amount, product IDs, and quantities are optional (the backend can retrieve them).

**Back-end:**
- **Request:** Receive the request and validate data
- **Business Logic:** Save data to the database
- **Response:** Return a response

**Route:** POST

**Steps:**

1. **Receive Request:**
   - `user`, `address_id`, `pay_method`

2. **Validate Data:**
   - Generate `order_id` as a primary key
   - Payment status determined by payment method
   - Total quantity, total amount, shipping fee
   - Connect to Redis
   - Retrieve hash and set
   - Query product information (e.g., `sku.price`) based on product IDs

3. **Save Data to Database:**
   - **Generate Order:**
     - 3.1 Save order basic information
     - 3.2 Save order item details:
       - Connect to Redis
       - Retrieve hash and set
       - Reorganize data for selected products (e.g., `{sku_id: count, sku_id: count}`)
       - Query product details based on selected product IDs
       - Check inventory:
         - If insufficient, order fails
         - If sufficient, reduce inventory and increase sales volume
       - Accumulate total quantity and total amount
       - Save order item details
   - Update order's total amount and total quantity
   - Remove selected product information from Redis

4. **Return Response**

**Summary:**
1. **Receive Request:** `user`, `address_id`, `pay_method`
2. **Validate Data:**
   - Generate `order_id`
   - Determine payment status
   - Set total quantity and amount to 0 initially
   - Include shipping fee
3. **Save Data to Database:**
   - **Save Basic Order Information**
   - **Save Order Item Details:**
     - Connect to Redis
     - Retrieve hash and set
     - Reorganize data for selected products `{sku_id: count, sku_id: count}`
     - Query product details for each selected product ID
     - Check inventory and handle accordingly
     - Update total quantity and amount
     - Save order item details
   - Update order total amount and quantity
   - Remove selected product information from Redis
4. **Return Response**
"""
import json
from apps.orders.models import OrderInfo,OrderGoods
from django.db import transaction

class OrderCommitView(LoginRequiredJSONMixin,View):

    def post(self,request):
        user=request.user
        # 1. Receive the request     user,address_id,pay_method
        data=json.loads(request.body.decode())
        address_id=data.get('address_id')
        pay_method=data.get('pay_method')

        # 2. Validate the data
        if not all([address_id,pay_method]):
            return JsonResponse({'code':400,'errmsg':'Parameters are incomplete'})

        try:
            address=Address.objects.get(id=address_id)
        except Address.DoesNotExist:
            return JsonResponse({'code':400,'errmsg':'Parameters are incorrect'})

        # if pay_method not in [1,2]:   这么写是没有问题的。
        # From the perspective of code readability, it is quite poor. I don't understand what 1 means or what 2 means.

        if pay_method not in [OrderInfo.PAY_METHODS_ENUM['CASH'],OrderInfo.PAY_METHODS_ENUM['ALIPAY']]:
            return JsonResponse({'code': 400, 'errmsg': 'Parameters are incorrect'})
        # `order_id` is a primary key (generated by yourself) consisting of the current date and time
        # (year, month, day, hour, minute, second) plus a 9-digit user ID.
        from django.utils import timezone
        from datetime import datetime
        # datetime.strftime()
        # Year
        # month
        # day
        # Hour
        # Minute
        # Second
        # %f Microseconds
        # timezone.localtime() 2020-10-19 10:03:10
        order_id=timezone.localtime().strftime('%Y%m%d%H%M%S%f') + '%09d'%user.id

        # The payment status is determined by the payment method.
        # The code is correct, but the readability is poor.
        # if pay_method == 1: # Cash on delivery
        #     pay_status=2
        # else:
        #     pay_status=1

        if pay_method == OrderInfo.PAY_METHODS_ENUM['CASH']:
            status=OrderInfo.ORDER_STATUS_ENUM['UNSEND']
        else:
            status=OrderInfo.ORDER_STATUS_ENUM['UNPAID']

        # Total quantity, total amount = 0
        total_count=0
        from decimal import Decimal
        total_amount=Decimal('0')        # Total amount
        # Shipping fee
        freight=Decimal('10.00')

        with transaction.atomic():

            # Transaction start point
            point = transaction.savepoint()

            # 3. Data storage: Generate orders (order basic information table and order product information table)
            #     1. First, save the order's basic information.
            orderinfo=OrderInfo.objects.create(
                order_id=order_id,
                user=user,
                address=address,
                total_count=total_count,
                total_amount=total_amount,
                freight=freight,
                pay_method=pay_method,
                status=status
            )
            #     2 Then, save the order's product information.
            #       2.1 Connect to Redis
            redis_cli=get_redis_connection('carts')
            #       2.2 Retrieve the hash
            sku_id_counts=redis_cli.hgetall('carts_%s'%user.id)
            #       2.3 Retrieve the set
            selected_ids=redis_cli.smembers('selected_%s'%user.id)
            #       2.4 Iterate over the selected product IDs
            carts={}
            #         It’s best to reorganize the data into a format representing the selected product information.
            #         {sku_id:count,sku_id:count}
            for sku_id in selected_ids:
                carts[int(sku_id)]=int(sku_id_counts[sku_id])

            ##         {sku_id:count,sku_id:count}
            #       2.5 Iterate over
            for sku_id,count in carts.items():

                # for i in range(10):
                while True:
                    # Query based on the selected product IDs
                    sku=SKU.objects.get(id=sku_id)
                    #       2.6 Check if the inventory is sufficient
                    if sku.stock<count:

                        # Rollback point
                        transaction.savepoint_rollback(point)

                        #       2.7 If the inventory is insufficient, the order fails.
                        return JsonResponse({'code':400,'errmsg':'Insufficient stock'})

                    from time import sleep
                    sleep(7)
                    #       2.8 If stock is sufficient, reduce the inventory and increase the sales.
                    # sku.stock -= count
                    # sku.sales += count
                    # sku.save()  # Remember to save it.

                    # 1. First, record a specific piece of data; it can be any data.
                    # Old inventory: We use this record as a reference.
                    old_stock=sku.stock

                    # 2. When updating, compare the record to ensure its accuracy.
                    new_stock=sku.stock-count
                    new_sales=sku.sales+count

                    result=SKU.objects.filter(id=sku_id,stock=old_stock).update(stock=new_stock,sales=new_sales)
                    # `result = 1` indicates that 1 record was successfully modified.
                    # `result = 0` indicates that no updates were made.

                    if result == 0:
                        # sleep(0.005)
                        continue
                        # Temporarily roll back and return an order failure.
                        # transaction.savepoint_rollback(point)
                        # return JsonResponse({'code':400,'errmsg':'Order failed~~~~~~~'})

                    #       2.9 Accumulate the total quantity and total amount.
                    orderinfo.total_count+=count
                    orderinfo.total_amount+=(count*sku.price)

                    #       2.10 Save the order item information.
                    OrderGoods.objects.create(
                        order=orderinfo,
                        sku=sku,
                        count=count,
                        price=sku.price
                    )
                    break
            #   3. Update the total amount and total quantity of the order.
            orderinfo.save()
            # Submission point
            transaction.savepoint_commit(point)

        #   4. Temporarily defer the removal of selected item information from Redis.
        # 4. Return response.
        return JsonResponse({'code':0,'errmsg':'ok','order_id':order_id})

"""
Resolving Concurrency Issues with Overselling:

① Queues

② Locks

Pessimistic Locking: When querying a record, the database locks the record so that others cannot operate on it while it is locked.

Characteristics: Pessimistic locking is similar to mutex locks used in multithreading, and it can easily lead to deadlock situations.
Example:

A: 1, 3, 5, 7
B: 2, 4, 7, 5
Optimistic Locking: Optimistic locking is not a real lock. It checks whether the inventory at the time of update is the same as the inventory previously queried. If it is the same, it means no one else has made changes, so the update can proceed; otherwise, if someone else has modified it, the update will be rejected.

Example:

There are 10 meat buns on the table: 9, 8
There are 5 people, and only the first one who runs 1 km is eligible to eat a meat bun.
5, 4, 3
Steps:

Record some data initially
When updating, compare the recorded data to see if it is still valid
MySQL Database Transaction Isolation Levels:

Serializable: Transactions are executed one at a time. This level is rarely used.
Repeatable Read: Data read within a transaction remains consistent, regardless of other transactions' modifications and commits.
Read Committed: A transaction reads data only after other transactions have committed changes to it.
Read Uncommitted: A transaction can see changes made by other transactions even if they haven't been committed yet.
Example:

Inventory: 5, 7, initial value is 8
A: 5, 7, actual inventory is 5
B: 7, 5, actual inventory is 5
MySQL Database Default Isolation Level: Repeatable Read
         

"""