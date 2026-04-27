from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # --- Main Boutique Pages ---
    path('', views.index, name='index'),
    path('shop/', views.shop, name='shop'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    
    # --- Cart Logic ---
    path('cart/', views.cart, name='cart'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('decrease-item/<int:item_id>/', views.decrease_cart_item, name='decrease_cart_item'),
    path('remove-from-cart/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    
    # --- Product & Category Logic ---
    path('collection/<slug:slug>/', views.category_detail, name='category_detail'),
    path('product/<int:pk>/', views.product_detail_view, name='product_detail'), 
    
    # --- Orders ---
    path('save-order/', views.save_order, name='save_order'),
    path('order/<int:order_id>/', views.order_detail_view, name='order_detail'),

    # --- Authentication Flow ---
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('verify/<str:phone_number>/', views.verify_otp, name='verify_otp'),
    path('profile/', views.profile_view, name='profile'),
    
    # Built-in Logout
    path('logout/', auth_views.LogoutView.as_view(next_page='index'), name='logout'),
]
