"""
Tests for ProductConcierge
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from weni_utils.tools import ProductConcierge
from weni_utils.tools.context import SearchContext
from weni_utils.tools.plugins import PluginBase

from dotenv import load_dotenv
import os

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))


class TestProductConcierge:
    """Tests for the ProductConcierge class."""
    
    def test_init_basic(self):
        """Test basic initialization."""
        concierge = ProductConcierge(
            base_url="https://test.vtexcommercestable.com.br",
            store_url="https://test.com.br"
        )
        
        assert concierge.client is not None
        assert concierge.stock_manager is not None
        assert concierge.plugins == []
        assert concierge.max_products == 20
        assert concierge.max_variations == 5
    
    def test_init_with_plugins(self):
        """Test initialization with plugins."""
        plugin = PluginBase()
        
        concierge = ProductConcierge(
            base_url="https://test.vtexcommercestable.com.br",
            store_url="https://test.com.br",
            plugins=[plugin]
        )
        
        assert len(concierge.plugins) == 1
        assert concierge.plugins[0] is plugin
    
    def test_init_with_config(self):
        """Test initialization with custom config."""
        concierge = ProductConcierge(
            base_url=os.getenv("VTEX_BASE_URL"),
            store_url=os.getenv("VTEX_STORE_URL"),
            max_products=10,
            max_variations=3,
            max_payload_kb=15,
            utm_source="weni_concierge"
        )

        search_result = concierge.search(product_name="ceramica")
        
        print(search_result)

    def test_search_process_products(self):
        """Test search: intelligent_search (client) + process_products (concierge)."""
        concierge = ProductConcierge(
            base_url=os.getenv("VTEX_BASE_URL"),
            store_url=os.getenv("VTEX_STORE_URL")
        )
        raw_result = concierge.intelligent_search(product_name="ceramica")
        formatted_result = concierge.process_products(raw_result, extra_product_fields=["clusterHighlights", "items.0.images", "imagemteste"])
        print(formatted_result)
        assert raw_result is not None
        assert len(raw_result) > 0
        assert formatted_result is not None
        assert isinstance(formatted_result, dict)
        assert len(formatted_result) > 0


class TestProductConciergePluginFlow:
    """Tests for plugin execution flow."""
    
    def test_plugin_before_search_called(self):
        """Test that before_search hook is called."""
        plugin = Mock(spec=PluginBase)
        plugin.before_search.return_value = SearchContext(product_name="test")
        plugin.after_search.return_value = {}
        plugin.after_stock_check.return_value = []
        plugin.enrich_products.return_value = {}
        plugin.finalize_result.return_value = {}
        
        concierge = ProductConcierge(
            base_url="https://test.vtexcommercestable.com.br",
            store_url="https://test.com.br",
            plugins=[plugin]
        )
        
        with patch.object(concierge.client, 'intelligent_search', return_value={}):
            with patch.object(concierge.stock_manager, 'check_availability_simple', return_value=[]):
                with patch.object(concierge.stock_manager, 'filter_products_with_stock', return_value={}):
                    with patch.object(concierge.stock_manager, 'limit_payload_size', return_value={}):
                        concierge.search(product_name="test")
        
        plugin.before_search.assert_called_once()
    
    def test_plugin_after_search_called(self):
        """Test that after_search hook is called."""
        plugin = Mock(spec=PluginBase)
        plugin.before_search.return_value = SearchContext(product_name="test")
        plugin.after_search.return_value = {"product": {}}
        plugin.after_stock_check.return_value = []
        plugin.enrich_products.return_value = {}
        plugin.finalize_result.return_value = {}
        
        concierge = ProductConcierge(
            base_url="https://test.vtexcommercestable.com.br",
            store_url="https://test.com.br",
            plugins=[plugin]
        )
        
        with patch.object(concierge.client, 'intelligent_search', return_value={"product": {}}):
            with patch.object(concierge.stock_manager, 'check_availability_simple', return_value=[]):
                with patch.object(concierge.stock_manager, 'filter_products_with_stock', return_value={}):
                    with patch.object(concierge.stock_manager, 'limit_payload_size', return_value={}):
                        concierge.search(product_name="test")
        
        plugin.after_search.assert_called_once()


class TestSearchContext:
    """Tests for SearchContext."""
    
    def test_context_creation(self):
        """Test context creation with defaults."""
        context = SearchContext(product_name="test")
        
        assert context.product_name == "test"
        assert context.brand_name == ""
        assert context.postal_code is None
        assert context.quantity == 1
        assert context.country_code == "BRA"
        assert context.sellers == []
    
    def test_context_add_to_result(self):
        """Test adding data to result."""
        context = SearchContext(product_name="test")
        
        context.add_to_result("key", "value")
        
        assert context.extra_data["key"] == "value"
    
    def test_context_get_credential(self):
        """Test getting credentials."""
        context = SearchContext(
            product_name="test",
            credentials={"API_KEY": "secret"}
        )
        
        assert context.get_credential("API_KEY") == "secret"
        assert context.get_credential("MISSING") is None
        assert context.get_credential("MISSING", "default") == "default"
