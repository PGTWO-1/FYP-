from django.contrib import admin
from django.urls import path,include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("user/", include(("apps.user.urls",'user'),namespace='user')), #用户模块
    path("cart/", include(("apps.cart.urls",'cart'),namespace='cart')), #购物车模块
    path("order/",include(("apps.order.urls",'order'),namespace='order')),#订单模块
    path("", include(("apps.goods.urls",'goods'),namespace='goods')), #商品模块

]
