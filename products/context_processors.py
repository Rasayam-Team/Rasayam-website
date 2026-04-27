from .models import Cart

def cart_count(request):
    if request.user.is_authenticated:
        # Get or create the cart for the user
        cart, _ = Cart.objects.get_or_create(user=request.user)
        # Count the total number of items (sum of quantities)
        count = sum(item.quantity for item in cart.items.all())
        return {'cart_count': count}
    return {'cart_count': 0}