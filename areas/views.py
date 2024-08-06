from django.shortcuts import render

# Create your views here.
from django.views.generic.base import View

"""
Requirement：
    Get province information
Front-end：
    When the page loads, an Axios request will be sent to retrieve province information
Back-end：
    Request：         No request parameters needed
    Business logic：       Query province information
    Response：         JSON
    
    Route：         areas/
    Steps：
        1. Query province information
        2. Convert the object to dictionary data
        3. Return the response
"""
from apps.areas.models import Area
from django.http import JsonResponse
from django.core.cache import cache

class AreaView(View):

    def get(self,request):

        # First, query the cached data
        province_list=cache.get('province')
        # If there is no cache, query the database and cache the data
        if province_list is None:
            # 1. Query province information
            provinces=Area.objects.filter(parent=None)
            # Query result set

            # 2. Convert the object to dictionary data
            province_list = []
            for province in provinces:
                province_list.append({
                    'id':province.id,
                    'name':province.name
                })

            # Save the cached data
            # cache.set(key,value,expire)
            cache.set('province',province_list,24*3600)
        # 3. Return the response
        return JsonResponse({'code':0,'errmsg':'ok','province_list':province_list})


"""
Requirement：
    Get city and district information
Front-end：
    When the page changes the province or city, an Axios request will be sent to retrieve the information for the next level
Back-end：
    Request：         The province ID and city ID need to be passed.
    Business logic：       Query information based on the ID, and convert the result set to a list of dictionaries.
    Response：         JSON

    Route：         areas/id/
    Steps：
        1. Get the province ID and city ID, and query the information.
        2. Convert the object to dictionary data
        3. Return the response
"""

class SubAreaView(View):

    def get(self,request,id):

        # First, retrieve the cached data
        data_list=cache.get('city:%s'%id)

        if data_list is None:
            # 1. Retrieve the province ID and city ID, then query the information.
            # Area.objects.filter(parent_id=id)
            # Area.objects.filter(parent=id)

            up_level = Area.objects.get(id=id)  #
            down_level=up_level.subs.all()  #
            # 2. Convert the object to dictionary data
            data_list=[]
            for item in down_level:
                data_list.append({
                    'id':item.id,
                    'name':item.name
                })

            # Cache data
            cache.set('city:%s'%id,data_list,24*3600)

        # 3. Return the response
        return JsonResponse({'code':0,'errmsg':'ok','sub_data':{'subs':data_list}})

# Example: Online Mall
# 1 billion registered users
# Daily active users: 1% (1 million)
# Order rate: 1% (10,000)
# Probability of adding a new address: 1%   100 addresses    300 times    2 times

# For data that does not change frequently, it is best to cache it in Redis (content) to reduce database queries

# 5 minutes