from weni_utils.tools.utils import Utils, convert_cents


# ---------------------------------------------------------------------------
# convert_cents (standalone function)
# ---------------------------------------------------------------------------
class TestConvertCents:
    def test_flat_dict_converts_known_keys(self):
        data = {"totalValue": 1500, "value": 990, "name": "Widget"}
        result = convert_cents(data)
        assert result["totalValue"] == 15.0
        assert result["value"] == 9.9
        assert result["name"] == "Widget"

    def test_nested_dict(self):
        data = {"order": {"price": 4999, "tax": 100, "label": "ok"}}
        result = convert_cents(data)
        assert result["order"]["price"] == 49.99
        assert result["order"]["tax"] == 1.0
        assert result["order"]["label"] == "ok"

    def test_list_of_dicts(self):
        data = [{"sellingPrice": 2000}, {"sellingPrice": 3000}]
        result = convert_cents(data)
        assert result[0]["sellingPrice"] == 20.0
        assert result[1]["sellingPrice"] == 30.0

    def test_none_values_are_preserved(self):
        data = {"price": None, "discount": None}
        result = convert_cents(data)
        assert result["price"] is None
        assert result["discount"] is None

    def test_non_currency_keys_untouched(self):
        data = {"quantity": 500, "weight": 200}
        result = convert_cents(data)
        assert result["quantity"] == 500
        assert result["weight"] == 200

    def test_case_insensitive_matching(self):
        data = {"TotalValue": 1000, "SELLINGPRICE": 2000}
        result = convert_cents(data)
        assert result["TotalValue"] == 10.0
        assert result["SELLINGPRICE"] == 20.0

    def test_deeply_nested_structure(self):
        data = {"a": {"b": [{"listPrice": 500}]}}
        result = convert_cents(data)
        assert result["a"]["b"][0]["listPrice"] == 5.0

    def test_non_dict_non_list_passthrough(self):
        assert convert_cents("hello") == "hello"
        assert convert_cents(42) == 42
        assert convert_cents(None) is None

    def test_empty_structures(self):
        assert convert_cents({}) == {}
        assert convert_cents([]) == []

    def test_string_value_in_currency_key_untouched(self):
        data = {"price": "free"}
        result = convert_cents(data)
        assert result["price"] == "free"

    def test_zero_value(self):
        data = {"discount": 0}
        result = convert_cents(data)
        assert result["discount"] == 0.0

    def test_rounding(self):
        data = {"price": 1}
        result = convert_cents(data)
        assert result["price"] == 0.01


# ---------------------------------------------------------------------------
# Utils.encode_vtex_segment
# ---------------------------------------------------------------------------
class TestEncodeVtexSegment:
    def test_dict_input(self):
        result = Utils.encode_vtex_segment({"channel": "1", "regionId": "v2.ABC"})
        assert result is not None
        import base64
        import json

        decoded = json.loads(base64.b64decode(result))
        assert decoded["channel"] == "1"
        assert decoded["regionId"] == "v2.ABC"

    def test_json_string_input(self):
        import json

        raw = json.dumps({"channel": "2"})
        result = Utils.encode_vtex_segment(raw)
        assert result is not None

        import base64

        decoded = json.loads(base64.b64decode(result))
        assert decoded["channel"] == "2"

    def test_empty_string_returns_none(self):
        assert Utils.encode_vtex_segment("") is None

    def test_none_returns_none(self):
        assert Utils.encode_vtex_segment(None) is None

    def test_empty_dict_returns_none(self):
        assert Utils.encode_vtex_segment({}) is None

    def test_invalid_json_string_returns_none(self):
        assert Utils.encode_vtex_segment("{not valid json}") is None

    def test_unsupported_type_returns_none(self):
        assert Utils.encode_vtex_segment(12345) is None

    def test_list_type_returns_none(self):
        assert Utils.encode_vtex_segment([1, 2, 3]) is None


