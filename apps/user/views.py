from django.shortcuts import render,redirect
from .models import User
import re

#/user/register
def register(request):
    return render(request,'register.html')

def register_handle(request):
    #accept data
    username=request.POST.get('user_name')
    password=request.POST.get('pwd')
    cpassword=request.POST.get('cpwd')
    email=request.POST.get('email')
    allow=request.POST.get('allow')
    #check data
    if not all([username,password,email]):
        return render(request,'register.html',{'errmsg':'数据不完整'})
    if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$',email):
        return render(request,'register.html',{'errmsg':'邮箱不合法'})
    if allow !='on':
        return render(request,'register.html',{'errmsg':'请确认协议'})
    if password!=cpassword:
        return render(request, 'register.html', {'errmsg': '请确认密码一致'})
    #handle data
    user=User.objects.create_user(username,email,password)
    user.is_active=0
    user.save()
    #return request
    return redirect('goods:index')