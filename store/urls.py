from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('products/', views.product_list, name='product_list'),
    path('add_to_cart/<str:pro_id>/', views.add_to_cart, name='add_to_cart'),
    path('clear_cart/', views.clear_cart, name='clear_cart'),
    path('pos/', views.pos, name='pos'),
    path('checkout/', views.checkout, name='checkout'),
    path('receipt/<str:sale_id>/', views.receipt, name='receipt'),
    path('report/', views.sales_report, name='sales_report'),
    path('claims/', views.claim_list, name='claim_list'),
    path('claims/add/', views.add_claim, name='add_claim'),
]
