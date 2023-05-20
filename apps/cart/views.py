from django.shortcuts import render
from django.views.generic import View
from django.http import JsonResponse
from apps.goods.models import GoodsSKU
from django_redis import get_redis_connection


# Create your views here.

class CartAddView(View):
    def post(self, request):
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': 0, 'errmsg': '请先登录'})
        sku_id = request.POST.get('sku_id')
        print(sku_id,type(sku_id))
        count = request.POST.get('count')
        if not all([sku_id, count]):
            return JsonResponse({'res': 1, 'errmsg': '数据不完整'})

        try:
            count = int(count)
        except Exception as e:
            return JsonResponse({'res': 2, 'errmsg': '商品数目出错'})

        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'res': 3, 'errmsg': '商品不存在'})

        connection = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id
        cart_count = connection.hget(cart_key, sku_id)
        if cart_count:
            count += int(cart_count)
        if count > sku.stock:
            return JsonResponse({'res': 4, 'errmsg': '商品库存不足'})
        connection.hset(cart_key, sku_id, count)
        total_amount = connection.hlen(cart_key)
        return JsonResponse({'res': 5, 'message': '添加成功', 'total_amount': total_amount})


class CartInfoView(View):
    def get(self, request):
        user = request.user
        connection = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id
        cart_dict = connection.hgetall(cart_key)  # {cart_id:amount}
        sku_list = []
        total_count = 0
        total_price = 0
        for sku_id, count in cart_dict.items():
            sku = GoodsSKU.objects.get(id=sku_id)
            price = int(count) * sku.price
            sku.amount = price
            sku.count = int(count)
            total_count += int(count)
            total_price += price
            sku_list.append(sku)
        dict = {
            'total_count': total_count,
            'total_price': total_price,
            'sku_list': sku_list
        }
        return render(request, 'cart.html', dict)


class CartUpdateView(View):
    '''购物车记录更新'''

    def post(self, request):
        '''购物车记录更新'''
        user = request.user
        if not user.is_authenticated:
            # 用户未登录
            return JsonResponse({'res': 0, 'errmsg': '请先登录'})

        # 接收数据
        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')

        # 数据校验
        if not all([sku_id, count]):
            return JsonResponse({'res': 1, 'errmsg': '数据不完整'})

        # 校验添加的商品数量
        try:
            count = int(count)
        except Exception as e:
            # 数目出错cart/
            return JsonResponse({'res': 2, 'errmsg': '商品数目出错'})

        # 校验商品是否存在
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            # 商品不存在
            return JsonResponse({'res': 3, 'errmsg': '商品不存在'})

        # 业务处理:更新购物车记录
        connection = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id

        # 校验商品的库存
        if count > sku.stock:
            return JsonResponse({'res': 4, 'errmsg': '商品库存不足'})

        # 更新
        connection.hset(cart_key, sku_id, count)

        # 计算用户购物车中商品的总件数 {'1':5, '2':3}
        total_count = 0
        vals = connection.hvals(cart_key)
        for val in vals:
            total_count += int(val)

        # 返回应答
        return JsonResponse({'res': 5, 'total_count': total_count, 'message': '更新成功'})

class CartDeleteView(View):
    """购物车记录删除"""
    def post(self, request):
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': 0, 'errmsg': '请先登录'})

        # 接收参数
        sku_id = request.POST.get('sku_id')

        # 数据校验
        if not sku_id:
            return JsonResponse({'res': 1, 'errmsg': '无效的商品id'})

        # 校验商品是否存在
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'res': 2, 'errmsg': '商品不存在'})

        # 业务处理: 删除购物车记录
        connection = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id

        # 删除 hdel
        connection.hdel(cart_key, sku_id)

        # 计算用户购物车中商品的总件数{'1':5,'2':3}
        total_count = 0
        vals = connection.hvals(cart_key)
        for val in vals:
            total_count += int(val)

        return JsonResponse({'res': 3, 'total_count': total_count, 'message': '删除成功'})