from django.shortcuts import render, redirect
from django.views.generic import View
from .models import GoodsType, IndexTypeGoodsBanner, IndexPromotionBanner, IndexGoodsBanner, GoodsSKU
from django_redis import get_redis_connection
from django.contrib.auth import authenticate
from apps.order.models import OrderGoods
from django.core.paginator import Paginator


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

        user = request.user
        cart_count = 0
        if user.is_authenticated:
            connection = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            cart_count = connection.hlen(cart_key)
        else:
            cart_count = 0
        dict = {'types': types,
                'goods_banners': goods_banners,
                'promotion_banners': promotion_banners,
                'cart_count': cart_count
                }
        return render(request, 'index.html', dict)


# /goods/商品id
class DetailView(View):
    def get(self, request, goods_id):
        try:
            sku = GoodsSKU.objects.get(id=goods_id)
            print(goods_id)
        except GoodsSKU.DoesNotExist:
            return redirect('goods:index')

        types = GoodsType.objects.all()
        sku_orders = OrderGoods.objects.filter(sku=sku)
        new_skus = GoodsSKU.objects.filter(type=sku.type).order_by('-create_times')
        user = request.user
        cart_count = 0
        if user.is_authenticated:
            connection = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            cart_count = connection.hlen(cart_key)
        context = {'sku': sku,
                   'types': types,
                   'sku_orders': sku_orders,
                   'new_skus': new_skus,
                   'cart_count': cart_count}
        return render(request, 'detail.html', context)


# type page
# /list/type_id/page/
class ListView(View):
    def get(self, request, type_id, page):
        try:
            type = GoodsType.objects.get(id=type_id)
        except GoodsType.DoesNotExist:
            return redirect('goods:index')
        types = GoodsType.objects.all()
        # sort by default/price/sales
        sort = request.GET.get('sort')
        if sort == 'price':
            skus = GoodsSKU.objects.filter(type=type).order_by('price')
        elif sort == 'sales':
            skus = GoodsSKU.objects.filter(type=type).order_by('-sales')
        else:
            skus = GoodsSKU.objects.filter(type=type).order_by('-id')

        paginator = Paginator(skus, 1)
        try:
            page = int(page)
        except Exception as e:
            page = 1
        if page > paginator.num_pages:
            page = 1
        skus_page = paginator.page(page)
        num_pages = paginator.num_pages
        if num_pages < 5:
            pages = range(1, num_pages)
        elif page <= 3:
            pages = range(1, 6)
        elif num_pages - page <= 2:
            pages = range(num_pages - 4, num_pages + 1)
        else:
            pages = range(page - 2, page + 3)

        new_skus = GoodsSKU.objects.filter(type=type).order_by('-create_times')
        user = request.user
        cart_count = 0
        if user.is_authenticated:
            connection = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            cart_count = connection.hlen(cart_key)
        dict = {'type': type,
                'types': types,
                'skus_page': skus_page,
                'pages': pages,
                'new_skus': new_skus,
                'cart_count': cart_count,
                'sort': sort}
        return render(request, 'list.html', dict)
