# products/admin.py
from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline 
from import_export.admin import ImportExportModelAdmin
from unfold.contrib.import_export.forms import ExportForm, ImportForm
from .models import (
    CustomerProfile, Product, Banner, Category, 
    Order, OrderItem, Review, PromoBox, ContactInquiry
)

# --- 1. Product Management with Import/Export ---

@admin.register(Product)
class ProductAdmin(ModelAdmin, ImportExportModelAdmin):
    import_form_class = ImportForm
    export_form_class = ExportForm

    list_display = ('name', 'price', 'seller_tag', 'category')
    list_filter = ('category', 'seller_tag')
    search_fields = ('name', 'description')
    fixed_submit_bar = True

# --- 2. Branding & Content ---

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
    list_display = ('title', 'subtitle', 'order')

@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ('name', 'order')
    search_fields = ('name',)

# --- 3. User & Interaction ---

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

# --- 4. Orders: The Heart of the Business (MERGED) ---

class OrderItemInline(TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('price',) 

@admin.register(Order)
class OrderAdmin(ModelAdmin):
    # Combined display to show payment status and total at a glance
    list_display = ('id', 'user', 'total_amount', 'is_paid', 'status', 'created_at')
    
    # Combined filters for better accounting
    list_filter = ('is_paid', 'status', 'created_at')
    
    # Razorpay fields are locked to prevent accidental manual changes
    readonly_fields = ('razorpay_order_id', 'razorpay_payment_id', 'razorpay_signature')
    
    # Includes the list of items inside the order view
    inlines = [OrderItemInline]
    
    fixed_submit_bar = True