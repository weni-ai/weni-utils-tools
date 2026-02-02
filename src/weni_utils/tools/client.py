"""
VTEXClient - Cliente para APIs da VTEX

Este módulo contém toda a lógica de comunicação com as APIs da VTEX,
extraída e consolidada dos agentes existentes.
"""

import json
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import requests


@dataclass
class ProductVariation:
    """Representa uma variação (SKU) de um produto"""

    sku_id: str
    sku_name: str
    variations: str  # Formato: "[Cor: Branco, Tamanho: M]"
    price: Optional[float] = None
    spot_price: Optional[float] = None
    list_price: Optional[float] = None
    pix_price: Optional[float] = None
    credit_card_price: Optional[float] = None
    image_url: str = ""
    seller_id: Optional[str] = None
    available_quantity: int = 0


@dataclass
class Product:
    """Representa um produto com suas variações"""

    name: str
    description: str
    brand: str
    product_link: str
    image_url: str
    categories: List[str]
    specification_groups: List[Dict]
    variations: List[ProductVariation]


class VTEXClient:
    """
    Cliente para comunicação com APIs da VTEX.

    Centraliza todas as chamadas de API para:
    - Intelligent Search (busca de produtos)
    - Cart Simulation (verificação de estoque)
    - Regions (regionalização)
    - SKU Details (detalhes do produto)

    Example:
        client = VTEXClient(
            base_url="https://loja.vtexcommercestable.com.br",
            store_url="https://loja.com.br"
        )

        products = client.intelligent_search("furadeira")
    """

    def __init__(
        self,
        base_url: str,
        store_url: str,
        vtex_app_key: Optional[str] = None,
        vtex_app_token: Optional[str] = None,
        timeout: int = 30,
    ):
        """
        Inicializa o cliente VTEX.

        Args:
            base_url: URL base da API VTEX (ex: https://loja.vtexcommercestable.com.br)
            store_url: URL da loja (ex: https://loja.com.br)
            vtex_app_key: App Key para APIs autenticadas (opcional)
            vtex_app_token: App Token para APIs autenticadas (opcional)
            timeout: Timeout para requisições em segundos
        """
        self.base_url = base_url.rstrip("/")
        self.store_url = store_url.rstrip("/")
        if not self._validate_base_url_and_store_url():
            raise ValueError("Base URL or store URL is invalid")

        self.vtex_app_key = vtex_app_key
        self.vtex_app_token = vtex_app_token
        self.timeout = timeout

    def _get_auth_headers(self) -> Dict[str, str]:
        """Retorna headers de autenticação se disponíveis"""
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        if self.vtex_app_key and self.vtex_app_token:
            headers["X-VTEX-API-AppKey"] = self.vtex_app_key
            headers["X-VTEX-API-AppToken"] = self.vtex_app_token

        return headers

    def _validate_base_url_and_store_url(self) -> bool:
        """Validate if the base URL and store URL are valid"""
        if not self.base_url or not self.store_url:
            return False
        
        if not self.base_url.startswith("https://") or not self.store_url.startswith("https://"):
            return False

        if not self.base_url.endswith((".vtexcommercestable.com.br", "myvtex.com")):
            return False
        
        return True

    def _clean_image_url(self, img_url: str) -> str:
        """Remove query parameters da URL da imagem"""
        if not img_url:
            return ""

        # Remove query parameters
        if "?" in img_url:
            img_url = img_url.split("?")[0]

        # Remove fragment identifier
        if "#" in img_url:
            img_url = img_url.split("#")[0]

        return img_url

    def _format_variations(self, variation_items: List[Dict]) -> str:
        """
        Converte variações para formato compacto.

        Args:
            variation_items: Lista de variações do item

        Returns:
            String no formato "[Cor: Branco, Tamanho: M]"
        """
        compact_variations = []
        for var in variation_items:
            name = var.get("name", "")
            values = var.get("values", [])
            if name and values:
                value = values[0] if values else ""
                compact_variations.append(f"{name}: {value}")

        return f"[{', '.join(compact_variations)}]" if compact_variations else "[]"

    def _format_specifications(self, spec_groups: List[Dict], max_groups: int = 3) -> List[Dict]:
        """
        Formata grupos de especificações de forma simplificada.

        Args:
            spec_groups: Grupos de especificação do produto
            max_groups: Número máximo de grupos a incluir

        Returns:
            Lista simplificada de especificações
        """
        simplified_specs = []

        # Procura primeiro pelo grupo "allSpecifications"
        all_specs_group = None
        for group in spec_groups:
            if group.get("name") == "allSpecifications" and group.get("specifications"):
                all_specs_group = group
                break

        if all_specs_group:
            specs = all_specs_group["specifications"]
            compact_specs = []
            for spec in specs:
                name = spec.get("name", "")
                values = spec.get("values", [])
                if name and values:
                    value = values[0] if values else ""
                    compact_specs.append(f"{name}: {value}")

            simplified_specs.append(
                {
                    "name": "allSpecifications",
                    "specifications": f"[{', '.join(compact_specs)}]" if compact_specs else "[]",
                }
            )
        else:
            # Fallback: usa os primeiros grupos
            for group in spec_groups[:max_groups]:
                if group.get("specifications"):
                    limited_specs = group["specifications"][:5]
                    compact_specs = []
                    for spec in limited_specs:
                        name = spec.get("name", "")
                        values = spec.get("values", [])
                        if name and values:
                            value = values[0] if values else ""
                            compact_specs.append(f"{name}: {value}")

                    simplified_specs.append(
                        {
                            "name": group.get("name", ""),
                            "specifications": (
                                f"[{', '.join(compact_specs)}]" if compact_specs else "[]"
                            ),
                        }
                    )

        return simplified_specs

    def _extract_prices_from_seller(self, seller_data: Dict) -> Dict[str, Optional[float]]:
        """
        Extrai preços de um seller, incluindo PIX e cartão.

        Args:
            seller_data: Dados do seller

        Returns:
            Dicionário com preços extraídos
        """
        commercial_offer = seller_data.get("commertialOffer", {})
        installments = commercial_offer.get("Installments", [])

        prices = {
            "price": commercial_offer.get("Price"),
            "spot_price": commercial_offer.get("spotPrice"),
            "list_price": commercial_offer.get("ListPrice"),
            "pix_price": None,
            "credit_card_price": None,
        }

        # Busca preço do PIX
        for installment in installments:
            if installment.get("PaymentSystemName") == "Pix":
                prices["pix_price"] = installment.get("Value")
                break

        # Busca preço do cartão de crédito à vista
        for installment in installments:
            if (
                installment.get("PaymentSystemName") == "Visa"
                and installment.get("NumberOfInstallments") == 1
            ):
                prices["credit_card_price"] = installment.get("Value")
                break

        return prices

    def _select_best_seller(self, sellers: List[Dict]) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Seleciona o melhor seller para um item.

        Prioridade:
        1. Seller padrão com estoque
        2. Primeiro seller com estoque
        3. Primeiro seller disponível

        Args:
            sellers: Lista de sellers do item

        Returns:
            Tuple (seller_data, seller_id)
        """
        if not sellers:
            return None, None

        # Tenta seller padrão com estoque
        for seller in sellers:
            if (
                seller.get("sellerDefault", False)
                and seller.get("commertialOffer", {}).get("AvailableQuantity", 0) > 0
            ):
                return seller, seller.get("sellerId")

        # Tenta primeiro com estoque
        for seller in sellers:
            if seller.get("commertialOffer", {}).get("AvailableQuantity", 0) > 0:
                return seller, seller.get("sellerId")

        # Fallback: primeiro disponível
        return sellers[0], sellers[0].get("sellerId")

    def intelligent_search(
        self,
        product_name: str,
        brand_name: str = "",
        region_id: Optional[str] = None,
        hide_unavailable: bool = True,
        trade_policy_id: Optional[int] = None,
        cluster_id: Optional[int] = None,
        allow_redirect: bool = False,
    ) -> List[Dict]:
        """
        Busca produtos usando a API Intelligent Search da VTEX.
        
        Retorna apenas os dados brutos da API, sem processamento.
        A lógica de formatação, filtragem e limitação deve ser feita pelo agente.

        Args:
            product_name: Nome do produto a buscar
            brand_name: Marca do produto (opcional)
            region_id: ID da região para regionalização (opcional)
            hide_unavailable: Se deve ocultar produtos indisponíveis
            trade_policy_id: Trade policy / sales channel ID (opcional)
            cluster_id: Filter by collection ID (opcional)
            allow_redirect: Se deve permitir redirecionamentos (opcional)

        Returns:
            Lista de produtos brutos da API VTEX
        """
        # Constrói a URL com ou sem regionalização
        query = f"{product_name} {brand_name}".strip()

        # Build path segments
        path_segments = []
        if trade_policy_id:
            path_segments.append(f"trade-policy/{trade_policy_id}")
        if region_id:
            path_segments.append(f"region-id/{region_id}")
        if cluster_id:
            path_segments.append(f"productClusterIds/{cluster_id}")

        path = "/".join(path_segments)
        if path:
            path = f"{path}/"

        search_url = (
            f"{self.base_url}/api/io/_v/api/intelligent-search/product_search/{path}"
            f"?query={query}&simulationBehavior=default"
            f"&hideUnavailableItems={str(hide_unavailable).lower()}"
            f"&allowRedirect={str(allow_redirect).lower()}"
        )

        try:
            response = requests.get(search_url, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            return data.get("products", [])

        except requests.exceptions.RequestException as e:
            print(f"ERROR: Erro na busca inteligente: {e}")
            return []
        except json.JSONDecodeError as e:
            print(f"ERROR: Erro ao processar JSON: {e}")
            return []

    def cart_simulation(
        self, items: List[Dict], country: str = "BRA", postal_code: Optional[str] = None
    ) -> Dict:
        """
        Realiza simulação de carrinho para verificar disponibilidade.

        Args:
            items: Lista de itens [{id, quantity, seller}]
            country: Código do país
            postal_code: CEP (opcional)

        Returns:
            Resposta da simulação
        """
        url = f"{self.base_url}/api/checkout/pub/orderForms/simulation"

        payload = {"items": items, "country": country}

        if postal_code:
            payload["postalCode"] = postal_code

        try:
            response = requests.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            print(f"ERROR: Erro na simulação de carrinho: {e}")
            return {"items": []}

    def batch_simulation(
        self,
        sku_id: str,
        quantity: int,
        sellers: List[str],
        postal_code: str,
        max_quantity_per_seller: int = 8000,
        max_total_quantity: int = 24000,
    ) -> Optional[Dict]:
        """
        Simula um SKU específico com múltiplos sellers (usado para regionalização).

        Args:
            sku_id: ID do SKU
            quantity: Quantidade desejada
            sellers: Lista de sellers
            postal_code: CEP
            max_quantity_per_seller: Quantidade máxima por seller
            max_total_quantity: Quantidade máxima total

        Returns:
            Melhor resultado da simulação ou None
        """
        quantity = int(quantity)

        # Calcula quantidade por seller
        if len(sellers) > 1:
            total_quantity = min(quantity * len(sellers), max_total_quantity)
            quantity_per_seller = min(total_quantity // len(sellers), max_quantity_per_seller)
        else:
            quantity_per_seller = min(quantity, max_quantity_per_seller)

        items = [
            {"id": sku_id, "quantity": quantity_per_seller, "seller": seller} for seller in sellers
        ]

        url = f"{self.base_url}/_v/api/simulations-batches?sc=1&RnbBehavior=1"
        payload = {"items": items, "country": "BRA", "postalCode": postal_code}

        try:
            response = requests.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            simulation_data = response.json()

            data_content = simulation_data.get("data", {})
            if not data_content:
                return None

            sku_simulations = data_content.get(sku_id, [])
            if not sku_simulations:
                return None

            # Retorna a simulação com maior quantidade
            return max(sku_simulations, key=lambda x: x.get("quantity", 0))

        except requests.exceptions.RequestException as e:
            print(f"ERROR: Erro na simulação batch: {e}")
            return None

    def get_region(
        self, postal_code: str, trade_policy: int, country_code: str
    ) -> Tuple[Optional[str], Optional[str], List[str]]:
        """
        Consulta a API de regionalização para obter região e sellers.

        Args:
            postal_code: CEP

        Returns:
            Tuple (region_id, error_message, sellers)
        """
        region_url = f"{self.base_url}/api/checkout/pub/regions?country={country_code}&postalCode={postal_code}&sc={trade_policy}"

        try:
            response = requests.get(region_url, timeout=self.timeout)
            response.raise_for_status()
            regions_data = response.json()

            if not regions_data:
                return (
                    None,
                    "Não atendemos a sua região. Compre presencialmente em nossas lojas.",
                    [],
                )

            region = regions_data[0]
            sellers = region.get("sellers", [])

            if not sellers:
                return (
                    None,
                    "Não atendemos a sua região. Compre presencialmente em nossas lojas.",
                    [],
                )

            region_id = region.get("id")
            seller_ids = [seller.get("id") for seller in sellers]

            return region_id, None, seller_ids

        except requests.exceptions.RequestException as e:
            print(f"ERROR: Erro na regionalização: {e}")
            return None, f"Erro ao consultar regionalização: {e}", []

    def get_sku_details(self, sku_id: str) -> Dict:
        """
        Busca detalhes de um SKU (dimensões, peso, etc).
        Requer credenciais VTEX.

        Args:
            sku_id: ID do SKU

        Returns:
            Dicionário com detalhes do SKU
        """
        default_response = {
            "PackagedHeight": None,
            "PackagedLength": None,
            "PackagedWidth": None,
            "PackagedWeightKg": None,
            "Height": None,
            "Length": None,
            "Width": None,
            "WeightKg": None,
            "CubicWeight": None,
        }

        if not self.vtex_app_key or not self.vtex_app_token:
            return default_response

        url = f"{self.base_url}/api/catalog/pvt/stockkeepingunit/{sku_id}"

        try:
            response = requests.get(url, headers=self._get_auth_headers(), timeout=self.timeout)

            if response.status_code != 200:
                return default_response

            data = response.json()

            return {
                "PackagedHeight": data.get("PackagedHeight"),
                "PackagedLength": data.get("PackagedLength"),
                "PackagedWidth": data.get("PackagedWidth"),
                "PackagedWeightKg": data.get("PackagedWeightKg"),
                "Height": data.get("Height"),
                "Length": data.get("Length"),
                "Width": data.get("Width"),
                "WeightKg": data.get("WeightKg"),
                "CubicWeight": data.get("CubicWeight"),
            }

        except Exception:
            return default_response

    def get_product_by_sku(self, sku_id: str) -> Optional[Dict]:
        """
        Busca um produto específico pelo SKU ID.

        Args:
            sku_id: ID do SKU

        Returns:
            Dados do produto ou None
        """
        search_url = f"{self.base_url}/api/io/_v/api/intelligent-search/product_search/?query=sku.id:{sku_id}"

        try:
            response = requests.get(search_url, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()

            products = data.get("products", [])
            if not products:
                return None

            return products[0]

        except Exception as e:
            print(f"ERROR: Erro ao buscar SKU {sku_id}: {e}")
            return None

    def get_orders_by_document(self, document: str) -> Dict:
        """
        Busca pedidos por documento.

        Args:
            document: Documento do cliente

        Returns:
            Dicionário com lista de pedidos
        """
        if not document:
            return {"list": []}

        # Busca pedidos completos
        url = f"{self.base_url}/api/oms/pvt/orders?q={document}"

        try:
            response = requests.get(url, headers=self._get_auth_headers(), timeout=self.timeout)
            response.raise_for_status()
            orders_data = response.json()
        except requests.exceptions.RequestException as e:
            print(f"ERROR: Erro ao buscar pedidos: {e}")
            orders_data = {"list": []}

        # Busca pedidos incompletos
        url_incomplete = f"{self.base_url}/api/oms/pvt/orders?q={document}&incompleteOrders=true"

        try:
            response_incomplete = requests.get(
                url_incomplete, headers=self._get_auth_headers(), timeout=self.timeout
            )
            response_incomplete.raise_for_status()
            orders_data_incomplete = response_incomplete.json()

            if orders_data_incomplete and "list" in orders_data_incomplete:
                if "list" not in orders_data:
                    orders_data["list"] = []
                orders_data["list"].extend(orders_data_incomplete["list"])

        except requests.exceptions.RequestException as e:
            print(f"ERROR: Erro ao buscar pedidos incompletos: {e}")

        return orders_data

    def get_order_by_id(self, order_id: str) -> Optional[Dict]:
        """
        Busca pedido por ID.

        Args:
            order_id: ID do pedido

        Returns:
            Dicionário com dados do pedido ou None
        """
        if not order_id:
            return None

        url = f"{self.base_url}/api/oms/pvt/orders/{order_id}"

        try:
            response = requests.get(url, headers=self._get_auth_headers(), timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"ERROR: Erro ao buscar pedido {order_id}: {e}")
            return None

    def process_products(
        self,
        raw_products: List[Dict],
        max_products: int = 20,
        max_variations: int = 5,
        utm_source: Optional[str] = "weni_concierge",
        extra_product_fields: Optional[List] = None,
    ) -> Dict[str, Dict]:
        """
        Process raw products from the VTEX API.

        Formats, filters, and limits products and their variations.

        Args:
            raw_products: List of raw products from the VTEX API
            max_products: Maximum number of products to return
            max_variations: Maximum variations per product
            utm_source: UTM source for product links
            extra_product_fields: Extra fields to include in the result.
                Can be a string or tuple (path, alias).
                Examples: ["clusterHighlights"], [("items.0.images", "images")]

        Returns:
            Dictionary with structured products {product_name: data}
        """
        products_structured: Dict[str, Dict] = {}
        product_count = 0

        for product in raw_products:
            if product_count >= max_products:
                break

            if not product.get("items"):
                continue

            product_name = product.get("productName", "")

            # Process variations (SKUs)
            variations = self._extract_variations(product.get("items", []))
            if not variations:
                continue

            # Limit variations per product
            limited_variations = variations[:max_variations]

            # Build product link
            product_link = f"{self.store_url}{product.get('link', '')}"
            if utm_source:
                product_link += f"?utm_source={utm_source}"

            # Build product data
            product_data = {
                "variations": limited_variations,
                "description": self._truncate_description(product.get("description", "")),
                "brand": product.get("brand", ""),
                "specification_groups": self._format_specifications(
                    product.get("specificationGroups", [])
                ),
                "productLink": product_link,
                "imageUrl": self._get_product_image(product),
                "categories": product.get("categories", []),
            }

            # Add extra product fields if specified
            if extra_product_fields:
                self._add_extra_fields(product_data, product, extra_product_fields)

            products_structured[product_name] = product_data
            product_count += 1

        return products_structured

    def _extract_variations(self, items: List[Dict]) -> List[Dict]:
        """Extract and format variations from product items."""
        variations = []

        for item in items:
            sku_id = item.get("itemId")
            if not sku_id:
                continue

            seller_data, seller_id = self._select_best_seller(item.get("sellers", []))
            prices = self._extract_prices_from_seller(seller_data) if seller_data else {}

            variations.append({
                "sku_id": sku_id,
                "sku_name": item.get("nameComplete"),
                "variations": self._format_variations(item.get("variations", [])),
                "price": prices.get("price"),
                "spotPrice": prices.get("spot_price"),
                "listPrice": prices.get("list_price"),
                "pixPrice": prices.get("pix_price"),
                "creditCardPrice": prices.get("credit_card_price"),
                "imageUrl": self._get_first_image(item.get("images", [])),
                "sellerId": seller_id,
            })

        return variations

    def _get_first_image(self, images: List[Dict]) -> str:
        """Get the first valid image URL from a list of images."""
        if not images or not isinstance(images, list):
            return ""

        for img in images:
            img_url = img.get("imageUrl", "")
            if img_url:
                return self._clean_image_url(img_url)

        return ""

    def _get_product_image(self, product: Dict) -> str:
        """Get the main product image from the first item."""
        items = product.get("items", [])
        if not items:
            return ""

        first_item = items[0]
        return self._get_first_image(first_item.get("images", []))

    def _truncate_description(self, description: str, max_length: int = 200) -> str:
        """Truncate description if too long."""
        if len(description) > max_length:
            return description[:max_length] + "..."
        return description

    def _add_extra_fields(
        self,
        product_data: Dict,
        product: Dict,
        extra_fields: List,
    ) -> None:
        """Add extra fields to product data."""
        for field in extra_fields:
            if isinstance(field, tuple):
                path, alias = field
            else:
                path = field
                alias = path.split(".")[-1]

            product_data[alias] = self._get_nested_value(product, path)

    @staticmethod
    def _get_nested_value(data: Dict, path: str):
        """
        Get a nested value from a dictionary using dot notation.

        Args:
            data: Source dictionary
            path: Path in format "key1.key2.0.key3"

        Returns:
            Value found or None if not exists
        """
        current = data

        for part in path.split("."):
            if isinstance(current, list):
                try:
                    current = current[int(part)]
                except (ValueError, IndexError):
                    return None
            elif isinstance(current, dict):
                current = current.get(part)
                if current is None:
                    return None
            else:
                return None

        return current