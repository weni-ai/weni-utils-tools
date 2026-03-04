"""
Exemplo de Uso Modular - weni-tools-utils v1.1.0

Este exemplo mostra como usar as funções de forma independente,
chamando cada funcionalidade separadamente.
"""

import sys
import os

# Adiciona o path local da lib para teste
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from weni_utils.tools import (
    # Funções modulares
    search_products,
    search_product_by_sku,
    get_region,
    get_sellers_by_region,
    simulate_cart,
    check_stock_availability,
    get_product_price,
    send_capi_event,
    trigger_weni_flow,
    send_whatsapp_carousel,
)

# Configurações
BASE_URL = "https://www.obramax.com.br"
STORE_URL = "https://www.obramax.com.br"


def exemplo_busca_simples():
    """Exemplo 1: Busca de produtos básica"""
    print("\n" + "="*60)
    print("EXEMPLO 1: Busca Simples")
    print("="*60)
    
    # Busca com parâmetros customizados
    products = search_products(
        base_url=BASE_URL,
        product_name="furadeira",
        max_products=3,      # Limita a 3 produtos
        max_variations=2,    # Limita a 2 variações
        timeout=15           # Timeout de 15 segundos
    )
    
    print(f"\n✅ Encontrados {len(products)} produtos")
    for name, data in products.items():
        print(f"  - {name}: R$ {data['variations'][0].get('price', 'N/A')}")
    
    return products


def exemplo_busca_com_marca():
    """Exemplo 2: Busca com filtro de marca"""
    print("\n" + "="*60)
    print("EXEMPLO 2: Busca com Marca")
    print("="*60)
    
    products = search_products(
        base_url=BASE_URL,
        product_name="furadeira",
        brand_name="Bosch",   # Filtra por marca
        max_products=5
    )
    
    print(f"\n✅ Encontrados {len(products)} produtos Bosch")
    for name in products.keys():
        print(f"  - {name}")
    
    return products


def exemplo_regionalizacao():
    """Exemplo 3: Consulta de regionalização separada"""
    print("\n" + "="*60)
    print("EXEMPLO 3: Regionalização (CEP)")
    print("="*60)
    
    CEP = "01310-100"
    
    # Função separada para obter região
    region_id, error, sellers = get_region(
        base_url=BASE_URL,
        postal_code=CEP,
        country="BRA"
    )
    
    if error:
        print(f"\n⚠️ Erro: {error}")
    else:
        print(f"\n✅ Region ID: {region_id}")
        print(f"✅ Sellers disponíveis: {sellers}")
    
    # Ou use a versão simplificada
    sellers_only = get_sellers_by_region(BASE_URL, CEP)
    print(f"✅ Sellers (simplificado): {sellers_only}")
    
    return region_id, sellers


def exemplo_busca_regionalizada():
    """Exemplo 4: Busca com região (2 chamadas separadas)"""
    print("\n" + "="*60)
    print("EXEMPLO 4: Busca Regionalizada (composição)")
    print("="*60)
    
    CEP = "01310-100"
    
    # Passo 1: Obter região
    region_id, error, sellers = get_region(BASE_URL, CEP)
    
    if error:
        print(f"⚠️ {error}")
        return None
    
    print(f"1. Região obtida: {region_id}")
    
    # Passo 2: Buscar produtos com a região
    products = search_products(
        base_url=BASE_URL,
        product_name="cimento",
        region_id=region_id,  # Passa o region_id obtido
        max_products=3
    )
    
    print(f"2. Produtos encontrados: {len(products)}")
    
    return products


def exemplo_simulacao_carrinho():
    """Exemplo 5: Simulação de carrinho independente"""
    print("\n" + "="*60)
    print("EXEMPLO 5: Simulação de Carrinho")
    print("="*60)
    
    # Simula carrinho com itens específicos
    items = [
        {"id": "61556", "quantity": 1, "seller": "1"},
        {"id": "82598", "quantity": 2, "seller": "1"},
    ]
    
    result = simulate_cart(
        base_url=BASE_URL,
        items=items,
        country="BRA",
        postal_code="01310-100"  # Opcional
    )
    
    print("\n✅ Resultado da simulação:")
    for item in result.get("items", []):
        print(f"  - SKU {item.get('id')}: {item.get('availability', 'N/A')}")
    
    return result


def exemplo_verificar_estoque():
    """Exemplo 6: Verificar disponibilidade de múltiplos SKUs"""
    print("\n" + "="*60)
    print("EXEMPLO 6: Verificar Estoque (múltiplos SKUs)")
    print("="*60)
    
    sku_ids = ["61556", "82598", "40240"]
    
    availability = check_stock_availability(
        base_url=BASE_URL,
        sku_ids=sku_ids,
        quantity=1,      # Quantidade a verificar
        seller="1"       # Seller
    )
    
    print("\n✅ Disponibilidade:")
    for sku_id, disponivel in availability.items():
        status = "✅ Disponível" if disponivel else "❌ Indisponível"
        print(f"  - SKU {sku_id}: {status}")
    
    return availability


def exemplo_preco_produto():
    """Exemplo 7: Obter preço de produto"""
    print("\n" + "="*60)
    print("EXEMPLO 7: Preço do Produto")
    print("="*60)
    
    price_info = get_product_price(
        base_url=BASE_URL,
        sku_id="61556",
        seller_id="1",
        quantity=1
    )
    
    print(f"\n✅ Preço: R$ {price_info.get('price', 'N/A')}")
    print(f"✅ Preço original: R$ {price_info.get('list_price', 'N/A')}")
    
    return price_info


def exemplo_composicao_completa():
    """Exemplo 8: Composição completa (como um agente faria)"""
    print("\n" + "="*60)
    print("EXEMPLO 8: Composição Completa")
    print("="*60)
    
    CEP = "01310-100"
    PRODUTO = "cimento"
    
    print(f"\n🔍 Buscando '{PRODUTO}' para CEP {CEP}...")
    
    # 1. Obter região
    region_id, error, sellers = get_region(BASE_URL, CEP)
    print(f"1. Região: {region_id or error}")
    
    # 2. Buscar produtos
    products = search_products(
        base_url=BASE_URL,
        product_name=PRODUTO,
        region_id=region_id,
        max_products=5
    )
    print(f"2. Produtos encontrados: {len(products)}")
    
    # 3. Extrair SKUs para verificar estoque
    sku_ids = []
    for product_data in products.values():
        for variation in product_data.get("variations", []):
            sku_ids.append(variation.get("sku_id"))
    
    # 4. Verificar disponibilidade
    if sku_ids:
        availability = check_stock_availability(
            base_url=BASE_URL,
            sku_ids=sku_ids[:10],  # Limita a 10
            quantity=1
        )
        available_count = sum(1 for v in availability.values() if v)
        print(f"3. SKUs disponíveis: {available_count}/{len(availability)}")
    
    # 5. Retornar resultado
    print(f"\n✅ Busca completa!")
    return products


if __name__ == "__main__":
    print("\n" + "🚀"*30)
    print("   EXEMPLOS DE USO MODULAR")
    print("   weni-tools-utils v1.1.0")
    print("🚀"*30)
    
    # Execute os exemplos
    exemplo_busca_simples()
    exemplo_busca_com_marca()
    exemplo_regionalizacao()
    exemplo_busca_regionalizada()
    exemplo_simulacao_carrinho()
    exemplo_verificar_estoque()
    exemplo_preco_produto()
    exemplo_composicao_completa()
    
    print("\n" + "="*60)
    print("✅ TODOS OS EXEMPLOS CONCLUÍDOS!")
    print("="*60 + "\n")