# ---------------------------------------------------------------------------
# Utils.format_vtex_account
# ---------------------------------------------------------------------------
class TestFormatVtexAccount:
    def _make_utils(self, base_url):
        u = Utils()
        u.base_url_vtex = base_url
        return u

    def test_standard_myvtex_url(self):
        u = self._make_utils("https://bravtexgrocerystore.myvtex.com")
        assert u.format_vtex_account() == "bravtexgrocerystore"

    def test_vtexcommercestable_url(self):
        u = self._make_utils("https://mystore.vtexcommercestable.com.br")
        assert u.format_vtex_account() == "mystore"

    def test_empty_url_returns_none(self):
        u = self._make_utils("")
        assert u.format_vtex_account() is None

    def test_none_url_returns_none(self):
        u = self._make_utils(None)
        assert u.format_vtex_account() is None

    def test_url_without_scheme(self):
        u = self._make_utils("store.myvtex.com")
        assert u.format_vtex_account() == "store"


# ---------------------------------------------------------------------------
# process_products (changed method: store_url_vtex is now a parameter)
# ---------------------------------------------------------------------------
class TestProcessProducts:
    STORE_URL = "https://mystore.com.br"

    def _raw_product(self, name="Product A", sku_id="100", price=50.0):
        return {
            "productName": name,
            "description": "A short description",
            "brand": "BrandX",
            "link": "/product-a/p",
            "categories": ["/Electronics/"],
            "specificationGroups": [],
            "items": [
                {
                    "itemId": sku_id,
                    "nameComplete": f"{name} - Default",
                    "variations": [{"name": "Color", "values": ["Blue"]}],
                    "images": [{"imageUrl": "https://img.vtex.com/a.jpg?v=123"}],
                    "sellers": [
                        {
                            "sellerId": "1",
                            "sellerDefault": True,
                            "commertialOffer": {
                                "Price": price,
                                "ListPrice": price + 10,
                                "spotPrice": price - 2,
                                "AvailableQuantity": 10,
                                "Installments": [],
                            },
                        }
                    ],
                }
            ],
        }

    def test_store_url_as_parameter(self):
        """The main change: store_url_vtex comes from the parameter, not self."""
        utils = Utils()
        result = utils.process_products([self._raw_product()], store_url_vtex=self.STORE_URL)
        product = result["Product A"]
        assert product["productLink"].startswith(self.STORE_URL)

    def test_store_url_none_still_builds_link(self):
        utils = Utils()
        result = utils.process_products([self._raw_product()], store_url_vtex=None)
        product = result["Product A"]
        assert "None/product-a/p" in product["productLink"]

    def test_default_utm_source_appended(self):
        utils = Utils()
        result = utils.process_products([self._raw_product()], store_url_vtex=self.STORE_URL)
        assert "?utm_source=weni_concierge" in result["Product A"]["productLink"]

    def test_custom_utm_source(self):
        utils = Utils()
        result = utils.process_products(
            [self._raw_product()],
            store_url_vtex=self.STORE_URL,
            utm_source="custom_campaign",
        )
        assert "?utm_source=custom_campaign" in result["Product A"]["productLink"]

    def test_no_utm_source(self):
        utils = Utils()
        result = utils.process_products(
            [self._raw_product()], store_url_vtex=self.STORE_URL, utm_source=None
        )
        assert "utm_source" not in result["Product A"]["productLink"]

    def test_max_products_limit(self):
        utils = Utils()
        raw = [self._raw_product(name=f"P{i}", sku_id=str(i)) for i in range(10)]
        result = utils.process_products(raw, store_url_vtex=self.STORE_URL, max_products=3)
        assert len(result) == 3

    def test_max_variations_limit(self):
        product = self._raw_product()
        product["items"] = [
            {
                "itemId": str(i),
                "nameComplete": f"Var {i}",
                "variations": [],
                "images": [],
                "sellers": [
                    {
                        "sellerId": "1",
                        "sellerDefault": True,
                        "commertialOffer": {
                            "Price": 10.0,
                            "AvailableQuantity": 5,
                            "Installments": [],
                        },
                    }
                ],
            }
            for i in range(10)
        ]
        utils = Utils()
        result = utils.process_products([product], store_url_vtex=self.STORE_URL, max_variations=2)
        assert len(result["Product A"]["variations"]) == 2

    def test_skips_products_without_items(self):
        raw = [{"productName": "Empty", "items": []}]
        utils = Utils()
        result = utils.process_products(raw, store_url_vtex=self.STORE_URL)
        assert result == {}

    def test_skips_products_with_no_items_key(self):
        raw = [{"productName": "NoItems"}]
        utils = Utils()
        result = utils.process_products(raw, store_url_vtex=self.STORE_URL)
        assert result == {}

    def test_empty_input(self):
        utils = Utils()
        assert utils.process_products([], store_url_vtex=self.STORE_URL) == {}

    def test_product_data_fields(self):
        utils = Utils()
        result = utils.process_products([self._raw_product()], store_url_vtex=self.STORE_URL)
        product = result["Product A"]
        assert "variations" in product
        assert "description" in product
        assert "brand" in product
        assert product["brand"] == "BrandX"
        assert "specification_groups" in product
        assert "productLink" in product
        assert "imageUrl" in product
        assert "categories" in product
        assert product["categories"] == ["/Electronics/"]

    def test_extra_product_fields_string(self):
        raw = self._raw_product()
        raw["clusterHighlights"] = {"1": "Promo"}
        utils = Utils()
        result = utils.process_products(
            [raw],
            store_url_vtex=self.STORE_URL,
            extra_product_fields=["clusterHighlights"],
        )
        assert result["Product A"]["clusterHighlights"] == {"1": "Promo"}

    def test_extra_product_fields_tuple_with_alias(self):
        raw = self._raw_product()
        utils = Utils()
        result = utils.process_products(
            [raw],
            store_url_vtex=self.STORE_URL,
            extra_product_fields=[("items.0.images", "images")],
        )
        assert "images" in result["Product A"]

    def test_remove_specifications(self):
        raw = self._raw_product()
        raw["specificationGroups"] = [
            {
                "name": "allSpecifications",
                "specifications": [
                    {"name": "sellerId", "values": ["1"]},
                    {"name": "color", "values": ["blue"]},
                ],
            }
        ]
        utils = Utils()
        result = utils.process_products(
            [raw],
            store_url_vtex=self.STORE_URL,
            remove_specifications=["sellerId"],
        )
        specs_str = result["Product A"]["specification_groups"][0]["specifications"]
        assert "sellerId" not in specs_str
        assert "color" in specs_str

    def test_remove_specifications_also_filters_variations(self):
        raw = self._raw_product()
        raw["items"][0]["variations"] = [
            {"name": "Color", "values": ["Blue"]},
            {"name": "VALOR_HEX_ORIGINAL", "values": ["#30B349"]},
            {"name": "ID_COR_ORIGINAL", "values": ["049"]},
        ]
        utils = Utils()
        result = utils.process_products(
            [raw],
            store_url_vtex=self.STORE_URL,
            remove_specifications=["VALOR_HEX_ORIGINAL", "ID_COR_ORIGINAL"],
        )
        variations_str = result["Product A"]["variations"][0]["variations"]
        assert "Color" in variations_str
        assert "VALOR_HEX_ORIGINAL" not in variations_str
        assert "ID_COR_ORIGINAL" not in variations_str


