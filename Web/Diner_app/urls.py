from django.urls import path

from . import views

urlpatterns = [
    path('api/v1/dinersearch', views.DinerSearch.as_view()),
    path('api/v1/dinershuffle', views.DinerShuffle.as_view()),
    path('api/v1/dinerinfo', views.DinerInfo.as_view()),
    path('api/v1/filters', views.Filters.as_view()),
    path('api/v1/favorites', views.FavoritesAPI.as_view()),
    path('api/v1/dashboard', views.DashBoardView.as_view()),
    path('', views.dinerlist, name='dinerlist'),
    path('dinerinfo', views.dinerinfo, name='dinerinfo'),
    path('favorites', views.favorites, name='favorites'),
    path('dashboard', views.dashboard, name='dashboard'),
    path('test_500', views.test_500, name='test_500'),
    # path('.well-known/pki-validation/F6B43E81B6BB7366178E7DE03B1BB0FC.txt', views.forSSL, name='test')
]
