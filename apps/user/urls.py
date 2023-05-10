from django.contrib import admin
from django.urls import path
from django.urls import path,include,re_path
from .views import RegisterView,ActiveView,LoginView
urlpatterns = [
    path('register',RegisterView.as_view(),name='register'), #注册
    re_path(r'^active/(?P<token>.*)$',ActiveView.as_view(),name='active'),
    path('login',LoginView.as_view(),name='login'),
]