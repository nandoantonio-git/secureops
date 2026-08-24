# SecureOps Validation Fixtures

Baseline fixtures for the quickstart validation scenarios.

## Quickstart fixture map

- Python clean code: `python_clean/safe_request_handler.py`
- Python vulnerable code: `python_vulnerable/command_injection.py`
- Python critical unprotected data-flow case:
  `python_vulnerable/critical_unprotected_data_flow.py`
- US3 controlled critical-unprotected case:
  `python_vulnerable/controlled_critical_unprotected.py`
- US3 controlled clean-code case:
  `python_clean/controlled_clean_refund.py`
- Secondary-language clean code: `secondary_clean/safe_dom_update.js`
- Secondary-language deterministic vulnerable pattern:
  `secondary_vulnerable/dom_xss.js`
- Ollama unavailable/fallback behavior:
  `python_fallback/unsafe_yaml_load.py`

The secondary language for the MVP fixture set is JavaScript. Python fixtures
are the primary-language corpus and include both deterministic rule and
data-flow examples.
