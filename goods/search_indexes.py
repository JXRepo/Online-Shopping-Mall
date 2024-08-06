from apps.goods.models import SKU
from haystack import indexes

"""
0. We need to create a search_indexes.py file in the sub-application corresponding to the model. 
This makes it easier for haystack to retrieve data
1. The index class must inherit from indexes.SearchIndex, indexes.Indexable
2. A field document=True must be defined
The field name can be anything. text is just a convention (everyone is used to doing this).
All indexes have the same field
3. use_template=True
Allows us to set up a separate file to specify which fields to search

Where is this separate file created? ? ?
Template folder/search/indexes/sub-application name directory/model class name lowercase_text.txt

Data <----------Haystack---------> elasticsearch

Operation: We should let haystack get the data to es to generate the index

In a virtual environment python manage.py rebuild_index
    
"""
class SKUIndex(indexes.SearchIndex, indexes.Indexable):

    text = indexes.CharField(document=True, use_template=True)


    def get_model(self):
        """Returns the indexed model class"""
        return SKU

    def index_queryset(self, using=None):
        """Returns the data query set to be indexed"""
        return self.get_model().objects.all()
        # return SKU.objects.all()

