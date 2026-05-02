# products/admin.py
from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline 
from import_export.admin import ImportExportModelAdmin
from unfold.contrib.import_export.forms import ExportForm, ImportForm
from .models import (
    CustomerProfile, Product, Banner, Category, 
    Order, OrderItem, Review, PromoBox, ContactInquiry,
    Size, ProductImage  # Added these
)

# --- 1. Product Inlines & Size Management ---

class ProductImageInline(TabularInline):
    """Allows uploading multiple gallery images directly on the Product page"""
    model = ProductImage
    extra = 3  # Provides 3 empty slots for side, back, and close-up views
    tab = True # Unfold specific: puts inlines in a nice tab

@admin.register(Size)
class SizeAdmin(ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

# --- 2. Product Management with Gallery & Sizes ---

@admin.register(Product)
class ProductAdmin(ModelAdmin, ImportExportModelAdmin):
    import_form_class = ImportForm
    export_form_class = ExportForm

    list_display = ('display_thumbnail', 'name', 'price', 'category', 'seller_tag')
    list_filter = ('category', 'seller_tag', 'sizes')
    search_fields = ('name', 'description')
    
    # Enables a nice side-by-side selection for sizes
    filter_horizontal = ('sizes',)
    
    # Adds the image gallery uploader
    inlines = [ProductImageInline]
    
    fixed_submit_bar = True

    def display_thumbnail(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 4px;" />', obj.image.url)
        return "No Image"
    display_thumbnail.short_description = "Main View"

# --- 3. Branding & Content ---

@admin.register(Banner)
class BannerAdmin(ModelAdmin):
    list_display = ('display_banner', 'title', 'active', 'order')
    list_filter = ('active',)
    
    def display_banner(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width: 100px; height: 40px; object-fit: cover; border-radius: 4px;" />', obj.image.url)
        return "No Image"

@admin.register(PromoBox)
class PromoBoxAdmin(ModelAdmin):
    list_display = ('title', 'subtitle', 'link_text', 'link_url', 'order')
    list_editable = ('order', 'link_text', 'link_url')

@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ('name', 'order')
    search_fields = ('name',)

# --- 4. User & Interaction ---

@admin.register(CustomerProfile)
class CustomerProfileAdmin(ModelAdmin):
    list_display = ('user', 'phone_number', 'city', 'is_verified', 'otp')
    list_filter = ('is_verified', 'city')
    search_fields = ('user__username', 'phone_number')

@admin.register(ContactInquiry)
class ContactInquiryAdmin(ModelAdmin):
    list_display = ('full_name', 'email', 'subject', 'created_at')
    readonly_fields = ('created_at',)
    list_filter = ('created_at',)

@admin.register(Review)
class ReviewAdmin(ModelAdmin):
    list_display = ('user', 'product', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')

# --- 5. Orders & Payments ---

class OrderItemInline(TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('price',) 

@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = ('id', 'user', 'total_amount', 'is_paid', 'status', 'created_at')
    list_filter = ('is_paid', 'status', 'created_at')
    
    # Razorpay fields are locked to maintain transaction integrity
    readonly_fields = ('razorpay_order_id', 'razorpay_payment_id', 'razorpay_signature')
    
    inlines = [OrderItemInline]
    fixed_submit_bar = True