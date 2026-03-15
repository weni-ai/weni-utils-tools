# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.2] - 2026-03-14

### Fixed
- Fixed infinite recursion in `ProductConcierge.get_sku_details` (renamed to `get_sku_info`)
- Fixed `OrderConcierge._get_timezone` crash when `get_store_details()` returns `None`
- Fixed wrong attribute name `client.store_url` in `Carousel.send_carousel_for_skus`
- Fixed query string not URL-encoded in `intelligent_search`
- Fixed `list_orders` incomplete orders fetch passing wrong parameters
- Fixed weak domain validation in `_validate_base_url_and_store_url_vtex`
- Fixed `get_store_details` return type annotation (`Dict` → `Optional[Dict]`)
- Removed non-currency keys from `CURRENCY_KEYS`

### Changed
- Consolidated duplicate `process_products` / `_extract_variations` from `VTEXClient` into `Utils`
- Added `prefer_default_seller` parameter to `ProductConcierge.search()` for per-search flexibility
- Added `vtex_segment` support with automatic extraction from Weni `Context`
- Added strategic logging across all modules using Python `logging` library
- Replaced all `print()` statements with proper logger calls
- Improved PIX and credit card payment matching with case-insensitive substring checks
- Updated license format in `pyproject.toml` to SPDX standard
- Fixed package name to `weni-utils-tools` to match PyPI

## [0.0.1] - 2026-02-01

### Added
- Initial release of weni-tools-utils
- `ProductConcierge` - Main class for product search orchestration
- `VTEXClient` - VTEX API client with intelligent search, cart simulation, and regionalization
- `StockManager` - Stock availability verification and filtering
- `SearchContext` - Shared context for plugin communication

### Plugins
- `Regionalization` - Postal code-based region and seller selection
- `Carousel` - WhatsApp carousel message formatting and sending
- `CAPI` - Meta Conversions API integration
- `WeniFlowTrigger` - Weni flow triggering

### Documentation
- Complete README with usage examples
- Example implementations for agents
