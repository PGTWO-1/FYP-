from django.shortcuts import render,redirect
from django.views.generic import View
from apps.goods.models import GoodsSKU
from django_redis import get_redis_connection
from apps.user.models import Address
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
            sku.count=count
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
            'address':address
        }
        return render(request,'place_order.html',dict)