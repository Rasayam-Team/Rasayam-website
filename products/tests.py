from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Cart, CartItem, Category, Product

class RasayamCoreSystemTests(TestCase):

    def setUp(self):
        """Build mock data structures in memory with fake image references"""
        self.category_odisha = Category.objects.create(
            name="Odisha", 
            slug="odisha",
            image="mock_odisha.jpg"  # 🌟 Added fake image string
        )
        self.category_punjab = Category.objects.create(
            name="Punjab", 
            slug="punjab",
            image="mock_punjab.jpg"  # 🌟 Added fake image string
        )
        
        # Build mock listings with image placeholders to keep template renderers happy
        self.item_ikat = Product.objects.create(
            name="Premium Ikat Silk Kurti",
            price=4500,
            category=self.category_odisha,
            seller_tag="Handloom Artisan",
            image="mock_ikat.jpg"  # 🌟 Added fake image string
        )
        self.item_phulkari = Product.objects.create(
            name="Heritage Phulkari Suit",
            price=6800,
            category=self.category_punjab,
            seller_tag="Vintage Craft",
            image="mock_phulkari.jpg"  # 🌟 Added fake image string
        )

        self.category_plain = Category.objects.create(name="Plain Cotton", slug="plain-cotton")
        self.category_without_slug = Category.objects.create(name="Unlinked Category")
        self.item_without_image = Product.objects.create(
            name="Minimal Cotton Kurti",
            price=2200,
            category=self.category_plain,
            seller_tag="Everyday Craft",
        )

    def test_homepage_render_and_grid_context(self):
        """Verify the index view successfully parses our variety categories"""
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.category_odisha, response.context['categories'])

    def test_search_engine_by_name(self):
        """Verify search handles direct name intersections matching database queries"""
        response = self.client.get(reverse('search'), {'q': 'Ikat'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Premium Ikat Silk Kurti")

    def test_search_engine_by_seller_tag(self):
        """Verify complex Q filters accurately evaluate multi-column tag parameters"""
        response = self.client.get(reverse('search'), {'q': 'Vintage'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Heritage Phulkari Suit")

    def test_search_engine_empty_fallbacks(self):
        """Verify layout system provides a clean UX empty state if no matches occur"""
        response = self.client.get(reverse('search'), {'q': 'NonExistentProductStyle'})
        self.assertEqual(response.status_code, 200)

    def test_storefront_pages_render_optional_images_and_slugs(self):
        """Optional images and blank category slugs should not crash templates."""
        urls = [
            reverse('index'),
            reverse('shop'),
            reverse('category_detail', args=[self.category_plain.slug]),
            reverse('product_detail', args=[self.item_without_image.id]),
        ]

        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('search'), {'q': 'Minimal'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Minimal Cotton Kurti")

    def test_cart_renders_item_without_image(self):
        """Cart thumbnails should fall back cleanly when a product has no image."""
        user = User.objects.create_user(username="buyer", password="test-pass-123")
        cart = Cart.objects.create(user=user)
        CartItem.objects.create(cart=cart, product=self.item_without_image, quantity=1)

        self.client.force_login(user)
        response = self.client.get(reverse('cart'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Minimal Cotton Kurti")
