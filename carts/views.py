import json

from django.http import JsonResponse
from django.shortcuts import render

# Create your views here.
from django.views import View
from django_redis import get_redis_connection

"""
1.  A's website allows logged-in users to access the shopping cart, while unlogged-in users can access the shopping cart      v
    B's website must be a logged-in user to access the shopping cart
    
2.  Where is the logged-in user data stored? On the server        mysql/redis
                                        mysql
                                        redis           Learning, shopping cart frequent additions, deletions, modifications and checks
                                        mysql+redis
    Where is the data of non-logged-in users stored? Client
                                        cookie      

3.  What data is saved???
    
    redis:
            user_id,sku_id(Product ID),count(number),selected（Selected state）
    
    cookie:
            sku_id,count,selected,
    
4.  Organization of data

    redis:
            user_id,    sku_id(Product ID),count(number),selected（Selected state）
            
            hash
            user_id:
                    sku_id:count
                    xxx_sku_id:selected
                    
            1：  
                    1:10
                    xx_1: True
                    
                    2:20
                    xx_2: False
                    
                    3:30
                    xx_3: True
            13 places of space
            
            Further optimization!!!
            Why optimize? ? ?
            Redis data is stored in memory. We should try to occupy as little space as possible in redis
            
            user_id:
                    sku_id:count
                    
            
            selected 
            
            
            
            user_1:         id: number
                            1: 10 
                            2: 20
                            3: 30
            Record selected products
            1,3
            
            
            
            user_1
                    1: 10 
                    2: 20
                    3: 30
            selected_1: {1,3}
            
            10 spaces
            
            
             user_1
                    1: 10 
                    2: -20
                    3: 30
            
            7 spaces
            
    cookie:
        {
            sku_id: {count:xxx,selected:xxxx},
            sku_id: {count:xxx,selected:xxxx},
            sku_id: {count:xxx,selected:xxxx},
        }
        

5.
    The cookie dictionary is converted to a string and saved, and the data is not encrypted
    
    
    base64：         6 bits as a unit
    
    1G=1024MB
    1MB=1024KB
    1KB=1024B
    
    1B=8bytes
    
    bytes 0 or 1
    
    ASCII
    
    a 
    0110 0001
    
    a               a       a                   24 bits
    0110 0001  0110 0001   0110 0001 
    
    011000      010110      000101          100001 
    X               Y       Z                  N
    
    aaa --> XYZN
    
    Base64 module usage：
        base64.b64encode()Encode the bytes type data in base64 and return the encoded bytes type data
        base64.b64deocde()Decode the base64-encoded bytes data and return the decoded bytes data.
    
    
    
    dictionary ----》 pickle ------Binary------》Base64 encoding
    
    The pickle module uses:
        pickle.dumps() to serialize Python data into bytes type data.
        pickle.loads() to deserialize bytes type data into Python data.

#######################Encoding Data####################################
# dictionary
carts = {
    '1': {'count':10,'selected':True},
    '2': {'count':20,'selected':False},
}


# Convert dictionary to bytes type
import pickle
b=pickle.dumps(carts)

# Base64 encoding of bytes type data
import base64
encode=base64.b64encode(b)

#######################Decoding the data####################################

# Decode base64 encoded data
decode_bytes=base64.b64decode(encode)

# Then convert the decoded data into a dictionary
pickle.loads(decode_bytes)

6.
Request
Business logic (add, delete, modify, and query data)
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

Check (personal center data display, province, city and district)
1. Query the specified data
2. Convert object data to dictionary data
3. Return response

"""
from apps.goods.models import SKU
import pickle
import base64

