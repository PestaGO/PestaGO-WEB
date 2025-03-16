from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('predict/', views.predict, name='predict'),
    path('prediction_detail/', views.prediction_detail, name='prediction_detail'),
    path('image/<str:image_type>/', views.serve_image, name='serve_image'),
    path('about/', views.about, name='about'),
] 