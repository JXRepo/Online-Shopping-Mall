from django.shortcuts import render

# Create your views here.
"""
About the analysis of the model
1. Analyze as many fields as possible according to the page effect
2. Analyze whether it is stored in one table or multiple tables (more examples)

When analyzing the relationship between tables, do not exceed 3 tables at most

Many-to-many (usually 3 tables)

Students and teachers

Student table
stu_id stu_name

100 Tom

200 Bruce

Teacher table
teacher_id teacher_name
666 Teacher Niu
999 Teacher Qi

Third table

stu_id teacher_id
100 666
100 999
200 666
200 999

Analysis of the product day01 model --》 Fdfs (used to save pictures, videos and other files) --》 Learn Docker to deploy Fdfs


"""

############Code for uploading pictures################################
# from fdfs_client.client import Fdfs_client
#
# # 1. Creating a Client
# # Modify the path for loading configuration files
# client=Fdfs_client('utils/fastdfs/client.conf')
#
# # 2. upload image
# # The absolute path to the image
# client.upload_by_filename('/home/ubuntu/Desktop/img/c.png')

# 3. Get file_id .upload_by_filename Upload successfully and return dictionary data
# There is file_id in the dictionary data
"""
{'Group name': 'group1', 'Remote file_id': 'group1/M00/00/02/wKgTgF-FCP-AHcq2AAMTeyk-Y3M402.png', 
'Status': 'Upload successed.', 'Local file name': '/home/ubuntu/Desktop/img/c.png', 
'Uploaded size': '196.00KB', 'Storage IP': '192.168.19.128'}

"""

from django.views import View
from utils.goods import get_categories
from apps.contents.models import ContentCategory

class IndexView(View):

    def get(self,request):

        """
        The data on the homepage is divided into 2 parts
        Part 1 is product classification data
        Part 2 is advertising data

        """
        # 1. Product classification data
        categories=get_categories()
        # 2. Advertising data
        contents = {}
        content_categories = ContentCategory.objects.all()
        for cat in content_categories:
            contents[cat.key] = cat.content_set.filter(status=True).order_by('sequence')

        # Our homepage will explain page staticization later
        # We pass the data to the template
        context = {
            'categories': categories,
            'contents': contents,
        }
        # Templates are rarely used, and you will naturally learn how to use them when you arrive at the company.
        return render(request,'index.html',context)

"""
Requirements:
    According to the category clicked, get the category data (with sorting and paging)
Front-end:
    The front-end will send an axios request, the category id is in the route,
    The paging page number (which page of data), the number of data per page, and the sorting will also be passed
Back-end:
    Request Receive parameters
    Business logic Query data according to requirements and convert object data into dictionary data
    
Response JSON

Route GET /list/category_id/skus/
Steps
1. Receive parameters
2. Get the category id
3. Query and verify the category data according to the category id
4. Get breadcrumb data
5. Query the sku data corresponding to the category, then sort, and then paginate
6. Return the response
"""
from apps.goods.models import GoodsCategory
from django.http import JsonResponse
from utils.goods import get_breadcrumb
from apps.goods.models import SKU
class ListView(View):

    def get(self,request,category_id):
        # 1. Receiving parameters
        # Sort Field
        ordering=request.GET.get('ordering')
        # How many records per page
        page_size=request.GET.get('page_size')
        # Which page of data do you want
        page=request.GET.get('page')

        # 2. Get category id
        # 3. Query and verify the classification data based on the classification ID
        try:
            category=GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            return JsonResponse({'code':400,'errmsg':'Missing parameters'})
        # 4. Get breadcrumb data
        breadcrumb=get_breadcrumb(category)

        # 5. Query the sku data corresponding to the category, sort it, and then paginate it
        skus=SKU.objects.filter(category=category,is_launched=True).order_by(ordering)
        # Pagination
        from django.core.paginator import Paginator
        # object_list, per_page
        # object_list   List Data
        # per_page      How many records per page
        paginator=Paginator(skus,per_page=page_size)

        # Get the data of the specified page number
        page_skus=paginator.page(page)

        sku_list=[]
        # Convert object to dictionary data
        for sku in page_skus.object_list:
            sku_list.append({
                'id':sku.id,
                'name':sku.name,
                'price':sku.price,
                'default_image_url':sku.default_image.url
            })

        # Get the total page number
        total_num = paginator.num_pages

        # 6. Return Response
        return JsonResponse({'code':0,'errmsg':'ok','list':sku_list,'count':total_num,'breadcrumb':breadcrumb})


########################################################################


"""
We/data <----------Haystack---------> elasticsearch

We use haystack to connect to elasticsearch
So haystack can help us query data
"""
from haystack.views import SearchView
from django.http import JsonResponse


class SKUSearchView(SearchView):

    def create_response(self):
        # Get the results of the search
        context = self.get_context()
        # How do we know what data is inside???
        # Add breakpoints to analyze
        sku_list=[]
        for sku in context['page'].object_list:
            sku_list.append({
                'id':sku.object.id,
                'name':sku.object.name,
                'price': sku.object.price,
                'default_image_url': sku.object.default_image.url,
                'searchkey': context.get('query'),
                'page_size': context['page'].paginator.num_pages,
                'count': context['page'].paginator.count
            })

        return JsonResponse(sku_list,safe=False)


"""
Requirements:
    Details page
    
    1. Classification data
    2. Breadcrumbs
    3. SKU information
    4. Specification information

    Our details page also needs to be implemented statically.
    But before we explain staticization, we should be able to display the data of the details page first

"""
from utils.goods import get_categories
from utils.goods import get_breadcrumb
from utils.goods import get_goods_specs
class DetailView(View):

    def get(self,request,sku_id):
        try:
            sku=SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            pass
        # 1. Categorizing Data
        categories=get_categories()
        # 2. Bread crumbs
        breadcrumb=get_breadcrumb(sku.category)
        # 3. SKU Information
        # 4. Specifications
        goods_specs=get_goods_specs(sku)

        context = {

            'categories': categories,
            'breadcrumb': breadcrumb,
            'sku': sku,
            'specs': goods_specs,

        }
        return render(request,'detail.html',context)



"""
Requirements:
    Count the number of visits to classified products every day

Front-end:
    When visiting a specific page, an axios request will be sent. Carry the category id
    
Back-end:
    Request: Receive the request and get the parameters
    Business logic: Check if there is any, if so, update the data, if not, create new data
    Response: Return JSON

Route: POST detail/visit/<category_id>/
    Steps:
    
    1. Receive the category id
    2. Verify the parameters (verify the category id)
    3. Check if there are any records in this category on the day
    4. No new data
    5. Update the data if yes
    6. Return the response
    

"""
from apps.goods.models import GoodsVisitCount
from datetime import date
class CategoryVisitCountView(View):

    def post(self,request,category_id):
        # 1. Receive category id
        # 2. Verification parameters (verification category id)
        try:
            category=GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            return JsonResponse({'code':400,'errmsg':'No such category'})
        # 3. Check if there are any records in this category on that day

        today=date.today()
        try:
            gvc=GoodsVisitCount.objects.get(category=category,date=today)
        except GoodsVisitCount.DoesNotExist:
            # 4. No new data
            GoodsVisitCount.objects.create(category=category,
                                           date=today,
                                           count=1)
        else:
            # 5. Update data if any
            gvc.count+=1
            gvc.save()
        # 6. Return Response
        return JsonResponse({'code':0,'errmsg':'ok'})

