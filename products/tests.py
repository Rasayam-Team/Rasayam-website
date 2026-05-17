from django.test import TestCase
from django.urls import reverse
from .models import Category, Product

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