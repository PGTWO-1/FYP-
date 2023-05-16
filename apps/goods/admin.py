from django.contrib import admin
from .models import GoodsType, GoodsSKU, Goods, GoodsImage, IndexTypeGoodsBanner, IndexGoodsBanner, IndexPromotionBanner


class GoodsInfoAdmin(admin.ModelAdmin):
    admin.site.register(Goods)
    admin.site.register(GoodsType)
    admin.site.register(GoodsSKU)
    admin.site.register(GoodsImage)
    admin.site.register(IndexGoodsBanner)
    admin.site.register(IndexTypeGoodsBanner)
    admin.site.register(IndexPromotionBanner)
# Register your models here.
