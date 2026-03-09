from unittest.mock import Mock, patch

import pytest
import requests

from weni_utils.tools.client import VTEXClient

VALID_BASE_URL = "https://test.vtexcommercestable.com.br"
VALID_STORE_URL = "https://test.com.br"


def _make_client(**kwargs):
    defaults = {"base_url_vtex": VALID_BASE_URL, "store_url_vtex": VALID_STORE_URL}
    defaults.update(kwargs)
    return VTEXClient(**defaults)


# ---------------------------------------------------------------------------
# Initialization & validation
# ---------------------------------------------------------------------------
class TestVTEXClientInit:
    def test_init_basic(self):
        client = _make_client()
        assert client.base_url_vtex == VALID_BASE_URL
        assert client.store_url_vtex == VALID_STORE_URL
        assert client.vtex_app_key is None
        assert client.vtex_app_token is None
        assert client.timeout == 30

    def test_init_with_credentials(self):
        client = _make_client(vtex_app_key="key", vtex_app_token="token")
        assert client.vtex_app_key == "key"
        assert client.vtex_app_token == "token"

    def test_init_strips_trailing_slash(self):
        client = _make_client(
            base_url=VALID_BASE_URL + "/",
            store_url=VALID_STORE_URL + "/",
        )
        assert not client.base_url_vtex.endswith("/")
        assert not client.store_url_vtex.endswith("/")

    def test_init_invalid_base_url_raises(self):
        with pytest.raises(ValueError):
            _make_client(base_url_vtex="http://invalid.com")

    def test_init_empty_urls_raises(self):
        with pytest.raises(ValueError):
            VTEXClient(base_url_vtex="", store_url_vtex="")

    def test_init_myvtex_domain(self):
        client = VTEXClient(
            base_url_vtex="https://store.myvtex.com",
            store_url_vtex=VALID_STORE_URL,
        )
        assert client.base_url_vtex == "https://store.myvtex.com"


class TestAuthHeaders:
    def test_without_credentials(self):
        headers = _make_client()._get_auth_headers()
        assert headers["Accept"] == "application/json"
        assert headers["Content-Type"] == "application/json"
        assert "X-VTEX-API-AppKey" not in headers

    def test_with_credentials(self):
        headers = _make_client(vtex_app_key="k", vtex_app_token="t")._get_auth_headers()
        assert headers["X-VTEX-API-AppKey"] == "k"
        assert headers["X-VTEX-API-AppToken"] == "t"


