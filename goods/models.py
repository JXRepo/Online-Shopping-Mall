from django.db import models
from utils.models import BaseModel

class GoodsCategory(BaseModel):
    """Product category"""
    name = models.CharField(max_length=10, verbose_name='Name')
    parent = models.ForeignKey('self', related_name='subs', null=True, blank=True, on_delete=models.CASCADE, verbose_name='Parent category')

    class Meta:
        db_table = 'tb_goods_category'
        verbose_name = 'Product category'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class GoodsChannelGroup(BaseModel):
    """Product channel group"""
    name = models.CharField(max_length=20, verbose_name='Channel group name')

    class Meta:
        db_table = 'tb_channel_group'
        verbose_name = 'Product channel group'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class GoodsChannel(BaseModel):
    """Product channel"""
    group = models.ForeignKey(GoodsChannelGroup, on_delete=models.CASCADE, verbose_name='Channel group name')
    category = models.ForeignKey(GoodsCategory, on_delete=models.CASCADE, verbose_name='Top-level product category')
    url = models.CharField(max_length=50, verbose_name='Channel page link')
    sequence = models.IntegerField(verbose_name='Order within the group')

    class Meta:
        db_table = 'tb_goods_channel'
        verbose_name = 'Product channel'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.category.name


class Brand(BaseModel):
    """Brand"""
    name = models.CharField(max_length=20, verbose_name='Name')
    logo = models.ImageField(verbose_name='Logo image')
    first_letter = models.CharField(max_length=1, verbose_name='Brand initials')

    class Meta:
        db_table = 'tb_brand'
        verbose_name = 'Brand'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class SPU(BaseModel):
    """Product SPU (Stock Keeping Unit)"""
    name = models.CharField(max_length=50, verbose_name='Name')
    brand = models.ForeignKey(Brand, on_delete=models.PROTECT, verbose_name='Brand')
    category1 = models.ForeignKey(GoodsCategory, on_delete=models.PROTECT, related_name='cat1_spu', verbose_name='Primary category')
    category2 = models.ForeignKey(GoodsCategory, on_delete=models.PROTECT, related_name='cat2_spu', verbose_name='Secondary category')
    category3 = models.ForeignKey(GoodsCategory, on_delete=models.PROTECT, related_name='cat3_spu', verbose_name='Tertiary category')
    sales = models.IntegerField(default=0, verbose_name='Sales volume')
    comments = models.IntegerField(default=0, verbose_name='Number of reviews')
    desc_detail = models.TextField(default='', verbose_name='Detailed description')
    desc_pack = models.TextField(default='', verbose_name='Packaging information')
    desc_service = models.TextField(default='', verbose_name='After-sales service')

    class Meta:
        db_table = 'tb_spu'
        verbose_name = 'Product SPU (Stock Keeping Unit)'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class SKU(BaseModel):
    """Product SKU (Stock Keeping Unit)"""
    name = models.CharField(max_length=50, verbose_name='Name')
    caption = models.CharField(max_length=100, verbose_name='Subtitle')
    spu = models.ForeignKey(SPU, on_delete=models.CASCADE, verbose_name='Product')
    category = models.ForeignKey(GoodsCategory, on_delete=models.PROTECT, verbose_name='Subcategory')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Unit price')
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Cost price')
    market_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Market price')
    stock = models.IntegerField(default=0, verbose_name='Stock quantity')
    sales = models.IntegerField(default=0, verbose_name='Sales volume')
    comments = models.IntegerField(default=0, verbose_name='Number of reviews')
    is_launched = models.BooleanField(default=True, verbose_name='Is it on sale')
    default_image = models.ImageField(max_length=200, default='', null=True, blank=True, verbose_name='Default image')

    class Meta:
        db_table = 'tb_sku'
        verbose_name = 'Product SKU'
        verbose_name_plural = verbose_name

    def __str__(self):
        return '%s: %s' % (self.id, self.name)


class SKUImage(BaseModel):
    """SKU Image"""
    sku = models.ForeignKey(SKU, on_delete=models.CASCADE, verbose_name='sku')
    image = models.ImageField(verbose_name='picture')

    class Meta:
        db_table = 'tb_sku_image'
        verbose_name = 'SKU Image'
        verbose_name_plural = verbose_name

    def __str__(self):
        return '%s %s' % (self.sku.name, self.id)


class SPUSpecification(BaseModel):
    """Product SPU Specifications"""
    spu = models.ForeignKey(SPU, on_delete=models.CASCADE, related_name='specs', verbose_name='Commodity SPU')
    name = models.CharField(max_length=20, verbose_name='Specification name')

    class Meta:
        db_table = 'tb_spu_specification'
        verbose_name = 'Product SPU Specifications'
        verbose_name_plural = verbose_name

    def __str__(self):
        return '%s: %s' % (self.spu.name, self.name)


class SpecificationOption(BaseModel):
    """Specification options"""
    spec = models.ForeignKey(SPUSpecification, related_name='options', on_delete=models.CASCADE, verbose_name='Specification')
    value = models.CharField(max_length=20, verbose_name='Option Value')

    class Meta:
        db_table = 'tb_specification_option'
        verbose_name = 'Specification options'
        verbose_name_plural = verbose_name

    def __str__(self):
        return '%s - %s' % (self.spec, self.value)


class SKUSpecification(BaseModel):
    """SKU Specific Specifications"""
    sku = models.ForeignKey(SKU, related_name='specs', on_delete=models.CASCADE, verbose_name='sku')
    spec = models.ForeignKey(SPUSpecification, on_delete=models.PROTECT, verbose_name='Specification name')
    option = models.ForeignKey(SpecificationOption, on_delete=models.PROTECT, verbose_name='Specification Value')

    class Meta:
        db_table = 'tb_sku_specification'
        verbose_name = 'SKU Specifications'
        verbose_name_plural = verbose_name

    def __str__(self):
        return '%s: %s - %s' % (self.sku, self.spec.name, self.option.value)


"""
Problem:
The project did not perform migration. The corresponding table already exists in the database
    

"""
class GoodsVisitCount(BaseModel):
    """Statistical classification product visit volume model class"""
    category = models.ForeignKey(GoodsCategory, on_delete=models.CASCADE, verbose_name='Categories')
    count = models.IntegerField(verbose_name='Views', default=0)
    date = models.DateField(auto_now_add=True, verbose_name='Statistical date')

    class Meta:
        db_table = 'tb_goods_visit'
        verbose_name = 'Statistics of classified product visits'
        verbose_name_plural = verbose_name