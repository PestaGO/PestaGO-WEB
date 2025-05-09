from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('predict/', views.predict, name='predict'),
    path('result/', views.result, name='result'),
    path('image/<str:image_type>/', views.serve_image, name='serve_image'),
] 