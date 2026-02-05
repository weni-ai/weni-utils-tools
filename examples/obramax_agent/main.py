"""
Exemplo: Agente Obramax Refatorado

Este arquivo mostra como o agente de 900+ linhas se torna ~50 linhas.

ANTES: 938 linhas de código com lógica duplicada
DEPOIS: ~50 linhas importando da biblioteca

Plugins utilizados:
- Regionalization: Para busca por CEP
- WeniFlowTrigger: Para disparar fluxos de tracking
"""

from weni import Tool
from weni.context import Context
from weni.responses import TextResponse

# Importa da biblioteca centralizada
from weni_utils.tools import ProductConcierge
from weni_utils.tools.plugins import Regionalization, WeniFlowTrigger


class SearchProduct(Tool):
    """
    Tool de busca de produtos para Obramax.
    
    Agora utiliza a biblioteca weni-vtex-concierge, reduzindo
    drasticamente a quantidade de código e facilitando manutenção.
    """
    
    def execute(self, context: Context) -> TextResponse:
        # Extrai parâmetros
        product_name = context.parameters.get("product_name", "")
        brand_name = context.parameters.get("brand_name", "")
        postal_code = context.parameters.get("postal_code", "")
        delivery_type = context.parameters.get("deliverytype", "")
        quantity = context.parameters.get("quantity", "1")
        
        # Extrai credenciais
        base_url = context.credentials.get("BASE_URL", "")
        store_url = context.credentials.get("STORE_URL", "")
        vtex_app_key = context.credentials.get("VTEX_API_APPKEY", "")
        vtex_app_token = context.credentials.get("VTEX_API_APPTOKEN", "")
        
        if not base_url:
            return TextResponse(data={"error": "BASE_URL not configured"})
        
        # Configura os plugins específicos do Varejo
        regionalization = Regionalization(
            seller_rules={
                "region_a_sellers": ["store_1", "store_2", "store_3"],
                "pickup_sellers": ["store_1", "store_2"],
                "delivery_sellers": ["store_1", "store_3"],
            },
            priority_categories=[
                "/Floors/Ceramics/",
                "/Floors/Porcelain/",
                "/Floors/Coatings/"
            ],
            require_delivery_type_for_priority=True
        )
        
        flow_trigger = WeniFlowTrigger(
            flow_uuid=context.credentials.get("EVENT_ID_CONCIERGE"),
            trigger_once=True
        )
        
        # Cria o concierge com os plugins
        concierge = ProductConcierge(
            base_url=base_url,
            store_url=store_url,
            vtex_app_key=vtex_app_key,
            vtex_app_token=vtex_app_token,
            plugins=[regionalization, flow_trigger],
            max_products=20,
            max_variations=5,
            max_payload_kb=20,
            priority_categories=[
                "/Pisos e Revestimentos/Pisos Cerâmicos/",
                "/Pisos e Revestimentos/Porcelanatos/",
                "/Pisos e Revestimentos/Revestimentos Cerâmicos/"
            ]
        )
        
        # Executa a busca - TODA a lógica está na biblioteca
        result = concierge.search(
            product_name=product_name,
            brand_name=brand_name,
            postal_code=postal_code,
            quantity=int(quantity) if quantity else 1,
            delivery_type=delivery_type,
            credentials={
                "API_TOKEN_WENI": context.credentials.get("API_TOKEN_WENI"),
                "EVENT_ID_CONCIERGE": context.credentials.get("EVENT_ID_CONCIERGE"),
            },
            contact_info={
                "urn": context.contact.get("urn", ""),
            }
        )
        
        return TextResponse(data=result)


# ============================================================================
# COMPARAÇÃO: ANTES vs DEPOIS
# ============================================================================
#
# ANTES (938 linhas):
# - isPriorityCategory()
# - getRegionId()
# - getSkuDetails()
# - getFixedPrice()
# - addFixedPriceToProducts()
# - addSkuDetailsToProducts()
# - intelligentSearch()
# - filterProductsWithStock()
# - selectProducts()
# - batchSimulation()
# - tryAlternativeSimulation()
# - cartSimulation()
# - trigger_weni_flow()
# - execute()
#
# DEPOIS (50 linhas):
# - execute() que usa ProductConcierge com plugins
#
# BENEFÍCIOS:
# 1. Bug no core? Corrige na lib, todos os clientes atualizados
# 2. Novo cliente? Copia este arquivo e ajusta plugins
# 3. Nova feature? Adiciona plugin na lib
# 4. Testes? Centralizados na lib
# ============================================================================
