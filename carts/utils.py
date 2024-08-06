"""
**Requirement:**
During login, merge cookie data into Redis.

**Front-end:**

**Back-end:**
- **Request:** Retrieve cookie data during login.
- **Business Logic:** Merge into Redis.
- **Response:**

**Abstract Problem Specific Example:**
1. Read cookie data.
2. Initialize a dictionary to store `sku_id:count`.
   Initialize a list to store selected product IDs.
   Initialize a list to store unselected product IDs.
3. Iterate through cookie data.
4. Add dictionary data and list data to Redis.
5. Delete cookie data.

#######################################

redis       hash
                    1:10
                    3:10
            set
                    1

cookie
        {
            1: {count:666,selected:True},
            2: {count:999,selected:True},
            5: {count:999,selected:False},
        }

hash
1:666       1
2:999       1

1. When there are items with the same ID in both cookie data and Redis data,
what about the quantity? We use the quantity from the cookie.

2. When there are items in the cookie data that are not in Redis data,
all items should be taken from the cookie.

3. When there are items in Redis data that are not in the cookie data,
no action is taken.

"""
import pickle
import base64

from django_redis import get_redis_connection


def merge_cookie_to_redis(request,response):
    """
    **Abstract Problem Specific Example:**

1. Read cookie data.
2. Initialize a dictionary to store `sku_id:count`.
   Initialize a list to store selected product IDs.
   Initialize a list to store unselected product IDs.
3. Iterate through cookie data.
4. Add the dictionary data and list data to Redis.
5. Delete cookie data.
    :return:
    """
    # 1. Read cookie data
    cookie_carts = request.COOKIES.get('carts')

    if cookie_carts is not None:
        carts=pickle.loads(base64.b64decode(cookie_carts))

        # 2. Initialize a dictionary to save sku_id:count
        # {sku_id:count,sku_id:count,....}
        cookie_dict={}
        # Initialize a list to save the selected product ID
        selected_ids=[]
        # Initialize a list to save the unselected product IDs
        unselected_ids=[]

        # 3. Traversing cookie data
        """
        {
            1: {count:666,selected:True},
            2: {count:999,selected:True},
            5: {count:999,selected:False},
        }
        """
        for sku_id,count_selected_dict in carts.items():
            # 1: {count:666,selected:True},
            # Dictionary data
            cookie_dict[sku_id]=count_selected_dict['count']
            if count_selected_dict['selected']:
                selected_ids.append(sku_id)
            else:
                unselected_ids.append(sku_id)
        user=request.user
        # 4. Add dictionary data and list data to redis respectively
        redis_cli=get_redis_connection('carts')
        pipeline=redis_cli.pipeline()
        #  {sku_id:count,sku_id:count,....}
        pipeline.hmset('carts_%s'%user.id,cookie_dict)
        # selected_id [1,3,2]
        if len(selected_ids)>0:
            # *selected_ids  Unpacking list data
            pipeline.sadd('selected_%s'%user.id,*selected_ids)
        # unselected_id [4,5,6]
        if len(unselected_ids)>0:
            pipeline.srem('selected_%s'%user.id,*unselected_ids)

        pipeline.execute()

        # 5. Deleting cookie data
        response.delete_cookie('carts')

    # response better to return
    return response