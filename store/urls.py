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
    path('remove-from-cart/<str:pro_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('shop-settings/', views.shop_settings, name='shop_settings'),
    path('import-stock/', views.import_stock, name='import_stock'),
    path('products/add/', views.add_product, name='add_product'),
    path('products/edit/<str:pro_id>/', views.edit_product, name='edit_product'),
    path('products/delete/<str:pro_id>/', views.delete_product, name='delete_product'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('claims/edit/<str:claim_id>/', views.edit_claim, name='edit_claim'),
]
