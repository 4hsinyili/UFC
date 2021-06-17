from django.urls import path

from . import views

urlpatterns = [
    path('api/v1/dinersearch', views.DinerSearchAPI.as_view()),
    path('api/v1/dinershuffle', views.DinerShuffleAPI.as_view()),
    path('api/v1/dinerinfo', views.DinerInfoAPI.as_view()),
    path('api/v1/filters', views.FiltersAPI.as_view()),
    path('api/v1/favorites', views.FavoritesAPI.as_view()),
    path('api/v1/noteq', views.NoteqAPI.as_view()),
    path('api/v1/dashboard', views.DashBoardAPI.as_view()),
    path('', views.dinerlist_view, name='dinerlist'),
    path('dinerinfo', views.dinerinfo_view, name='dinerinfo'),
    path('favorites', views.favorites_view, name='favorites'),
    path('dashboard', views.dashboard_view, name='dashboard'),
    path('test_500', views.test_500_view, name='test_500'),
    # path('.well-known/pki-validation/F6B43E81B6BB7366178E7DE03B1BB0FC.txt', views.forSSL, name='test')
]
