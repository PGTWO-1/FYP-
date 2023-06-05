import re
import os
from django.shortcuts import render, redirect
from django.views.generic import View
from apps.goods.models import GoodsSKU
from django_redis import get_redis_connection
from apps.user.models import Address
from django.http import JsonResponse
from datetime import datetime
from .models import OrderInfo, OrderGoods
from django.db import transaction
from alipay import AliPay
from django.conf import settings


# Create your views here.
class OrderPlaceView(View):
    def post(self, request):
        sku_ids = request.POST.getlist('sku_ids')
        if not sku_ids:
            return redirect('cart:cart')
        user = request.user
        connection = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id
        skus = []
        total_count = 0
        total_amount = 0
        for sku_id in sku_ids:
            sku = GoodsSKU.objects.get(id=sku_id)
            count = connection.hget(cart_key, sku_id)
            amount = sku.price * int(count)
            total_count += int(count)
            total_amount += amount
            sku.amount = amount
            sku.count = int(count)
            skus.append(sku)

        transit_price = 10
        total_pay = total_amount + transit_price
        address = Address.objects.filter(user=user)
        dict = {
            'skus': skus,
            'total_count': total_count,
            'total_amount': total_amount,
            'transit_price': transit_price,
            'total_pay': total_pay,
            'address': address,
            'sku_ids': sku_ids
        }
        return render(request, 'place_order.html', dict)


class OrderCommitView(View):
    @transaction.atomic
    def post(self, request):
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': 0, 'errmsg': '用户未登录'})
        addr_id = request.POST.get('addr_id')
        pay_method = request.POST.get('pay_method')
        sku_ids = request.POST.get('sku_ids')
        if not all([addr_id, pay_method, sku_ids]):
            return JsonResponse({'res': 1, 'errmsg': '参数不完整'})
        #  todo: obtain address
        address = Address.objects.get(id=addr_id)
        order_id = datetime.now().strftime('%d%m%Y%H%M%S') + str(user.id)
        transit_price = 10
        total_count = 0
        total_price = 0
        save_id = transaction.savepoint()
        try:
            # todo: create order information
            order = OrderInfo.objects.create(order_id=order_id,
                                             user=user,
                                             addr=address,
                                             pay_method=pay_method,
                                             total_count=total_count,
                                             transit_price=transit_price,
                                             total_price=total_price
                                             )
            connection = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            sku_ids = re.findall("\d+\.?\d*", str(sku_ids))

            for sku_id in sku_ids:
                try:
                    sku = GoodsSKU.objects.select_for_update().get(id=sku_id)
                except:
                    transaction.savepoint_rollback(save_id)
                    return JsonResponse({'res': 2, 'errmsg': '查不到商品信息'})
                count = connection.hget(cart_key, sku_id)
                if int(count) > sku.stock:
                    transaction.savepoint_rollback(save_id)
                    return JsonResponse({'res': 3, 'errmsg': '商品库存不足'})
                OrderGoods.objects.create(order=order, sku=sku, count=count, price=sku.price)
                sku.stock -= int(count)
                sku.sales += int(count)
                sku.save()

                total_count += int(count)
                total_price += sku.price * int(count)
            order.total_count = total_count
            order.total_price = total_price
            order.save()
        except Exception as e:
            transaction.savepoint_rollback(save_id)
            return JsonResponse({'res': 4, 'errmsg': '下单失败'})
        transaction.savepoint_commit(save_id)
        for sku_id in sku_ids:
            connection.hdel(cart_key, sku_id)
        return JsonResponse({'res': 5, 'message': '创建成功'})


class OrderPayView(View):
    def post(self, request):
        user = request.user
        if not user.is_authenticated:
            return JsonResponse({'res': 0, 'errmsg': '用户未登录'})
        # todo: accept ajax request
        order_id = request.POST.get('order_id')
        if not order_id:
            return JsonResponse({'res': 1, 'errmasg': '无效订单'})
        try:
            order = OrderInfo.objects.get(user=user, order_id=order_id, pay_method=3, order_status=1)
        except OrderInfo.DoesNotExist:
            return JsonResponse({'res': 2, 'errmsg': '订单错误'})
        # todo: use python sdk call alipay sdk
        app_private_key_string = open("apps/order/app_private_key.pem").read()
        alipay_public_key_string = open("apps/order/alipay_public_key.pem").read()
        alipay = AliPay(
            appid="2021000122674394",
            app_notify_url=None,
            app_private_key_string=app_private_key_string,
            alipay_public_key_string=alipay_public_key_string,
            sign_type="RSA2",
            debug=True
        )
        total_pay = order.total_price + 10
        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id,  # 生成随时间变动而变动的唯一订单号
            total_amount=str(total_pay),  # 将Decimal类型转换为字符串交给支付宝
            subject="天天生鲜",
            return_url="http://127.0.0.1:8000/order/check",
            notify_url="http://127.0.0.1:8000/order/check"  # 可选, 不填则使用默认notify url
        )
        pay_url = 'https://openapi-sandbox.dl.alipaydev.com/gateway.do?' + order_string
        return JsonResponse({'res': 3, 'pay_url': pay_url})


