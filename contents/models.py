from django.db import models
from utils.models import BaseModel
# Create your models here.
class ContentCategory(BaseModel):
    """Advertisement content categories"""
    name = models.CharField(max_length=50, verbose_name='Name')
    key = models.CharField(max_length=50, verbose_name='Category key name')

    class Meta:
        db_table = 'tb_content_category'
        verbose_name = 'Advertisement content category'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class Content(BaseModel):
    """Advertisement content"""
    category = models.ForeignKey(ContentCategory, on_delete=models.PROTECT, verbose_name='Category')
    title = models.CharField(max_length=100, verbose_name='Title')
    url = models.CharField(max_length=300, verbose_name='Content link')
    image = models.ImageField(null=True, blank=True, verbose_name='Image')
    text = models.TextField(null=True, blank=True, verbose_name='Content')
    sequence = models.IntegerField(verbose_name='Sorting')
    status = models.BooleanField(default=True, verbose_name='Whether to display')

    class Meta:
        db_table = 'tb_content'
        verbose_name = 'Advertisement content'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.category.name + ': ' + self.title