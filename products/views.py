import json
import random
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import (
    Product, Banner, Category, PromoBox, 
    CustomerProfile, ContactInquiry, Order, OrderItem, Review,
    Cart, CartItem 
)

# --- 1. Main Display Views ---

def index(request):
    banners = Banner.objects.filter(active=True).order_by('order')
    categories = Category.objects.all().order_by('order')
    promos = PromoBox.objects.all().order_by('order')[:3]
    items = Product.objects.all()
    
    context = {
        'items': items,
        'banners': banners,
        'categories': categories,
        'promos': promos,
    }
    return render(request, 'products/index.html', context)

def shop(request):
    items = Product.objects.all()
    categories = Category.objects.all().order_by('order')
    promos = PromoBox.objects.all().order_by('order')[:3]
    
    # 1. Initialize an empty list for product IDs
    cart_product_ids = []
    
    # 2. If the user is logged in, fetch their specific cart items
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        # We use .values_list('product_id', flat=True) to get just the IDs 
        # as a simple list, which is much faster than fetching full objects.
        cart_product_ids = list(cart.items.values_list('product_id', flat=True))

    return render(request, 'products/shop.html', {
        'items': items, 
        'categories': categories, 
        'promos': promos,
        'cart_product_ids': cart_product_ids  # Pass this to the template
    })



def about(request):
    reviews = Review.objects.all().order_by('-created_at')
    return render(request, 'products/about.html', {'reviews': reviews})

def contact(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        ContactInquiry.objects.create(
            full_name=full_name,
            email=email,
            subject=subject,
            message=message
        )
        messages.success(request, "Your inquiry has been sent to the Rasayam concierge.")
        return redirect('contact') 

    return render(request, 'products/contact.html')

@login_required
def cart(request):
    # Get or create the cart for the specific logged-in user
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.items.all()
    
    # Calculate subtotal using the model property we created
    total_price = sum(item.total_item_price for item in cart_items)
    
    recommended_items = Product.objects.all().exclude(category__isnull=True).order_by('?')[:4]
    
    context = {
        'cart_items': cart_items,
        'total_price': total_price,
        'recommended_items': recommended_items,
    }
    return render(request, 'products/cart.html', context)

# --- 2. Product & Category Logic ---

def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = Product.objects.filter(category=category)
    return render(request, 'products/category_detail.html', {
        'category': category,
        'products': products
    })

def product_detail_view(request, pk):
    product = get_object_or_404(Product, pk=pk)
    reviews = product.reviews.all().order_by('-created_at')
    return render(request, 'products/product_detail.html', {
        'product': product,
        'reviews': reviews
    })

# --- 3. Authentication Views ---

def register_view(request):
    if request.method == 'POST':
        phone = request.POST.get('phone')
        username = request.POST.get('username')
        email = request.POST.get('email')
        gender = request.POST.get('gender')
        city = request.POST.get('city')
        
        user, created = User.objects.get_or_create(username=username)
        if created:
            user.email = email
            user.set_password('temp_pass_123')
            user.save()
            
        profile, _ = CustomerProfile.objects.get_or_create(user=user)
        profile.phone_number = phone
        profile.email = email
        profile.gender = gender
        profile.city = city
        
        generated_otp = str(random.randint(100000, 999999))
        profile.otp = generated_otp
        profile.save()
        
        print(f"--- OTP FOR {username}: {generated_otp} ---")
        return redirect('verify_otp', phone_number=phone)
        
    return render(request, 'products/register.html')

def login_view(request):
    if request.method == "POST":
        phone = request.POST.get('phone_number')
        try:
            profile = CustomerProfile.objects.get(phone_number=phone)
            new_otp = str(random.randint(100000, 999999)) # Standardized to 6 digits
            profile.otp = new_otp
            profile.save()
            
            print(f"DEBUG: OTP for {phone} is {new_otp}")
            return redirect('verify_otp', phone_number=phone)
            
        except CustomerProfile.DoesNotExist:
            messages.error(request, "This phone number isn't registered yet.")
            return redirect('register')

    return render(request, 'products/login.html')

def verify_otp(request, phone_number):
    profile = get_object_or_404(CustomerProfile, phone_number=phone_number.strip())
    
    if request.method == 'POST':
        user_otp = request.POST.get('otp', '').strip()
        db_otp = profile.otp.strip()

        if user_otp == db_otp:
            profile.is_verified = True
            profile.save()
            login(request, profile.user)
            messages.success(request, f"Welcome back, {profile.user.username}!")
            return redirect('index')
        else:
            messages.error(request, "Incorrect OTP. Please check your terminal.")
            return render(request, 'products/verify_otp.html', {'phone': phone_number})

    return render(request, 'products/verify_otp.html', {'phone': phone_number})

def logout_view(request):
    logout(request)
    request.session.flush() # Clears any lingering guest data
    return redirect('index')

@login_required
def profile_view(request):
    orders = request.user.orders.all().order_by('-created_at')
    return render(request, 'products/profile.html', {'orders': orders})

# --- 4. Order & Cart Processing ---

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    
    messages.success(request, f"{product.name} added to your Selection.")
    
    # Stay on the current page or go to shop to prevent "disappearing" feel
    return redirect(request.META.get('HTTP_REFERER', 'shop'))

@login_required
def decrease_cart_item(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()
    else:
        cart_item.delete()
    return redirect('cart')

@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()
    messages.info(request, "Item removed from your bag.")
    return redirect('cart')

@login_required
def save_order(request):
    """ Converts Cart items into a permanent Order """
    cart = get_object_or_404(Cart, user=request.user)
    cart_items = cart.items.all()

    if not cart_items:
        messages.error(request, "Your bag is empty.")
        return redirect('shop')

    # Calculate final amount
    total_amount = sum(item.total_item_price for item in cart_items)

    order = Order.objects.create(
        user=request.user,
        total_amount=total_amount,
        status='Pending'
    )

    for item in cart_items:
        OrderItem.objects.create(
            order=order,
            product_name=item.product.name,
            price=item.product.price,
            quantity=item.quantity,
            image_url=item.product.image.url if item.product.image else ""
        )

    # Clear the cart completely
    cart_items.delete()

    messages.success(request, "Order placed successfully! Review your selection below.")
    return redirect('order_detail', order_id=order.id)

@login_required
def order_detail_view(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'products/order_detail.html', {'order': order})


from django.http import JsonResponse

@login_required
def add_to_cart_ajax(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    
    # Calculate the total count to update the navbar badge
    total_count = sum(item.quantity for item in cart.items.all())
    
    return JsonResponse({
        'status': 'success',
        'cart_count': total_count,
        'message': f"{product.name} added to your selection."
    })