
import os

# 1) Try Streamlit secrets first (deployment)
try:
    import streamlit as st
    _secrets = st.secrets
except Exception:
    _secrets = {}

# 2) Fallback to .env locally (optional)
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

def _get(key: str, default=None):
    # st.secrets acts like a dict
    if _secrets and key in _secrets:
        return _secrets[key]
    return os.getenv(key, default)

OPENAI_API_KEY   = _get("OPENAI_API_KEY")
VECTOR_STORE_ID  = _get("VECTOR_STORE_ID")
SITE_PASSWORD    = _get("SITE_PASSWORD")  # optional if you want to read it here too