class OrderPayCheck(View):
    def get(self, request):
        app_private_key_string = open("apps/order/app_private_key.pem").read()
        alipay_public_key_string = open("apps/order/alipay_public_key.pem").read()
        alipay = AliPay(
            appid="2021000122674394",
            app_notify_url=None,
            app_private_key_string=app_private_key_string,
            alipay_public_key_string=alipay_public_key_string,
            sign_type="RSA2",
            debug=True
        )
        data = request.GET.dict()
        signature = data.pop('sign')
        success = alipay.verify(data, signature)
        if success:
            print('支付成功')
            order_id = request.GET.get('out_trade_no')
            order = OrderInfo.objects.get(order_id=order_id)
            order.trade_no = order_id
            order.order_status = 4
            order.save()
        return render(request, 'user_center_order.html')
    # def post(self, request):
    #     user = request.user
    #     if not user.is_authenticated:
    #         return JsonResponse({'res': 0, 'errmsg': '用户未登录'})
    #     # todo: accept ajax request
    #     order_id = request.POST.get('order_id')
    #     if not order_id:
    #         return JsonResponse({'res': 1, 'errmasg': '无效订单'})
    #     try:
    #         order = OrderInfo.objects.get(user=user, order_id=order_id, pay_method=3, order_status=1)
    #     except OrderInfo.DoesNotExist:
    #         return JsonResponse({'res': 2, 'errmsg': '订单错误'})
    #     # todo: use python sdk call alipay sdk
    #     app_private_key_string = open("apps/order/app_private_key.pem").read()
    #     alipay_public_key_string = open("apps/order/alipay_public_key.pem").read()
    #     alipay = AliPay(
    #         appid="2021000122674394",
    #         app_notify_url=None,
    #         app_private_key_string=app_private_key_string,
    #         alipay_public_key_string=alipay_public_key_string,
    #         sign_type="RSA2",
    #         debug=True
    #     )
    #     while True:
    #         response = alipay.api_alipay_trade_query(order_id)
    #         """
    #         response = {
    #             "alipay_trade_query_response": {
    #                 "trade_no": "2017032121001004070200176844",
    #                 "code": "10000",
    #                 "invoice_amount": "20.00",
    #                 "open_id": "20880072506750308812798160715407",
    #                 "fund_bill_list": [
    #                     {
    #                         "amount": "20.00",
    #                         "fund_channel": "ALIPAYACCOUNT"
    #                     }
    #                 ],
    #                 "buyer_logon_id": "csq***@sandbox.com",
    #                 "send_pay_date": "2017-03-21 13:29:17",
    #                 "receipt_amount": "20.00",
    #                 "out_trade_no": "out_trade_no15",
    #                 "buyer_pay_amount": "20.00",
    #                 "buyer_user_id": "2088102169481075",
    #                 "msg": "Success",
    #                 "point_amount": "0.00",
    #                 "trade_status": "TRADE_SUCCESS",
    #                 "total_amount": "20.00"
    #             },
    #             "sign": ""
    #         }
    #         """
    #         code = response.get('code')
    #         if code == '10000' and response.get('trade_status') == "TRADE_SUCCESS":
    #             trade_no = response.get('trade_no')
    #             order.trade_no = trade_no
    #             order.order_status = 4
    #             order.save()
    #             return JsonResponse({'res': 3, 'message': '支付成功'})
    #         elif code == '10000' and response.get('trade_status') == "WAIT_BUYER_PAY":
    #             import time
    #             time.sleep(5)
    #             continue
    #         else:
    #             return JsonResponse({'res': 4, 'errmsg': '支付失败'})


class OrderCommentView(View):
    def get(self, request, order_id):
        """展示评论页"""
        user = request.user

        # 校验数据
        if not order_id:
            return redirect('user:order')

        try:
            order = OrderInfo.objects.get(order_id=order_id, user=user)
        except OrderInfo.DoesNotExist:
            return redirect('user:order')

        # 需要根据状态码获取状态
        order.status_name = OrderInfo.ORDER_STATUS[order.order_status]

        # 根据订单id查询对应商品，计算小计金额,不能使用get
        order_skus = OrderGoods.objects.filter(order_id=order_id)
        for order_sku in order_skus:
            amount = order_sku.count * order_sku.price
            order_sku.amount = amount
        # 增加实例属性
        order.order_skus = order_skus

        context = {
            'order': order,
        }
        return render(request, 'order_comment.html', context)
    def post(self, request, order_id):
        """处理评论内容"""
        # 判断是否登录
        user = request.user

        # 判断order_id是否为空
        if not order_id:
            return redirect('user:order')

        # 根据order_id查询当前登录用户订单
        try:
            order = OrderInfo.objects.get(order_id=order_id, user=user)
        except OrderInfo.DoesNotExist:
            return redirect('user:order')

        # 获取评论条数
        total_count = int(request.POST.get("total_count"))

        # 循环获取订单中商品的评论内容
        for i in range(1, total_count + 1):
            # 获取评论的商品的id
            sku_id = request.POST.get("sku_%d" % i)  # sku_1 sku_2
            # 获取评论的商品的内容
            content = request.POST.get('content_%d' % i, '')  # comment_1 comment_2

            try:
                order_goods = OrderGoods.objects.get(order=order, sku_id=sku_id)
            except OrderGoods.DoesNotExist:
                continue

            # 保存评论到订单商品表
            order_goods.comment = content
            order_goods.save()

        # 修改订单的状态为“已完成”
        order.order_status = 5  # 已完成
        order.save()
        # 1代表第一页的意思，不传会报错
        return redirect("user:order",page='1')
