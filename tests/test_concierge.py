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
        assert c.utm_source == "weni_concierge"
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
    def test_search_default_utm_in_links(self, mock_post, mock_get):
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
        for product_data in result.values():
            assert "?utm_source=weni_concierge" in product_data["productLink"]
            assert "None" not in product_data["productLink"]

    @patch("weni_utils.tools.client.requests.get")
    @patch("weni_utils.tools.client.requests.post")
    def test_search_custom_utm_in_links(self, mock_post, mock_get):
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

        c = _make_concierge(utm_source="my_campaign")
        result = c.search(product_name="drill")
        for product_data in result.values():
            assert "?utm_source=my_campaign" in product_data["productLink"]

    @patch("weni_utils.tools.client.requests.get")
    @patch("weni_utils.tools.client.requests.post")
    def test_search_none_utm_clean_links(self, mock_post, mock_get):
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

        c = _make_concierge(utm_source=None)
        result = c.search(product_name="drill")
        for product_data in result.values():
            assert "utm_source" not in product_data["productLink"]
            assert "None" not in product_data["productLink"]

    @patch("weni_utils.tools.client.requests.get")
    @patch("weni_utils.tools.client.requests.post")
    def test_search_with_vtex_segment_raw_string(self, mock_post, mock_get):
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

        import json

        segment = json.dumps({"channel": "1", "regionId": "v2.ABC"})
        _make_concierge().search(product_name="drill", vtex_segment_raw=segment)

        headers = mock_get.call_args[1].get("headers")
        assert headers is not None
        assert "vtex_segment=" in headers.get("Cookie", "")

    @patch("weni_utils.tools.client.requests.get")
    @patch("weni_utils.tools.client.requests.post")
    def test_search_with_weni_context_auto_extracts_segment(self, mock_post, mock_get):
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

        import json

        from weni.context import Context

        ctx = Context(
            credentials={},
            parameters={},
            globals={},
            contact={
                "fields": {"vtex_segment": json.dumps({"channel": "2", "regionId": "v2.XYZ"})}
            },
            project={},
            constants={},
        )
        _make_concierge().search(product_name="drill", context=ctx)

        headers = mock_get.call_args[1].get("headers")
        assert headers is not None
        assert "vtex_segment=" in headers.get("Cookie", "")

    @patch("weni_utils.tools.client.requests.get")
    @patch("weni_utils.tools.client.requests.post")
    def test_search_context_without_segment_no_cookie(self, mock_post, mock_get):
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

        from weni.context import Context

        ctx = Context(
            credentials={},
            parameters={},
            globals={},
            contact={"fields": {}},
            project={},
            constants={},
        )
        _make_concierge().search(product_name="drill", context=ctx)

        headers = mock_get.call_args[1].get("headers")
        assert headers is None

    @patch("weni_utils.tools.client.requests.get")
    @patch("weni_utils.tools.client.requests.post")
    def test_search_vtex_segment_raw_overrides_context(self, mock_post, mock_get):
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

        import base64
        import json

        from weni.context import Context

        ctx = Context(
            credentials={},
            parameters={},
            globals={},
            contact={"fields": {"vtex_segment": json.dumps({"channel": "from-context"})}},
            project={},
            constants={},
        )
        explicit = json.dumps({"channel": "explicit-override"})
        _make_concierge().search(product_name="drill", context=ctx, vtex_segment_raw=explicit)

        cookie = mock_get.call_args[1]["headers"]["Cookie"]
        cookie_value = cookie.split("vtex_segment=")[1]
        decoded = json.loads(base64.b64decode(cookie_value).decode("utf-8"))
        assert decoded["channel"] == "explicit-override"

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

    # --- prefer_default_seller at search level ---

    def _raw_product_multi_seller(self):
        return {
            "productName": "Multi Seller",
            "description": "desc",
            "brand": "Brand",
            "link": "/multi-seller",
            "categories": ["/Cat/"],
            "specificationGroups": [],
            "items": [
                {
                    "itemId": "200",
                    "nameComplete": "Multi Seller - Var",
                    "variations": [],
                    "images": [{"imageUrl": "https://img.com/a.jpg"}],
                    "sellers": [
                        {
                            "sellerId": "marketplace",
                            "sellerDefault": False,
                            "commertialOffer": {
                                "Price": 90.0,
                                "AvailableQuantity": 5,
                                "Installments": [],
                            },
                        },
                        {
                            "sellerId": "store",
                            "sellerDefault": True,
                            "commertialOffer": {
                                "Price": 100.0,
                                "AvailableQuantity": 10,
                                "Installments": [],
                            },
                        },
                    ],
                }
            ],
        }

    @patch("weni_utils.tools.client.requests.get")
    @patch("weni_utils.tools.client.requests.post")
    def test_search_default_prefers_default_seller(self, mock_post, mock_get):
        raw = [self._raw_product_multi_seller()]
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
                        {
                            "id": "200",
                            "availability": "available",
                            "quantity": 5,
                            "seller": "1",
                        }
                    ]
                }
            ),
            raise_for_status=Mock(),
        )

        result = _make_concierge().search(product_name="drill")
        assert result["Multi Seller"]["variations"][0]["sellerId"] == "store"

    @patch("weni_utils.tools.client.requests.get")
    @patch("weni_utils.tools.client.requests.post")
    def test_search_prefer_default_seller_false_picks_first(self, mock_post, mock_get):
        raw = [self._raw_product_multi_seller()]
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
                        {
                            "id": "200",
                            "availability": "available",
                            "quantity": 5,
                            "seller": "1",
                        }
                    ]
                }
            ),
            raise_for_status=Mock(),
        )

        result = _make_concierge().search(product_name="drill", prefer_default_seller=False)
        assert result["Multi Seller"]["variations"][0]["sellerId"] == "marketplace"


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