# ---------------------------------------------------------------------------
# Helper / pure-logic methods
# ---------------------------------------------------------------------------
class TestHelperMethods:
    @pytest.fixture()
    def client(self):
        return _make_client()

    def test_clean_image_url_with_query(self, client):
        assert client._clean_image_url("https://img.com/a.jpg?v=1") == "https://img.com/a.jpg"

    def test_clean_image_url_with_fragment(self, client):
        assert client._clean_image_url("https://img.com/a.png#top") == "https://img.com/a.png"

    def test_clean_image_url_both(self, client):
        assert client._clean_image_url("https://img.com/a.gif?v=1#s") == "https://img.com/a.gif"

    def test_clean_image_url_empty(self, client):
        assert client._clean_image_url("") == ""

    def test_format_variations(self, client):
        items = [
            {"name": "Color", "values": ["Blue"]},
            {"name": "Size", "values": ["M", "G"]},
        ]
        result = client._format_variations(items)
        assert "Color: Blue" in result
        assert "Size: M" in result

    def test_format_variations_empty(self, client):
        assert client._format_variations([]) == "{{}}"

    def test_truncate_description_short(self, client):
        assert client._truncate_description("short") == "short"

    def test_truncate_description_long(self, client):
        text = "x" * 300
        result = client._truncate_description(text, max_length=200)
        assert len(result) == 203  # 200 + "..."
        assert result.endswith("...")

    def test_get_nested_value_dict(self):
        data = {"a": {"b": {"c": 42}}}
        assert VTEXClient._get_nested_value(data, "a.b.c") == 42

    def test_get_nested_value_list(self):
        data = {"items": [{"id": "first"}, {"id": "second"}]}
        assert VTEXClient._get_nested_value(data, "items.1.id") == "second"

    def test_get_nested_value_missing(self):
        assert VTEXClient._get_nested_value({"a": 1}, "b.c") is None

    def test_get_nested_value_index_out_of_range(self):
        assert VTEXClient._get_nested_value({"a": [1]}, "a.5") is None

    def test_select_best_seller_default_with_stock(self, client):
        sellers = [
            {"sellerId": "2", "sellerDefault": False, "commertialOffer": {"AvailableQuantity": 5}},
            {"sellerId": "1", "sellerDefault": True, "commertialOffer": {"AvailableQuantity": 10}},
        ]
        seller, sid = client._select_best_seller(sellers)
        assert sid == "1"

    def test_select_best_seller_first_with_stock(self, client):
        sellers = [
            {"sellerId": "1", "sellerDefault": True, "commertialOffer": {"AvailableQuantity": 0}},
            {"sellerId": "2", "sellerDefault": False, "commertialOffer": {"AvailableQuantity": 3}},
        ]
        _, sid = client._select_best_seller(sellers)
        assert sid == "2"

    def test_select_best_seller_fallback(self, client):
        sellers = [
            {"sellerId": "1", "commertialOffer": {"AvailableQuantity": 0}},
        ]
        _, sid = client._select_best_seller(sellers)
        assert sid == "1"

    def test_select_best_seller_empty(self, client):
        seller, sid = client._select_best_seller([])
        assert seller is None and sid is None

    def test_extract_prices_from_seller(self, client):
        seller = {
            "commertialOffer": {
                "Price": 99.9,
                "spotPrice": 89.9,
                "ListPrice": 120.0,
                "Installments": [
                    {"PaymentSystemName": "Pix", "Value": 85.0},
                    {"PaymentSystemName": "Visa", "NumberOfInstallments": 1, "Value": 99.9},
                ],
            }
        }
        prices = client._extract_prices_from_seller(seller)
        assert prices["price"] == 99.9
        assert prices["pix_price"] == 85.0
        assert prices["credit_card_price"] == 99.9

    def test_extract_prices_from_seller_no_installments(self, client):
        seller = {"commertialOffer": {"Price": 50.0, "Installments": []}}
        prices = client._extract_prices_from_seller(seller)
        assert prices["price"] == 50.0
        assert prices["pix_price"] is None
        assert prices["credit_card_price"] is None

    def test_get_first_image(self, client):
        images = [{"imageUrl": "https://img.com/a.jpg?v=1"}]
        assert client._get_first_image(images) == "https://img.com/a.jpg"

    def test_get_first_image_empty(self, client):
        assert client._get_first_image([]) == ""
        assert client._get_first_image(None) == ""


# ---------------------------------------------------------------------------
# process_products (pure logic, no HTTP)
# ---------------------------------------------------------------------------
class TestProcessProducts:
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
                    "variations": [{"name": "Color", "values": ["Red"]}],
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

    def test_basic_processing(self):
        client = _make_client()
        result = client.process_products([self._raw_product()])
        assert "Product A" in result
        data = result["Product A"]
        assert data["brand"] == "Brand"
        assert len(data["variations"]) == 1
        assert data["variations"][0]["sku_id"] == "100"
        assert data["variations"][0]["price"] == 50.0
        assert "utm_source=weni_concierge" in data["productLink"]

    def test_max_products_limit(self):
        client = _make_client()
        raw = [self._raw_product(name=f"P{i}", sku_id=str(i)) for i in range(10)]
        result = client.process_products(raw, max_products=3)
        assert len(result) == 3

    def test_skips_products_without_items(self):
        client = _make_client()
        raw = [{"productName": "Empty", "items": []}]
        assert client.process_products(raw) == {}

    def test_extra_fields(self):
        client = _make_client()
        raw = self._raw_product()
        raw["clusterHighlights"] = {"123": "Promo"}
        result = client.process_products([raw], extra_product_fields=["clusterHighlights"])
        assert result["Product A"]["clusterHighlights"] == {"123": "Promo"}

    def test_extra_fields_with_alias(self):
        client = _make_client()
        raw = self._raw_product()
        result = client.process_products(
            [raw], extra_product_fields=[("items.0.itemId", "first_sku")]
        )
        assert result["Product A"]["first_sku"] == "100"

    def test_utm_source_none(self):
        client = _make_client()
        result = client.process_products([self._raw_product()], utm_source=None)
        assert "utm_source" not in result["Product A"]["productLink"]