# ---------------------------------------------------------------------------
# _select_best_seller
# ---------------------------------------------------------------------------
class TestSelectBestSeller:
    def _utils(self):
        return Utils()

    def test_empty_sellers(self):
        seller, sid = self._utils()._select_best_seller([])
        assert seller is None
        assert sid is None

    def test_single_seller_with_stock(self):
        sellers = [
            {
                "sellerId": "1",
                "sellerDefault": True,
                "commertialOffer": {"AvailableQuantity": 5},
            }
        ]
        seller, sid = self._utils()._select_best_seller(sellers)
        assert sid == "1"

    def test_prefer_default_seller_true(self):
        sellers = [
            {
                "sellerId": "marketplace",
                "sellerDefault": False,
                "commertialOffer": {"AvailableQuantity": 5},
            },
            {
                "sellerId": "default",
                "sellerDefault": True,
                "commertialOffer": {"AvailableQuantity": 3},
            },
        ]
        _, sid = self._utils()._select_best_seller(sellers, prefer_default_seller=True)
        assert sid == "default"

    def test_prefer_default_seller_false(self):
        sellers = [
            {
                "sellerId": "marketplace",
                "sellerDefault": False,
                "commertialOffer": {"AvailableQuantity": 5},
            },
            {
                "sellerId": "default",
                "sellerDefault": True,
                "commertialOffer": {"AvailableQuantity": 3},
            },
        ]
        _, sid = self._utils()._select_best_seller(sellers, prefer_default_seller=False)
        assert sid == "marketplace"

    def test_default_seller_no_stock_falls_back(self):
        sellers = [
            {
                "sellerId": "nostock",
                "sellerDefault": True,
                "commertialOffer": {"AvailableQuantity": 0},
            },
            {
                "sellerId": "hasstock",
                "sellerDefault": False,
                "commertialOffer": {"AvailableQuantity": 10},
            },
        ]
        _, sid = self._utils()._select_best_seller(sellers, prefer_default_seller=True)
        assert sid == "hasstock"

    def test_no_stock_anywhere_returns_first(self):
        sellers = [
            {
                "sellerId": "a",
                "sellerDefault": False,
                "commertialOffer": {"AvailableQuantity": 0},
            },
            {
                "sellerId": "b",
                "sellerDefault": True,
                "commertialOffer": {"AvailableQuantity": 0},
            },
        ]
        _, sid = self._utils()._select_best_seller(sellers)
        assert sid == "a"


