from unittest.mock import Mock, patch

from weni_utils.tools.concierge import ProductConcierge
from weni_utils.tools.context import SearchContext

VALID_BASE_URL = "https://test.vtexcommercestable.com.br"
VALID_STORE_URL = "https://test.com.br"


def _make_concierge(**kwargs):
    defaults = {"base_url_vtex": VALID_BASE_URL, "store_url_vtex": VALID_STORE_URL}
    defaults.update(kwargs)
    return ProductConcierge(**defaults)


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------
class TestProductConciergeInit:
    def test_defaults(self):
        c = _make_concierge()
        assert c.max_products == 20
        assert c.max_variations == 5
        assert c.max_payload_kb == 20
        assert c.utm_source is None
        assert c.priority_categories == []

    def test_custom_config(self):
        c = _make_concierge(
            max_products=10,
            max_variations=3,
            max_payload_kb=15,
            utm_source="test_src",
            priority_categories=["/Floors/"],
        )
        assert c.max_products == 10
        assert c.max_variations == 3
        assert c.max_payload_kb == 15
        assert c.utm_source == "test_src"
        assert c.priority_categories == ["/Floors/"]


# ---------------------------------------------------------------------------
# search flow (all HTTP mocked)
# ---------------------------------------------------------------------------
class TestProductConciergeSearch:
    def _raw_product(self, name="Product A", sku_id="100", price=50.0):
        return {
            "productName": name,
            "description": "desc",
            "brand": "Brand",
            "link": "/product-a",
            "categories": ["/Cat/"],
            "specificationGroups": [],
            "items": [
                {
                    "itemId": sku_id,
                    "nameComplete": f"{name} - Var",
                    "variations": [],
                    "images": [{"imageUrl": "https://img.com/a.jpg"}],
                    "sellers": [
                        {
                            "sellerId": "1",
                            "sellerDefault": True,
                            "commertialOffer": {
                                "Price": price,
                                "AvailableQuantity": 10,
                                "Installments": [],
                            },
                        }
                    ],
                }
            ],
        }

    @patch("weni_utils.tools.client.requests.get")
    @patch("weni_utils.tools.client.requests.post")
    def test_search_full_flow(self, mock_post, mock_get):
        raw = [self._raw_product()]

        mock_get.return_value = Mock(
            status_code=200,
            json=Mock(return_value={"products": raw}),
            raise_for_status=Mock(),
        )
        mock_post.return_value = Mock(
            status_code=200,
            json=Mock(
                return_value={
                    "items": [
                        {"id": "100", "availability": "available", "quantity": 5, "seller": "1"}
                    ]
                }
            ),
            raise_for_status=Mock(),
        )

        c = _make_concierge()
        result = c.search(product_name="drill")
        assert isinstance(result, dict)

    @patch("weni_utils.tools.client.requests.get")
    @patch("weni_utils.tools.client.requests.post")
    def test_search_no_results(self, mock_post, mock_get):
        mock_get.return_value = Mock(
            status_code=200,
            json=Mock(return_value={"products": []}),
            raise_for_status=Mock(),
        )
        mock_post.return_value = Mock(
            status_code=200,
            json=Mock(return_value={"items": []}),
            raise_for_status=Mock(),
        )

        result = _make_concierge().search(product_name="nonexistent")
        assert result == {}

    @patch("weni_utils.tools.client.requests.get")
    @patch("weni_utils.tools.client.requests.post")
    def test_search_with_postal_code_calls_region(self, mock_post, mock_get):
        region_resp = Mock(
            status_code=200,
            json=Mock(return_value=[{"id": "v1", "sellers": [{"id": "s1"}]}]),
            raise_for_status=Mock(),
        )
        search_resp = Mock(
            status_code=200,
            json=Mock(return_value={"products": []}),
            raise_for_status=Mock(),
        )
        mock_get.side_effect = [region_resp, search_resp]
        mock_post.return_value = Mock(
            status_code=200,
            json=Mock(return_value={"items": []}),
            raise_for_status=Mock(),
        )

        _make_concierge().search(product_name="drill", postal_code="01310-100")
        assert mock_get.call_count == 2
        region_url = mock_get.call_args_list[0][0][0]
        assert "regions" in region_url


# ---------------------------------------------------------------------------
# SearchContext
# ---------------------------------------------------------------------------
class TestSearchContext:
    def test_defaults(self):
        ctx = SearchContext(product_name="test")
        assert ctx.product_name == "test"
        assert ctx.brand_name == ""
        assert ctx.postal_code is None
        assert ctx.quantity == 1
        assert ctx.country_code == "BRA"
        assert ctx.sellers == []
        assert ctx.extra_data == {}

    def test_add_to_result(self):
        ctx = SearchContext(product_name="test")
        ctx.add_to_result("key", "value")
        assert ctx.extra_data["key"] == "value"

    def test_get_credential(self):
        ctx = SearchContext(product_name="test", credentials={"API_KEY": "secret"})
        assert ctx.get_credential("API_KEY") == "secret"
        assert ctx.get_credential("MISSING") is None
        assert ctx.get_credential("MISSING", "default") == "default"

    def test_get_contact(self):
        ctx = SearchContext(product_name="test", contact_info={"urn": "whatsapp:+55"})
        assert ctx.get_contact("urn") == "whatsapp:+55"
        assert ctx.get_contact("missing", "fallback") == "fallback"

    def test_full_construction(self):
        ctx = SearchContext(
            product_name="drill",
            brand_name="Bosch",
            postal_code="01310-100",
            quantity=2,
            country_code="BRA",
            delivery_type="Delivery",
            trade_policy=2,
        )
        assert ctx.brand_name == "Bosch"
        assert ctx.postal_code == "01310-100"
        assert ctx.quantity == 2
        assert ctx.delivery_type == "Delivery"
        assert ctx.trade_policy == 2