# ---------------------------------------------------------------------------
# intelligent_search (mocked HTTP)
# ---------------------------------------------------------------------------
class TestIntelligentSearch:
    @patch("weni_utils.tools.client.requests.get")
    def test_returns_raw_product_list(self, mock_get):
        raw_products = [{"productName": "Drill", "items": []}]
        mock_get.return_value = Mock(
            status_code=200,
            json=Mock(return_value={"products": raw_products}),
            raise_for_status=Mock(),
        )
        result = _make_client().intelligent_search("drill")
        assert result == raw_products

    @patch("weni_utils.tools.client.requests.get")
    def test_empty_results(self, mock_get):
        mock_get.return_value = Mock(
            status_code=200,
            json=Mock(return_value={"products": []}),
            raise_for_status=Mock(),
        )
        assert _make_client().intelligent_search("nothing") == []

    @patch("weni_utils.tools.client.requests.get")
    def test_request_error_returns_empty(self, mock_get):
        mock_get.side_effect = requests.exceptions.Timeout()
        assert _make_client().intelligent_search("drill") == []

    @patch("weni_utils.tools.client.requests.get")
    def test_includes_region_id_in_url(self, mock_get):
        mock_get.return_value = Mock(
            status_code=200,
            json=Mock(return_value={"products": []}),
            raise_for_status=Mock(),
        )
        _make_client().intelligent_search("drill", region_id="v123")
        url = mock_get.call_args[0][0]
        assert "region-id/v123" in url

    @patch("weni_utils.tools.client.requests.get")
    def test_includes_trade_policy_and_cluster(self, mock_get):
        mock_get.return_value = Mock(
            status_code=200,
            json=Mock(return_value={"products": []}),
            raise_for_status=Mock(),
        )
        _make_client().intelligent_search("drill", trade_policy_id=2, cluster_id=99)
        url = mock_get.call_args[0][0]
        assert "trade-policy/2" in url
        assert "productClusterIds/99" in url


# ---------------------------------------------------------------------------
# cart_simulation (mocked HTTP)
# ---------------------------------------------------------------------------
class TestCartSimulation:
    @patch("weni_utils.tools.client.requests.post")
    def test_success(self, mock_post):
        body = {"items": [{"id": "1", "availability": "available"}]}
        mock_post.return_value = Mock(
            status_code=200,
            json=Mock(return_value=body),
            raise_for_status=Mock(),
        )
        items = [{"id": "1", "quantity": 1, "seller": "1"}]
        result = _make_client().cart_simulation(items)
        assert result["items"][0]["availability"] == "available"

    @patch("weni_utils.tools.client.requests.post")
    def test_with_postal_code_and_channel(self, mock_post):
        mock_post.return_value = Mock(
            status_code=200,
            json=Mock(return_value={"items": []}),
            raise_for_status=Mock(),
        )
        _make_client().cart_simulation(
            [{"id": "1", "quantity": 1, "seller": "1"}],
            postal_code="01310-100",
            sales_channel=2,
        )
        url = mock_post.call_args[0][0]
        assert "sc=2" in url
        payload = mock_post.call_args[1]["json"]
        assert payload["postalCode"] == "01310-100"

    @patch("weni_utils.tools.client.requests.post")
    def test_error_returns_empty_items(self, mock_post):
        mock_post.side_effect = requests.exceptions.ConnectionError()
        result = _make_client().cart_simulation([])
        assert result == {"items": []}