class CartsView(View):

    """
Front-end:
    After we click Add to Cart, the front-end sends the product id and quantity to the back-end

Back-end:
    Request: Receive parameters, verify parameters
    Business logic: Query the database based on the product id to see if the product id is correct
    Data storage
    Logged-in user enters redis
        Connect to redis
        Get user id
        hash
        set
        Return response
    Unlogged-in user enters cookie
        First have a cookie dictionary
        Dictionary converted to bytes
        Bytes type data base64 encoding
        Set cookie
        Return response
Response: Return JSON
Route: POST /carts/
Steps:
    1. Receive data
    2. Verify data
    3. Determine the user's login status
    4. Logged-in user saves redis
        4.1 Connect to redis
        4.2 Operate hash
        4.3 Operate set
        4.4 Return response
    5. Unlogged-in user saves cookie
        5.1 First have a cookie dictionary
        5.2 Dictionary converted to bytes
        5.3 Bytes type data base64 encoding
        5.4 Setting cookies
        5.5 Returning responses


    """
    def post(self,request):
        # 1. Receive data
        data=json.loads(request.body.decode())
        sku_id=data.get('sku_id')
        count=data.get('count')
        # 2. verify the data

        try:
            sku=SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return JsonResponse({'code':400,'errmsg':'No such product found'})

        # Type Coercion
        try:
            count=int(count)
        except Exception:
            count=1
        # 3. Determine the user's login status
        # request.user If it is a logged-in user, it is the model data associated with User
        # is_authenticated = True Authenticate user
        # If it is not a logged-in user, it is an anonymous user
        # is_authenticated = False for anonymous users
        #
        user=request.user
        if user.is_authenticated:
            # 4. Login user saves redis
            #     4.1 连接redis
            redis_cli=get_redis_connection('carts')

            pipeline=redis_cli.pipeline()
            #     4.2 Manipulating hashes
            # redis_cli.hset(key,field,value)
            # 1. First get the previous data, then accumulate
            # 2.
            # redis_cli.hset('carts_%s'%user.id,sku_id,count)
            # hincrby
            # Accumulation operation will be performed
            pipeline.hincrby('carts_%s'%user.id,sku_id,count)
            #     4.3 Operation set
            # The default is selected
            pipeline.sadd('selected_%s'%user.id,sku_id)

            # Must be executed!!!
            pipeline.execute()
            #     4.4 Return Response
            return JsonResponse({'code':0,'errmsg':'ok'})
        else:
            # 5. Save cookies for non-logged in users
            """
                       
                cookie:
                    {
                        sku_id: {count:xxx,selected:xxxx},
                        sku_id: {count:xxx,selected:xxxx},
                        sku_id: {count:xxx,selected:xxxx},
                    }
        
            """
            # {16： {count:3,selected:True}}

            # 5.0 Read cookie data first
            cookie_carts=request.COOKIES.get('carts')
            if cookie_carts:
                # Decrypting encrypted data
                carts = pickle.loads(base64.b64decode(cookie_carts))
            else:
                #     5.1 First there is a cookie dictionary
                carts={}

            # Determine whether the newly added product is in the shopping cart
            if sku_id in carts:
                # The product ID is already in the shopping cart
                # Quantity accumulation
                ## {16： {count:3,selected:True}}
                origin_count=carts[sku_id]['count']
                count+=origin_count

            #     carts[sku_id] = {
            #         'count':count,
            #         'selected':True
            #     }
            # else:
            # There is no product ID in the shopping cart
            # {16： {count:3,selected:True}}
            carts[sku_id]={
                'count':count,
                'selected':True
            }


            #     5.2 Convert dictionary to bytes

            carts_bytes=pickle.dumps(carts)
            #     5.3 Base64 encoding of bytes type data

            base64encode=base64.b64encode(carts_bytes)
            #     5.4 Setting cookies
            response = JsonResponse({'code': 0, 'errmsg': 'ok'})
            # key, value='', max_age=None
            # The function of base64encode.decode() is to convert bytes to str
            # Because the value data is str data
            response.set_cookie('carts',base64encode.decode(),max_age=3600*24*12)
            #     5.5 Return Response
            return response


    """
    1. Determine whether the user is logged in
    2. Logged-in user queries redis
        2.1 Connect to redis
        2.2 hash {sku_id:count}
        2.3 set {sku_id}
        2.4 Traversal judgment
        2.5 Query product information based on product id
        2.6 Convert object data to dictionary data
        2.7 Return response
    3. Unlogged-in user queries cookie
        3.1 Read cookie data
        3.2 Determine whether shopping cart data exists
        If it exists, decode {sku_id:{count:xxx,selected:xxx}}
        If it does not exist, initialize an empty dictionary
        3.3 Query product information based on product id
        3.4 Convert object data to dictionary data
        3.5 Return response

    1. Determine whether the user is logged in
    2. Logged-in user queries redis
        2.1 Connect to redis
        2.2 hash {sku_id:count}
        2.3 set {sku_id}
        2.4 Traversal judgment
    3. Query cookies for non-logged-in users
        3.1 Read cookie data
        3.2 Determine whether shopping cart data exists
        If it exists, decode {sku_id:{count:xxx,selected:xxx}}
        If it does not exist, initialize an empty dictionary
    
    4 Query product information based on product id
    5 Convert object data to dictionary data
    6 Return response
        
    """
    def get(self,request):
        # 1. Determine if the user is logged in
        user=request.user
        if user.is_authenticated:

            # 2. Query Redis for logged-in users
            #     2.1 Connect to Redis
            redis_cli=get_redis_connection('carts')
            #     2.2 hash        {2:count,3:count,...}
            sku_id_counts=redis_cli.hgetall('carts_%s'%user.id)
            #     2.3 set         {2}
            selected_ids=redis_cli.smembers('selected_%s'%user.id)
            #     2.4 Convert Redis data to be like cookies
            #    This way, you can handle subsequent operations uniformly.
            # {sku_id:{count:xxx,selected:xxx}}
            carts={}

            for sku_id,count in sku_id_counts.items():
                carts[int(sku_id)]={
                    'count':int(count),
                    'selected': sku_id in selected_ids
                }
        else:
            # 3. Query cookies for users who are not logged in
            #     3.1 Read cookie data
            cookie_carts=request.COOKIES.get('carts')
            #     3.2 Check if there is shopping cart data
            if cookie_carts is not None:
                #         If it exists, decode it            {sku_id:{count:xxx,selected:xxx}}
               carts = pickle.loads(base64.b64decode(cookie_carts))
            else:
                #         If it does not exist, initialize an empty dictionary
                carts={}

        #{sku_id: {count: xxx, selected: xxx}}
        # 4 Query product information based on the product ID
        # You can directly iterate over `carts`
        # You can also get the top-level keys of the dictionary; all top-level keys represent product IDs.
        sku_ids=carts.keys()
        # [1,2,3,4,5]
        # You can iterate and query.
        # You can also use the `in` operator.
        skus=SKU.objects.filter(id__in=sku_ids)

        sku_list=[]
        for sku in skus:
            # 5 Convert object data to dictionary data
            sku_list.append({
                'id':sku.id,
                'price':sku.price,
                'name':sku.name,
                'default_image_url':sku.default_image.url,
                'selected': carts[sku.id]['selected'],          # Selected state
                'count': int(carts[sku.id]['count']),                # Forcefully convert the quantity
                'amount': sku.price*carts[sku.id]['count']      # Total price
            })
        # 6 Return the response
        return JsonResponse({'code':0,'errmsg':'ok','cart_skus':sku_list})


    """
    1. Get user information
    2. Receive data
    3. Validate data
    4. For logged-in users, update Redis
       4.1 Connect to Redis
       4.2 Use hash
       4.3 Use set
       4.4 Return response
    5. For non-logged-in users, update cookies
       5.1 First, read shopping cart data
           - Check if it exists.
           - If it exists, decrypt the data.
           - If it does not exist, initialize an empty dictionary.
       5.2 Update data
       5.3 Re-encode the dictionary and base64 encrypt it
       5.4 Set cookie
       5.5 Return response
    """
    def put(self,request):
        # 1. Get user information
        user=request.user
        # 2. Receive data
        data=json.loads(request.body.decode())
        sku_id=data.get('sku_id')
        count=data.get('count')
        selected=data.get('selected')
        # 3. Validate data
        if not all([sku_id,count]):
            return JsonResponse({'code':400,'errmsg':'Incomplete parameters'})

        try:
            SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return JsonResponse({'code':400,'errmsg':'No such product'})

        try:
            count=int(count)
        except Exception:
            count=1

        if user.is_authenticated:
            # 4. Update Redis for logged-in users
            #     4.1 Connect to Redis
            redis_cli=get_redis_connection('carts')
            #     4.2 hash
            redis_cli.hset('carts_%s'%user.id,sku_id,count)
            #     4.3 set
            if selected:
                redis_cli.sadd('selected_%s'%user.id,sku_id)
            else:
                redis_cli.srem('selected_%s'%user.id,sku_id)
            #     4.4 Return the response
            return JsonResponse({'code':0,'errmsg':'ok','cart_sku':{'count':count,'selected':selected}})

        else:
            # 5. Update cookies for non-logged-in users
            #     5.1 First, read the shopping cart data
            cookie_cart=request.COOKIES.get('carts')
            #         Check if it exists
            if cookie_cart is not None:
                #         If it exists, decrypt the data
                carts=pickle.loads(base64.b64decode(cookie_cart))
            else:
                #         If it does not exist, initialize an empty dictionary
                carts={}

            #     5.2 Update data
            # {sku_id: {count:xxx,selected:xxx}}
            if sku_id in carts:
                carts[sku_id]={
                    'count':count,
                    'selected':selected
                }
            #     5.3 Re-encode the dictionary and base64 encrypt it
            new_carts=base64.b64encode(pickle.dumps(carts))
            #     5.4 Set the cookie
            response = JsonResponse({'code':0,'errmsg':'ok','cart_sku':{'count':count,'selected':selected}})
            response.set_cookie('carts',new_carts.decode(),max_age=14*24*3600)
            #     5.5 Return the response
            return response

    """
    1. Receive the request
    2. Validate parameters
    3. Based on user status
    4. For logged-in users, operate on Redis
       4.1 Connect to Redis
       4.2 Use hash
       4.3 Use set
       4.4 Return response
    5. For non-logged-in users, operate on cookies
       5.1 Read shopping cart data from the cookie
           - Check if data exists
           - If it exists, decode it
           - If it does not exist, initialize a dictionary
       5.2 Delete data {}
       5.3 Encode the dictionary data and apply base64 processing
       5.4 Set cookie
       5.5 Return response   
    """
    def delete(self,request):
        # 1. Receive the request
        data=json.loads(request.body.decode())
        # 2. Validate parameters
        sku_id=data.get('sku_id')
        try:
            SKU.objects.get(pk=sku_id)  # pk primary key
        except SKU.DoesNotExist:
            return JsonResponse({'code':400,'errmsg':'No such product'})
        # 3. Based on user status
        user=request.user
        if user.is_authenticated:

            # 4. Operate on Redis for logged-in users
            #     4.1 Connect to Redis
            redis_cli=get_redis_connection('carts')
            #     4.2 hash
            redis_cli.hdel('carts_%s'%user.id,sku_id)
            #     4.3 set
            redis_cli.srem('selected_%s'%user.id,sku_id)
            #     4.4 Return the response
            return JsonResponse({'code':0,'errmsg':'ok'})

        else:
            # 5. Operate on cookies for non-logged-in users
            #     5.1 Read shopping cart data from the cookie
            cookie_cart=request.COOKIES.get('carts')
            #     Check if the data exists
            if cookie_cart is not None:
                #     If it exists, decode it
                carts=pickle.loads(base64.b64decode(cookie_cart))
            else:
                #     If it does not exist, initialize a dictionary
                carts={}
            #     5.2 Delete data {}
            del carts[sku_id]
            #     5.3 We need to encode the dictionary data and apply base64 processing
            new_carts=base64.b64encode(pickle.dumps(carts))
            #     5.4 Set the cookie
            response=JsonResponse({'code':0,'errmsg':'ok'})
            response.set_cookie('carts',new_carts.decode(),max_age=14*24*3600)
            #     5.5 Return the response
            return response

