from django.shortcuts import render
from django.views.generic import View
from .models import GoodsType, IndexTypeGoodsBanner, IndexPromotionBanner, IndexGoodsBanner


class IndexView(View):
    def get(self, request):
        types = GoodsType.objects.all()
        goods_banners = IndexGoodsBanner.objects.all().order_by('index')
        promotion_banners = IndexPromotionBanner.objects.all().order_by('index')
        for type in types:
            image_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=1).order_by('index')
            title_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=0).order_by('index')
            type.image_banners = image_banners
            type.title_banners = title_banners


        cart_count = 0
        dict = {'types': types,
                'goods_banners': goods_banners,
                'promotion_banners': promotion_banners,
                'cart_count': cart_count
                }
        return render(request, 'index.html', dict)