# ---------------------------------------------------------------------------
# get_region (mocked HTTP)
# ---------------------------------------------------------------------------
class TestGetRegion:
    @patch("weni_utils.tools.client.requests.get")
    def test_success(self, mock_get):
        mock_get.return_value = Mock(
            status_code=200,
            json=Mock(
                return_value=[
                    {
                        "id": "v123",
                        "sellers": [{"id": "s1"}, {"id": "s2"}],
                    }
                ]
            ),
            raise_for_status=Mock(),
        )
        rid, err, sellers = _make_client().get_region("01310-100", 1, "BRA")
        assert rid == "v123"
        assert err is None
        assert sellers == ["s1", "s2"]

    @patch("weni_utils.tools.client.requests.get")
    def test_empty_region(self, mock_get):
        mock_get.return_value = Mock(
            status_code=200,
            json=Mock(return_value=[]),
            raise_for_status=Mock(),
        )
        rid, err, sellers = _make_client().get_region("00000-000", 1, "BRA")
        assert rid is None
        assert err is not None
        assert sellers == []

    @patch("weni_utils.tools.client.requests.get")
    def test_no_sellers(self, mock_get):
        mock_get.return_value = Mock(
            status_code=200,
            json=Mock(return_value=[{"id": "v1", "sellers": []}]),
            raise_for_status=Mock(),
        )
        rid, err, _ = _make_client().get_region("01310-100", 1, "BRA")
        assert rid is None
        assert err is not None

    @patch("weni_utils.tools.client.requests.get")
    def test_request_error(self, mock_get):
        mock_get.side_effect = requests.exceptions.Timeout()
        rid, err, sellers = _make_client().get_region("01310-100", 1, "BRA")
        assert rid is None
        assert "Error" in err


# ---------------------------------------------------------------------------
# list_orders (mocked HTTP)
# ---------------------------------------------------------------------------
class TestListOrders:
    @patch("weni_utils.tools.client.requests.get")
    def test_empty_document(self, mock_get):
        result = _make_client(vtex_app_key="k", vtex_app_token="t").list_orders(document="")
        assert result["error"] == "Document or email is required"
        mock_get.assert_not_called()

    @patch("weni_utils.tools.client.requests.get")
    def test_returns_orders(self, mock_get):
        orders = {"list": [{"orderId": "O1"}, {"orderId": "O2"}]}
        mock_get.return_value = Mock(
            status_code=200,
            json=Mock(return_value=orders),
            raise_for_status=Mock(),
        )
        result = _make_client(vtex_app_key="k", vtex_app_token="t").list_orders(
            document="12345678900"
        )
        assert len(result["list"]) == 2

    @patch("weni_utils.tools.client.requests.get")
    def test_include_incomplete_merges(self, mock_get):
        complete = {"list": [{"orderId": "O1"}]}
        incomplete = {"list": [{"orderId": "O1"}, {"orderId": "O2"}]}
        mock_get.return_value = Mock(raise_for_status=Mock())
        mock_get.return_value.json = Mock(side_effect=[complete, incomplete])

        result = _make_client(vtex_app_key="k", vtex_app_token="t").list_orders(
            document="12345678900", include_incomplete=True
        )
        order_ids = {o["orderId"] for o in result["list"]}
        assert order_ids == {"O1", "O2"}


# ---------------------------------------------------------------------------
# get_order_by_id / batch_simulation
# ---------------------------------------------------------------------------
class TestOrderAndBatch:
    @patch("weni_utils.tools.client.requests.get")
    def test_get_order_by_id_success(self, mock_get):
        order = {"orderId": "O1", "status": "invoiced"}
        mock_get.return_value = Mock(
            status_code=200,
            json=Mock(return_value=order),
            raise_for_status=Mock(),
        )
        result = _make_client(vtex_app_key="k", vtex_app_token="t").get_order_by_id("O1")
        assert result["status"] == "invoiced"

    def test_get_order_by_id_empty(self):
        assert _make_client().get_order_by_id("") is None

    def test_batch_simulation_empty_sellers(self):
        assert (
            _make_client().batch_simulation(
                skus=[{"sku_id": "1", "quantity": 1}],
                sellers=[],
                postal_code="01310-100",
            )
            is None
        )

    def test_batch_simulation_empty_skus(self):
        assert (
            _make_client().batch_simulation(skus=[], sellers=["s1"], postal_code="01310-100")
            is None
        )

    def test_build_batch_items(self):
        client = _make_client()
        items = client._build_batch_items(
            skus=[{"sku_id": "10", "quantity": 2}],
            sellers=["s1", "s2"],
        )
        assert len(items) == 2
        assert items[0]["seller"] == "s1"
        assert items[1]["seller"] == "s2"
