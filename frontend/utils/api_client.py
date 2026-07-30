import os
import requests
import streamlit as st
from typing import Optional, Any, Dict

API_BASE_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000/api")


class APIClient:
    @staticmethod
    def get_headers() -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        token = st.session_state.get("token")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    @classmethod
    def get(cls, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Any]:
        url = f"{API_BASE_URL}{endpoint}"
        try:
            res = requests.get(url, headers=cls.get_headers(), params=params, timeout=10)
            if res.status_code == 401:
                st.session_state["authenticated"] = False
                st.session_state["token"] = None
                st.rerun()
            res.raise_for_status()
            return res.json()
        except Exception as e:
            print(f"API GET Error [{endpoint}]: {e}")
            return None

    @classmethod
    def post(cls, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Optional[Any]:
        url = f"{API_BASE_URL}{endpoint}"
        try:
            res = requests.post(url, headers=cls.get_headers(), json=data, timeout=10)
            if res.status_code == 401:
                st.session_state["authenticated"] = False
                st.session_state["token"] = None
                st.rerun()
            res.raise_for_status()
            return res.json()
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.content:
                try:
                    return {"error": e.response.json().get("detail", str(e))}
                except Exception:
                    pass
            return {"error": str(e)}
        except Exception as e:
            return {"error": str(e)}

    @classmethod
    def put(cls, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Optional[Any]:
        url = f"{API_BASE_URL}{endpoint}"
        try:
            res = requests.put(url, headers=cls.get_headers(), json=data, timeout=10)
            if res.status_code == 401:
                st.session_state["authenticated"] = False
                st.session_state["token"] = None
                st.rerun()
            res.raise_for_status()
            return res.json()
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.content:
                try:
                    return {"error": e.response.json().get("detail", str(e))}
                except Exception:
                    pass
            return {"error": str(e)}
        except Exception as e:
            return {"error": str(e)}

    @classmethod
    def delete(cls, endpoint: str) -> Optional[Any]:
        url = f"{API_BASE_URL}{endpoint}"
        try:
            res = requests.delete(url, headers=cls.get_headers(), timeout=10)
            if res.status_code == 401:
                st.session_state["authenticated"] = False
                st.session_state["token"] = None
                st.rerun()
            res.raise_for_status()
            return res.json()
        except Exception as e:
            print(f"API DELETE Error [{endpoint}]: {e}")
            return None