# ---------------------------------------------------------------------------
# _extract_prices_from_seller
# ---------------------------------------------------------------------------
class TestExtractPricesFromSeller:
    def _utils(self):
        return Utils()

    def test_basic_prices(self):
        seller = {
            "commertialOffer": {
                "Price": 99.90,
                "spotPrice": 89.90,
                "ListPrice": 119.90,
                "Installments": [],
            }
        }
        prices = self._utils()._extract_prices_from_seller(seller)
        assert prices["price"] == 99.90
        assert prices["spot_price"] == 89.90
        assert prices["list_price"] == 119.90
        assert prices["pix_price"] is None
        assert prices["credit_card_price"] is None

    def test_pix_installment(self):
        seller = {
            "commertialOffer": {
                "Price": 100.0,
                "Installments": [
                    {"PaymentSystemName": "Pix", "Value": 90.0, "NumberOfInstallments": 1},
                ],
            }
        }
        prices = self._utils()._extract_prices_from_seller(seller)
        assert prices["pix_price"] == 90.0

    def test_credit_card_single_installment(self):
        seller = {
            "commertialOffer": {
                "Price": 100.0,
                "Installments": [
                    {"PaymentSystemName": "Visa", "Value": 100.0, "NumberOfInstallments": 1},
                    {"PaymentSystemName": "Visa", "Value": 55.0, "NumberOfInstallments": 2},
                ],
            }
        }
        prices = self._utils()._extract_prices_from_seller(seller)
        assert prices["credit_card_price"] == 100.0

    def test_empty_seller_data(self):
        prices = self._utils()._extract_prices_from_seller({})
        assert prices["price"] is None
        assert prices["pix_price"] is None


# ---------------------------------------------------------------------------
# _extract_variations
# ---------------------------------------------------------------------------
class TestExtractVariations:
    def _utils(self):
        return Utils()

    def test_basic_extraction(self):
        items = [
            {
                "itemId": "10",
                "nameComplete": "SKU 10",
                "variations": [{"name": "Size", "values": ["M"]}],
                "images": [{"imageUrl": "https://img.com/10.jpg"}],
                "sellers": [
                    {
                        "sellerId": "1",
                        "sellerDefault": True,
                        "commertialOffer": {
                            "Price": 50.0,
                            "AvailableQuantity": 5,
                            "Installments": [],
                        },
                    }
                ],
            }
        ]
        result = self._utils()._extract_variations(items)
        assert len(result) == 1
        assert result[0]["sku_id"] == "10"
        assert result[0]["sku_name"] == "SKU 10"
        assert result[0]["sellerId"] == "1"

    def test_skips_items_without_sku_id(self):
        items = [{"nameComplete": "NoId", "variations": [], "images": [], "sellers": []}]
        result = self._utils()._extract_variations(items)
        assert result == []

    def test_no_sellers(self):
        items = [
            {
                "itemId": "10",
                "nameComplete": "SKU 10",
                "variations": [],
                "images": [],
                "sellers": [],
            }
        ]
        result = self._utils()._extract_variations(items)
        assert len(result) == 1
        assert result[0]["price"] is None
        assert result[0]["sellerId"] is None


