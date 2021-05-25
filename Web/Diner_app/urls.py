from django.urls import path

from . import views

urlpatterns = [
    path('api/v1/dinerlist', views.DinerList.as_view()),
    path('api/v1/dinersearch', views.DinerSearch.as_view()),
    path('api/v1/dinerinfo', views.DinerInfo.as_view()),
    path('api/v1/filters', views.Filters.as_view()),
    path('dinerlist', views.dinerlist, name='dinerlist'),
    path('dinerinfo', views.dinerinfo, name='dinerinfo'),
]
