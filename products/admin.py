# products/admin.py
from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline # <--- The Unfold upgrades
from .models import (
    CustomerProfile, Product, Banner, Category, 
    Order, OrderItem, Review, PromoBox, ContactInquiry
)

# products/admin.py
from import_export.admin import ImportExportModelAdmin
from unfold.contrib.import_export.forms import ExportForm, ImportForm
# ... keep your other imports ...

@admin.register(Product)
class ProductAdmin(ModelAdmin, ImportExportModelAdmin): # Inherit from both
    # These two lines ensure the Import/Export pages match the Unfold UI
    import_form_class = ImportForm
    export_form_class = ExportForm

    list_display = ('name', 'price', 'seller_tag', 'category')
    list_filter = ('category', 'seller_tag')
    search_fields = ('name', 'description')
    
    # Keeps the premium feel
    fixed_submit_bar = True

# --- Register everything with Unfold ---

@admin.register(Banner)
class BannerAdmin(ModelAdmin):
    list_display = ('display_banner', 'title', 'active', 'order')
    list_filter = ('active',)
    
    def display_banner(self, obj):
        if obj.image:
            # Added a slight border radius to match the modern UI
            return format_html('<img src="{}" style="width: 100px; height: 40px; object-fit: cover; border-radius: 4px;" />', obj.image.url)
        return "No Image"

@admin.register(PromoBox)
class PromoBoxAdmin(ModelAdmin):
    list_display = ('title', 'subtitle', 'order')

@admin.register(ContactInquiry)
class ContactInquiryAdmin(ModelAdmin):
    list_display = ('full_name', 'email', 'subject', 'created_at')
    readonly_fields = ('created_at',)
    # Makes long inquiry texts easier to read in the admin
    list_filter = ('created_at',)

@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ('name', 'order')
    search_fields = ('name',)

@admin.register(Review)
class ReviewAdmin(ModelAdmin):
    list_display = ('user', 'product', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')

@admin.register(CustomerProfile)
class CustomerProfileAdmin(ModelAdmin):
    list_display = ('user', 'phone_number', 'city', 'is_verified', 'otp')
    list_filter = ('is_verified', 'city')
    search_fields = ('user__username', 'phone_number')

# --- Orders: The Heart of the Business ---

class OrderItemInline(TabularInline): # Unfold styled inline
    model = OrderItem
    extra = 0
    # Makes the product selection inside an order look much cleaner
    readonly_fields = ('price',) 

@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = ('id', 'user', 'status', 'total_amount', 'created_at')
    list_filter = ('status', 'created_at')
    inlines = [OrderItemInline]
    
    # Color-coded status for the owner to see at a glance
    # You can add this logic later to make the statuses colorful!
    fixed_submit_bar = True