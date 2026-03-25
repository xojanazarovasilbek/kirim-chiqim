from django.urls import path
from . import views


urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('products/', views.product_list, name='products'),
    path('partners/', views.partner_list, name='partners'),
    path('partners/<int:pk>/', views.partner_detail, name='partner_detail'),
    path('pos/', views.pos_view, name='pos'),
    path('inbound/add/', views.inbound_create, name='inbound_add'),
    path('return/add/', views.return_create, name='return_add'), 
    path('payment/add/', views.payment_create, name='payment_add'),  
    path('product/add/', views.product_create, name='product_add'),
    path('category/add/', views.category_create, name='category_add'),
    path('api/sale/', views.api_sale, name='api_sale'), 
    path('history/', views.transaction_history, name='transaction_history'),
]