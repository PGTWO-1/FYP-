from django.urls import path,include
from apps.cart.views import CartAddView,CartInfoView,CartUpdateView,CartDeleteView
from django.contrib.auth.decorators import login_required
urlpatterns = [
    path('add',CartAddView.as_view(),name='add'),
    path('',login_required(CartInfoView.as_view()),name='cart'),
    path('update',CartUpdateView.as_view(),name='update'),
    path('delete',CartDeleteView.as_view(),name='delete')
]
