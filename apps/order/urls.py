from django.urls import path,include
from apps.order.views import OrderPlaceView
from django.contrib.auth.decorators import login_required
urlpatterns = [
    path('place',login_required(OrderPlaceView.as_view()),name='place')
]