# ---------------------------------------------------------------------------
# _clean_image_url
# ---------------------------------------------------------------------------
class TestCleanImageUrl:
    def _utils(self):
        return Utils()

    def test_removes_query_params(self):
        url = "https://img.com/photo.jpg?v=123&w=500"
        assert self._utils()._clean_image_url(url) == "https://img.com/photo.jpg"

    def test_removes_fragment(self):
        url = "https://img.com/photo.jpg#section"
        assert self._utils()._clean_image_url(url) == "https://img.com/photo.jpg"

    def test_removes_both(self):
        url = "https://img.com/photo.jpg?v=1#top"
        assert self._utils()._clean_image_url(url) == "https://img.com/photo.jpg"

    def test_clean_url_unchanged(self):
        url = "https://img.com/photo.jpg"
        assert self._utils()._clean_image_url(url) == url

    def test_empty_string(self):
        assert self._utils()._clean_image_url("") == ""

    def test_none_input(self):
        assert self._utils()._clean_image_url(None) == ""


# ---------------------------------------------------------------------------
# _get_first_image / _get_product_image
# ---------------------------------------------------------------------------
class TestImageHelpers:
    def _utils(self):
        return Utils()

    def test_get_first_image_returns_clean_url(self):
        images = [{"imageUrl": "https://img.com/a.jpg?v=1"}]
        assert self._utils()._get_first_image(images) == "https://img.com/a.jpg"

    def test_get_first_image_skips_empty_urls(self):
        images = [{"imageUrl": ""}, {"imageUrl": "https://img.com/b.jpg"}]
        assert self._utils()._get_first_image(images) == "https://img.com/b.jpg"

    def test_get_first_image_empty_list(self):
        assert self._utils()._get_first_image([]) == ""

    def test_get_first_image_none(self):
        assert self._utils()._get_first_image(None) == ""

    def test_get_product_image(self):
        product = {"items": [{"images": [{"imageUrl": "https://img.com/p.jpg"}]}]}
        assert self._utils()._get_product_image(product) == "https://img.com/p.jpg"

    def test_get_product_image_empty_product(self):
        assert self._utils()._get_product_image({}) == ""
        assert self._utils()._get_product_image(None) == ""

    def test_get_product_image_no_items(self):
        assert self._utils()._get_product_image({"items": []}) == ""

    def test_get_product_image_non_dict_item(self):
        assert self._utils()._get_product_image({"items": ["not a dict"]}) == ""


# ---------------------------------------------------------------------------
# _truncate_description
# ---------------------------------------------------------------------------
class TestTruncateDescription:
    def _utils(self):
        return Utils()

    def test_short_description_unchanged(self):
        assert self._utils()._truncate_description("Short text") == "Short text"

    def test_long_description_truncated(self):
        long_text = "A" * 250
        result = self._utils()._truncate_description(long_text)
        assert len(result) == 203  # 200 + "..."
        assert result.endswith("...")

    def test_exact_limit(self):
        text = "B" * 200
        assert self._utils()._truncate_description(text) == text

    def test_custom_max_length(self):
        result = self._utils()._truncate_description("Hello World", max_length=5)
        assert result == "Hello..."


# ---------------------------------------------------------------------------
# _get_nested_value
# ---------------------------------------------------------------------------
class TestGetNestedValue:
    def test_simple_key(self):
        assert Utils._get_nested_value({"a": 1}, "a") == 1

    def test_dot_path(self):
        data = {"a": {"b": {"c": 42}}}
        assert Utils._get_nested_value(data, "a.b.c") == 42

    def test_list_index(self):
        data = {"items": [{"id": "first"}, {"id": "second"}]}
        assert Utils._get_nested_value(data, "items.1.id") == "second"

    def test_missing_key_returns_none(self):
        assert Utils._get_nested_value({"a": 1}, "b") is None

    def test_invalid_index_returns_none(self):
        data = {"items": [{"id": 1}]}
        assert Utils._get_nested_value(data, "items.99.id") is None

    def test_non_numeric_index_on_list_returns_none(self):
        data = {"items": [1, 2, 3]}
        assert Utils._get_nested_value(data, "items.abc") is None

    def test_path_through_non_dict_non_list_returns_none(self):
        data = {"a": "string_value"}
        assert Utils._get_nested_value(data, "a.b") is None


