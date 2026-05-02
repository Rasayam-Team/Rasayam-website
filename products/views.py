import json
import random
import razorpay
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import (
    Product, Banner, Category, PromoBox, 
    CustomerProfile, ContactInquiry, Order, OrderItem, Review,
    Cart, CartItem, Size, ProductImage
)

# --- Razorpay Client Initialization ---
razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

# --- 1. Main Display Views ---

def index(request):
    banners = Banner.objects.filter(active=True).order_by('order')
    categories = Category.objects.all().order_by('order')
    promos = PromoBox.objects.all().order_by('order')[:3]
    items = Product.objects.all().prefetch_related('gallery_images')
    
    context = {
        'items': items,
        'banners': banners,
        'categories': categories,
        'promos': promos,
    }
    return render(request, 'products/index.html', context)

def shop(request):
    items = Product.objects.all().prefetch_related('gallery_images')
    categories = Category.objects.all().order_by('order')
    promos = PromoBox.objects.all().order_by('order')[:3]
    
    cart_product_ids = []
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart_product_ids = list(cart.items.values_list('product_id', flat=True))

    return render(request, 'products/shop.html', {
        'items': items, 
        'categories': categories, 
        'promos': promos,
        'cart_product_ids': cart_product_ids
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
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.items.all()
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
    products = Product.objects.filter(category=category).prefetch_related('gallery_images')
    return render(request, 'products/category_detail.html', {
        'category': category,
        'products': products
    })

def product_detail_view(request, pk):
    """Product Detail with Gallery and Sizes"""
    product = get_object_or_404(Product.objects.prefetch_related('gallery_images', 'sizes'), pk=pk)
    reviews = product.reviews.all().order_by('-created_at')
    
    # Process highlights for list display
    highlights_list = product.highlights.split('\n') if product.highlights else []

    return render(request, 'products/product_detail.html', {
        'product': product,
        'reviews': reviews,
        'highlights_list': highlights_list
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
        profile.otp_created_at = timezone.now()
        profile.save()
        
        # DEBUG MODE: Check your terminal for the code
        print(f"--- OTP FOR {username} ({phone}): {generated_otp} ---")
        
        return redirect('verify_otp', phone_number=phone)
        
    return render(request, 'products/register.html')

def login_view(request):
    if request.method == "POST":
        phone = request.POST.get('phone_number')
        try:
            profile = CustomerProfile.objects.get(phone_number=phone)
            new_otp = str(random.randint(100000, 999999))
            profile.otp = new_otp
            profile.otp_created_at = timezone.now()
            profile.save()
            
            # DEBUG MODE: Check your terminal for the code
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
            messages.error(request, "Incorrect OTP. Check your server logs.")
            return render(request, 'products/verify_otp.html', {'phone': phone_number})

    return render(request, 'products/verify_otp.html', {'phone': phone_number})

def logout_view(request):
    logout(request)
    request.session.flush()
    return redirect('index')

@login_required
def profile_view(request):
    orders = request.user.orders.all().order_by('-created_at')
    return render(request, 'products/profile.html', {'orders': orders})

# --- 4. Order & Cart Processing (with Razorpay) ---

@login_required
def save_order(request):
    cart = get_object_or_404(Cart, user=request.user)
    cart_items = cart.items.all()

    if not cart_items:
        messages.error(request, "Your bag is empty.")
        return redirect('shop')

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

    amount_in_paise = int(total_amount * 100)
    payment_data = {
        "amount": amount_in_paise,
        "currency": "INR",
        "receipt": f"rasayam_order_{order.id}",
    }

    try:
        razorpay_order = razorpay_client.order.create(data=payment_data)
        order.razorpay_order_id = razorpay_order['id']
        order.save()

        cart_items.delete()

        return render(request, 'products/payment.html', {
            'order': order,
            'razorpay_order_id': razorpay_order['id'],
            'razorpay_key_id': settings.RAZORPAY_KEY_ID,
            'amount': amount_in_paise,
        })
    except Exception as e:
        messages.error(request, f"Gateway Error: {str(e)}")
        return redirect('cart')

@csrf_exempt
@login_required
def payment_verify(request):
    """Verifies Razorpay Signature and finalizes transaction"""
    if request.method == "POST":
        try:
            payment_id = request.POST.get('razorpay_payment_id')
            razorpay_order_id = request.POST.get('razorpay_order_id')
            signature = request.POST.get('razorpay_signature')

            params_dict = {
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature
            }

            razorpay_client.utility.verify_payment_signature(params_dict)

            order = Order.objects.get(razorpay_order_id=razorpay_order_id)
            order.razorpay_payment_id = payment_id
            order.razorpay_signature = signature
            order.is_paid = True
            order.status = 'Paid'
            order.save()

            messages.success(request, "Payment verified!")
            return redirect('payment_success', order_id=order.id)

        except Exception as e:
            print("Verification Error:", str(e))
            return redirect('payment_fail')
    return redirect('shop')

@login_required
def order_detail_view(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'products/order_detail.html', {'order': order})

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    
    messages.success(request, f"{product.name} added to Selection.")
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
    messages.info(request, "Item removed.")
    return redirect('cart')

@login_required
def add_to_cart_ajax(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    
    total_count = sum(item.quantity for item in cart.items.all())
    
    return JsonResponse({
        'status': 'success',
        'cart_count': total_count,
        'message': f"{product.name} added."
    })

def payment_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'products/payment_success.html', {'order': order})

def payment_fail(request):
    return render(request, 'products/payment_fail.html')

# --- Policy Pages ---
def privacy(request): return render(request, 'products/privacy.html')
def refund(request): return render(request, 'products/refund.html')
def shipping(request): return render(request, 'products/shipping.html')
def terms(request): return render(request, 'products/terms.html')