from django.contrib import admin
from django.urls import path,include,re_path
from django.views.static import serve
from django.conf import settings
from django.conf.global_settings import MEDIA_ROOT
urlpatterns = [
    path("admin/", admin.site.urls),
    # re_path(r'media/(?P<path>.*)$', serve, {'document_root': MEDIA_ROOT}),
    path("user/", include(("apps.user.urls",'user'),namespace='user')), #用户模块
    path("cart/", include(("apps.cart.urls",'cart'),namespace='cart')), #购物车模块
    path("order/",include(("apps.order.urls",'order'),namespace='order')),#订单模块
    path("", include(("apps.goods.urls",'goods'),namespace='goods')), #商品模块

]
