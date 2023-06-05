from django.contrib import admin
from django.urls import path
from django.urls import path, include, re_path
from django.contrib.auth.decorators import login_required
from .views import RegisterView, ActiveView, LoginView, UserInfoView, UserOrderView, UserAddressView, LogoutView

urlpatterns = [
    path('register', RegisterView.as_view(), name='register'),  # 注册
    re_path(r'^active/(?P<token>.*)$', ActiveView.as_view(), name='active'),
    path('login', LoginView.as_view(), name='login'),
    path('logout', LogoutView.as_view(), name='logout'),
    path('', login_required(UserInfoView.as_view()), name='user'),
    re_path(r'order/(?P<page>\d+)$', login_required(UserOrderView.as_view()), name='order'),
    path('address', login_required(UserAddressView.as_view()), name='address'),
]
