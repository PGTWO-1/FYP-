import re
from django.shortcuts import render,redirect
from django.views.generic import View
from apps.goods.models import GoodsSKU
from django_redis import get_redis_connection
from apps.user.models import Address
from django.http import JsonResponse
from datetime import datetime
from .models import OrderInfo,OrderGoods
# Create your views here.
class OrderPlaceView(View):
    def post(self,request):
        sku_ids=request.POST.getlist('sku_ids')
        if not sku_ids:
            return redirect('cart:cart')
        user=request.user
        connection=get_redis_connection('default')
        cart_key='cart_%d'%user.id
        skus=[]
        total_count=0
        total_amount=0
        for sku_id in sku_ids:
            sku=GoodsSKU.objects.get(id=sku_id)
            count=connection.hget(cart_key,sku_id)
            amount=sku.price*int(count)
            total_count+=int(count)
            total_amount+=amount
            sku.amount=amount
            sku.count=int(count)
            skus.append(sku)

        transit_price=10
        total_pay=total_amount+transit_price
        address=Address.objects.filter(user=user)
        dict={
            'skus':skus,
            'total_count':total_count,
            'total_amount':total_amount,
            'transit_price':transit_price,
            'total_pay':total_pay,
            'address':address,
            'sku_ids':sku_ids
        }
        return render(request,'place_order.html',dict)


class OrderCommitView(View):
    def post(self,request):
        user=request.user
        if not user.is_authenticated:
            return JsonResponse({'res':0,'errmsg':'用户未登录'})
        addr_id= request.POST.get('addr_id')
        pay_method=request.POST.get('pay_method')
        sku_ids=request.POST.get('sku_ids')
        if not all([addr_id,pay_method,sku_ids]):
            return JsonResponse({'res':1,'errmsg':'参数不完整'})
        address=Address.objects.get(id=addr_id)
        order_id=datetime.now().strftime('%d%m%Y%H%M%S')+str(user.id)
        transit_price=10
        total_count =0
        total_price=0
        order=OrderInfo.objects.create(order_id=order_id,
                                       user=user,
                                       addr=address,
                                       pay_method=pay_method,
                                       total_count=total_count,
                                       transit_price=transit_price,
                                       total_price=total_price
                                       )
        connection = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id
        sku_ids=re.findall("\d+\.?\d*",str(sku_ids))

        for sku_id in sku_ids:
            try:
                sku=GoodsSKU.objects.get(id=sku_id)
            except:
                return JsonResponse({'res':2,'errmsg':'查不到商品信息'})
            count=connection.hget(cart_key,sku_id)
            OrderGoods.objects.create(order=order,sku=sku,count=count,price=sku.price)
            sku.stock-=int(count)
            sku.sales+=int(count)
            sku.save()

            total_count+=int(count)
            total_price+=sku.price*int(count)
        order.total_count=total_count
        order.total_price=total_price
        order.save()
        for sku_id in sku_ids:
            connection.hdel(cart_key,sku_id)
        return JsonResponse({'res':3,'message':'创建成功'})