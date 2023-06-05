from django.urls import path,re_path
from apps.order.views import OrderPlaceView,OrderCommitView,OrderPayView,OrderPayCheck,OrderCommentView
from django.contrib.auth.decorators import login_required
urlpatterns = [
    path('place',login_required(OrderPlaceView.as_view()),name='place'),
    path('commit',OrderCommitView.as_view(),name='commit'),
    path('pay',OrderPayView.as_view(),name='pay'),
    path('check',OrderPayCheck.as_view(),name='check'),
    re_path(r'comment/(?P<order_id>.+)$',OrderCommentView.as_view(),name='comment')
]
