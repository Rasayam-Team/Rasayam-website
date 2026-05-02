from django.db import models
from django.contrib.auth.models import User

# --- 1. User Infrastructure ---
class CustomerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    otp = models.CharField(max_length=6, blank=True, null=True)
    otp_created_at = models.DateTimeField(blank=True, null=True)
    
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    gender = models.CharField(max_length=10, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return self.user.username

class Banner(models.Model):
    title = models.CharField(max_length=100, blank=True)
    image = models.ImageField(upload_to='banners/')
    active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)

    def __str__(self):
        return self.title or f"Banner {self.id}"


class PromoBox(models.Model):
    title = models.CharField(max_length=100)
    subtitle = models.CharField(max_length=200, blank=True)
    link_url = models.CharField(max_length=500, blank=True, null=True)
    link_text = models.CharField(max_length=50, default="Shop Now")
    order = models.IntegerField(default=0)

    class Meta:
        verbose_name_plural = "Promo Boxes"
        ordering = ['order']

    def __str__(self):
        return self.title

# --- 2. Catalog ---

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True, null=True)
    order = models.IntegerField(default=0)
    image = models.ImageField(upload_to='category_images/', blank=True, null=True)
    
    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

class Size(models.Model):
    """Allows admin to create sizes like XS, S, M, L, XL, 5XL etc."""
    name = models.CharField(max_length=10, unique=True)
    
    def __str__(self):
        return self.name

class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    # This acts as the "Main" thumbnail image
    image = models.ImageField(upload_to='product_images/', blank=True, null=True)
    
    # Detailed Info for the Dedicated Product Page
    description = models.TextField(blank=True, help_text="Detailed story or description of the product.")
    highlights = models.TextField(blank=True, help_text="Amazon-style bullet points. Enter each highlight on a new line.")
    fabric_details = models.TextField(blank=True)
    seller_tag = models.CharField(max_length=50, blank=True)
    
    # Size selection
    sizes = models.ManyToManyField(Size, blank=True, help_text="Hold Ctrl to select multiple sizes.")

    def __str__(self):
        return self.name

class ProductImage(models.Model):
    """Allows for multiple gallery images for a single product."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='gallery_images')
    image = models.ImageField(upload_to='product_gallery/')
    alt_text = models.CharField(max_length=255, blank=True, help_text="Optional: Describes image for SEO.")

    def __str__(self):
        return f"Gallery Image for {self.product.name}"

# --- 3. Interaction & Orders ---

class ContactInquiry(models.Model):
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Contact Inquiries"

class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(default=5) 
    comment = models.TextField()
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='Pending')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    # --- RAZORPAY PAYMENT FIELDS ---
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)
    is_paid = models.BooleanField(default=False)

    def __str__(self):
        return f"Order {self.id} by {self.user.username}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product_name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    image_url = models.URLField(blank=True)

# --- 4. Cart Logic ---

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart for {self.user.username}"

    @property
    def total_price(self):
        return sum(item.total_item_price for item in self.items.all())

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    @property
    def total_item_price(self):
        return self.product.price * self.quantity