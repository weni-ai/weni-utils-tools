# Weni Tools

Modular tools library for AI agents on the Weni platform.

## 📦 Installation

```bash
pip install weni-utils-tools
```

> **Note**: The package name on PyPI is `weni-utils-tools` (with hyphens), and you import it as `weni_utils.tools`:
> - Install: `pip install weni-utils-tools`
> - Import: `from weni_utils.tools import ...`

## 🎯 Problem Solved

Before this library, each client had a complete copy of the agent code, resulting in:
- ❌ Duplicated code (70%+ identical between clients)
- ❌ Bug fix = N manual deploys
- ❌ Exponential maintenance
- ❌ Difficult onboarding of new clients

## ✅ Solution

A centralized library with plugin system:
- ✅ Shared core (search, simulation, stock)
- ✅ Optional plugins (regionalization, carousel)
- ✅ Bug fix = 1 deploy, all updated
- ✅ New client = import and configure plugins

## 🚀 Basic Usage

### Modular Functions (Recommended)

```python
from weni_utils.tools import search_products, get_region, simulate_cart

# Search products
products = search_products(
    base_url_vtex="https://store.vtexcommercestable.com.br",
    product_name="drill",
    max_products=10
)

# Get region by postal code
region_id, error, sellers = get_region(
    base_url_vtex="https://store.vtexcommercestable.com.br",
    postal_code="01310-100"
)

# Simulate cart
result = simulate_cart(
    base_url_vtex="https://store.vtexcommercestable.com.br",
    items=[{"id": "61556", "quantity": 1, "seller": "1"}],
    postal_code="01310-100"
)
```

### Orchestration Class

```python
from weni_utils.tools import ProductConcierge

concierge = ProductConcierge(
    base_url_vtex="https://store.vtexcommercestable.com.br",
    store_url_vtex="https://store.com.br"
)

result = concierge.search(product_name="drill")
```

## 🔌 Available Plugins

### Regionalization
For clients with postal code-based regionalization.

```python
from weni_utils.tools import ProductConcierge
from weni_utils.tools.plugins import Regionalization

concierge = ProductConcierge(
    base_url_vtex="...",
    store_url_vtex="...",
    plugins=[
        Regionalization()
    ]
)

result = concierge.search(
    product_name="cement",
    postal_code="01310-100"
)
```

### Carousel
For sending products via WhatsApp carousel.

```python
from weni_utils.tools.plugins import Carousel

concierge = ProductConcierge(
    plugins=[
        Carousel(
            weni_token="your-token",
            max_items=10,
            auto_send=True
        )
    ]
)

result = concierge.search(
    product_name="shirt",
    contact_info={"urn": "whatsapp:5511999999999"}
)
```

### CAPI (Meta Conversions API)
For sending conversion events to Meta.

```python
from weni_utils.tools.plugins import CAPI

concierge = ProductConcierge(
    plugins=[
        CAPI(event_type="lead", auto_send=True)
    ]
)
```

### WeniFlowTrigger
For triggering Weni flows.

```python
from weni_utils.tools.plugins import WeniFlowTrigger

concierge = ProductConcierge(
    plugins=[
        WeniFlowTrigger(
            flow_uuid="flow-uuid",
            trigger_once=True
        )
    ]
)
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        ProductConcierge                              │
│                     (Orchestrates entire flow)                       │
└─────────────────────────────────────────────────────────────────────┘
                                 │
            ┌────────────────────┼────────────────────┐
            │                    │                    │
            ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   VTEXClient    │  │  StockManager   │  │    Plugins      │
│                 │  │                 │  │                 │
│ • search()      │  │ • check()       │  │ • before_search │
│ • simulate()    │  │ • filter()      │  │ • after_search  │
│ • get_region()  │  │ • limit_size()  │  │ • enrich()      │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

## 🔄 Execution Flow

1. **before_search** - Plugins modify context (e.g., get region_id)
2. **intelligent_search** - Search products in VTEX
3. **after_search** - Plugins filter/modify products
4. **check_availability** - Verify stock
6. **filter_products** - Filter only products with stock
7. **enrich_products** - Plugins add extra data
8. **finalize_result** - Plugins perform final actions (e.g., send events)

## 🤝 Creating a New Plugin

```python
from weni_utils.tools.plugins import PluginBase

class MyPlugin(PluginBase):
    name = "my_plugin"

    def before_search(self, context, client):
        # Modify context before search
        return context

    def after_search(self, products, context, client):
        # Modify products after search
        return products

    def after_stock_check(self, products_with_stock, context, client):
        # Enrich products after stock check
        return products_with_stock

    def finalize_result(self, result, context):
        # Final modification before return
        return result
```

## 📝 License

MIT License - Weni AI
