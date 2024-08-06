from django.db import models

# Create your models here.
from django.db import models

class Area(models.Model):
    """Province, City, District"""
    name = models.CharField(max_length=20, verbose_name='Name')
    parent = models.ForeignKey('self', on_delete=models.SET_NULL,
                               related_name='subs',
                               null=True, blank=True, verbose_name='Superior Administrative Division')
    # subs = [Area,Area,Area]
    #  related_name Name of the Associated Model
    # By default, it is the lowercase of the associated model class name followed by _set     area_set
    # We can change the default name by using related_name; it is now changed to subs.

    class Meta:
        db_table = 'tb_areas'
        verbose_name = 'Province, City, District'
        verbose_name_plural = 'Province, City, District'

    def __str__(self):
        return self.name


"""
Province, City, District


id          name            parent_id

10000       A Province             NULL

10100       B City             10000
10200       C City            10000
10300       D City             10000


10101       A Province              10100
10102       B Province             10100



Query province information
 select * from tb_areas where parent_id is NULL;
 
 Area.objects.filter(parent=None)
 Area.objects.filter(parent__isnull=True)
 Area.objects.filter(parent_id__isnull=True)


Query city information
select * from tb_areas where parent_id=130000;

    Area.objects.filter(parent_id=130000)
    Area.objects.filter(parent=130000)
    
    >>> province=Area.objects.get(id=130000)  # Province
    >>> province.subs.all()                   # City


Query district information
select * from tb_areas where parent_id=130600;
    
    Area.objects.filter(parent_id=130600)
    Area.objects.filter(parent=130600)
    
    >>> city=Area.objects.get(id=130600)   # City
    >>> city.subs.all()                    # District/County
    
"""