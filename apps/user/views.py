from django.shortcuts import render, redirect
from django.views.generic import View
from .models import User, Address, AddressManager
import re
from django.core.mail import send_mail
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from apps.order.models import OrderInfo, OrderGoods
from django.core.paginator import Paginator

SECRET_KEY = "django-insecure-9d)*5&t6sfx2415%^szt#uo8#r^-5@!6)r*a%c$i925k7u@7!8"


def send_register_active_email(to_email, username, token):
    '''send active email'''
    EMAIL_FROM = "1443815378@qq.com"  # 邮箱来自
    email_title = '邮箱激活'
    email_body = "请点击下方的链接激活你的账号：http://127.0.0.1:8000/user/active/{}, 该链接有效时间为两分钟，请及时进行验证。".format(
        token)
    email_box = []
    email_box.append(to_email)
    send_mail(email_title, email_body, EMAIL_FROM, email_box, fail_silently=False)


# /user/register
class RegisterView(View):

    def get(self, request):
        return render(request, 'register.html')

    def post(self, request):
        # accept data
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        cpassword = request.POST.get('cpwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')
        # check data
        if not all([username, password, email]):
            return render(request, 'register.html', {'errmsg': '数据不完整'})
        if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {'errmsg': '邮箱不合法'})
        if allow != 'on':
            return render(request, 'register.html', {'errmsg': '请确认协议'})
        if password != cpassword:
            return render(request, 'register.html', {'errmsg': '请确认密码一致'})
        # handle data
        user = User.objects.create_user(username, email, password)
        user.is_active = 0
        user.save()
        # send email

        serializer = Serializer(SECRET_KEY, 3600)
        info = {'confirm': user.username}
        token = serializer.dumps(info)
        token = token.decode()
        send_register_active_email(email, username, token)
        return redirect('goods:index')


class ActiveView(View):
    def get(self, request, token):
        print(token)
        serializer = Serializer(SECRET_KEY, 3600)
        try:
            info = serializer.loads(token)
            user_name = info.get('confirm')
            print(user_name)
            user = User.objects.get(username=user_name)
            user.is_active = 1
            user.save()
            return redirect('user:login')
        except SignatureExpired as e:
            return HttpResponse('激活链接已过期')


class LoginView(View):
    def get(self, request):
        username = ''
        password = ''
        checked = ''
        # check whether remember the username
        if 'username' in request.COOKIES and 'password' in request.COOKIES:
            username = request.COOKIES.get('username')
            password = request.COOKIES.get('password')
            checked = 'checked'  # checkbox
        else:
            pass
        return render(request, 'login.html', {'username': username, 'password': password, 'checked': checked})

    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('pwd')
        if not all([username, password]):
            return render(request, 'login.html', {'errmsg': '数据不完整'})

        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                next_url = request.GET.get('next', 'goods:index')
                print(next_url)
                response = redirect(next_url)
                # check whether need to remember username
                remember = request.POST.get('remember')
                if remember == 'on':
                    response.set_cookie('username', username, max_age=7 * 24 * 3600)
                    response.set_cookie('password', password, max_age=7 * 24 * 3600)
                else:
                    response.delete_cookie('username')
                    response.delete_cookie('password')
                return response
            else:
                redirect('goods:index')
        else:
            return render(request, 'login.html', {'errmsg': '用户名密码错误'})


class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('goods:index')


class UserInfoView(View):
    def get(self, request):
        # get user information and history
        user = request.user
        address = Address.objects.get_default_address(user)

        return render(request, 'user_center_info.html', {'page': 'user', 'address': address})


class UserOrderView(View):
    def get(self, request, page):
        user = request.user
        orders = OrderInfo.objects.filter(user=user)
        for order in orders:
            order_skus = OrderGoods.objects.filter(order_id=order.order_id)
            for order_sku in order_skus:
                count = order_sku.count
                price = order_sku.price
                amount = price * int(count)
                order_sku.amount = amount
            order.order_skus = order_skus
            order.order_status_name = OrderInfo.ORDER_STATUS[order.order_status]

        paginator = Paginator(orders, 5)
        try:
            page = int(page)
        except Exception as e:
            page = 1
        if page > paginator.num_pages:
            page = 1
        order_page = paginator.page(page)

        num_pages = paginator.num_pages
        if num_pages < 5:
            pages = range(1, num_pages)
        elif page <= 3:
            pages = range(1, 6)
        elif num_pages - page <= 2:
            pages = range(num_pages - 4, num_pages + 1)
        else:
            pages = range(page - 2, page + 3)

        dict = {
            'order_page': order_page,
            'pages': pages,
            'page': 'order'
        }
        return render(request, 'user_center_order.html', dict)


class UserAddressView(View):
    def get(self, request):
        user = request.user
        address = Address.objects.filter(user=user)
        return render(request, 'user_center_site.html', {'page': 'address', 'address': address})

    def post(self, request):
        receiver = request.POST.get('receiver')
        addr = request.POST.get('addr')
        print(addr)
        zip_code = request.POST.get('zip_code')
        phone = request.POST.get('phone')
        if not all([receiver, addr, zip_code, phone]):
            return render(request, 'user_center_site.html', {'errmsg': '数据不完整'})
        user = request.user
        address = Address.objects.get_default_address(user)

        if address is not None:
            is_default = False
        else:
            is_default = True
        # add address
        Address.objects.create(user=user,
                               receiver=receiver,
                               addr=addr,
                               zip_code=zip_code,
                               phone=phone,
                               is_default=is_default)

        return redirect('user:address')