# ---------------------------------------------------------------------------
# _format_name_value_pairs / _format_variations
# ---------------------------------------------------------------------------
class TestFormatHelpers:
    def _utils(self):
        return Utils()

    def test_format_name_value_pairs(self):
        items = [
            {"name": "Color", "values": ["Red"]},
            {"name": "Size", "values": ["M"]},
        ]
        result = self._utils()._format_name_value_pairs(items)
        assert result == "{Color: Red, Size: M}"

    def test_format_name_value_pairs_empty(self):
        assert self._utils()._format_name_value_pairs([]) == "{{}}"

    def test_format_name_value_pairs_skips_incomplete(self):
        items = [
            {"name": "Color", "values": ["Red"]},
            {"name": "", "values": ["X"]},
            {"name": "Size", "values": []},
        ]
        result = self._utils()._format_name_value_pairs(items)
        assert result == "{Color: Red}"

    def test_format_variations_delegates(self):
        items = [{"name": "Color", "values": ["Blue"]}]
        result = self._utils()._format_variations(items)
        assert result == "{Color: Blue}"

    def test_format_variations_with_remove_specifications(self):
        items = [
            {"name": "Color", "values": ["Blue"]},
            {"name": "VALOR_HEX_ORIGINAL", "values": ["#30B349"]},
            {"name": "Size", "values": ["M"]},
        ]
        result = self._utils()._format_variations(
            items, remove_specifications=["VALOR_HEX_ORIGINAL"]
        )
        assert "Color" in result
        assert "Size" in result
        assert "VALOR_HEX_ORIGINAL" not in result


# ---------------------------------------------------------------------------
# _format_specifications
# ---------------------------------------------------------------------------
class TestFormatSpecifications:
    def _utils(self):
        return Utils()

    def test_all_specifications_group(self):
        groups = [
            {
                "name": "allSpecifications",
                "specifications": [
                    {"name": "Material", "values": ["Cotton"]},
                    {"name": "Weight", "values": ["200g"]},
                ],
            }
        ]
        result = self._utils()._format_specifications(groups)
        assert len(result) == 1
        assert result[0]["name"] == "allSpecifications"
        assert "Material" in result[0]["specifications"]
        assert "Weight" in result[0]["specifications"]

    def test_fallback_to_first_groups(self):
        groups = [
            {
                "name": "Group1",
                "specifications": [{"name": "Attr1", "values": ["V1"]}],
            },
            {
                "name": "Group2",
                "specifications": [{"name": "Attr2", "values": ["V2"]}],
            },
        ]
        result = self._utils()._format_specifications(groups)
        assert len(result) == 2
        assert result[0]["name"] == "Group1"

    def test_max_groups_limit(self):
        groups = [
            {"name": f"G{i}", "specifications": [{"name": f"A{i}", "values": [f"V{i}"]}]}
            for i in range(10)
        ]
        result = self._utils()._format_specifications(groups, max_groups=2)
        assert len(result) == 2

    def test_remove_specifications(self):
        groups = [
            {
                "name": "allSpecifications",
                "specifications": [
                    {"name": "sellerId", "values": ["1"]},
                    {"name": "color", "values": ["blue"]},
                ],
            }
        ]
        result = self._utils()._format_specifications(groups, remove_specifications=["sellerId"])
        assert "sellerId" not in result[0]["specifications"]
        assert "color" in result[0]["specifications"]

    def test_empty_groups(self):
        assert self._utils()._format_specifications([]) == []

    def test_group_without_specifications_skipped(self):
        groups = [{"name": "Empty", "specifications": []}]
        result = self._utils()._format_specifications(groups)
        assert result == []
