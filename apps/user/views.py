from django.shortcuts import render, redirect
from django.views.generic import View
from .models import User
import re
import random
from django.core.mail import send_mail
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
from django.http import HttpResponse
SECRET_KEY = "django-insecure-9d)*5&t6sfx2415%^szt#uo8#r^-5@!6)r*a%c$i925k7u@7!8"
def send_sms_code(to_email,token):
    """
    发送邮箱验证码
    :param to_mail: 发到这个邮箱
    :return: 成功：0 失败 -1
    """
    # 生成邮箱验证码

    EMAIL_FROM = "1443815378@qq.com"  # 邮箱来自
    email_title = '邮箱激活'
    email_body = "好喜欢阿格，亲亲亲！请点击下方的链接激活你的账号：http://127.0.0.1:8000/user/active/{}, 该链接有效时间为两分钟，请及时进行验证。".format(token)
    email_box=[]
    email_box.append(to_email)
    send_status = send_mail(email_title, email_body, EMAIL_FROM, email_box,fail_silently=False)
    return send_status

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
        info={'confirm':user.username}
        token=serializer.dumps(info)
        token=token.decode()
        send_sms_code(email,token)
        return redirect('goods:index')


class ActiveView(View):
    def get(self,request,token):
        print(token)
        serializer = Serializer(SECRET_KEY, 3600)
        try:
            info=serializer.loads(token)
            user_name=info.get('confirm')
            print(user_name)
            user=User.objects.get(username=user_name)
            user.is_active=1
            user.save()
            return redirect('user:login')
        except SignatureExpired as e:
            return HttpResponse('激活链接已过期')

class LoginView(View):
    def get(self,request):
        return render(request,'login.html')