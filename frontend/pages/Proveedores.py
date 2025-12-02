import streamlit as st
import requests
import pandas as pd
import os

st.set_page_config(page_title="Proveedores", page_icon="🏷️", layout="wide")

API_URL = os.getenv("API_GATEWAY_URL", "http://api-gateway:8000")

st.title("🏷️ Proveedores")
st.markdown("---")

@st.cache_data(ttl=30)
def fetch_proveedores():
    try:
        r = requests.get(f"{API_URL}/proveedores/proveedores", timeout=10)
        if r.status_code == 200:
            data = r.json()
            # Normalizar: permitir [lista, 200] o dict envolviendo
            if isinstance(data, list) and len(data) == 2 and isinstance(data[0], list) and isinstance(data[1], int):
                data = data[0]
            if isinstance(data, dict) and "proveedores" in data and isinstance(data["proveedores"], list):
                data = data["proveedores"]
            # Quedarse solo con dicts
            data = [d for d in data if isinstance(d, dict)] if isinstance(data, list) else []
            return data
    except Exception as e:
        st.warning(f"No se pudo obtener proveedores: {e}")
    return []

proveedores = fetch_proveedores()

col1, col2 = st.columns([2,1])
with col1:
    st.subheader("Listado")
    if proveedores:
        df = pd.DataFrame(proveedores)
        # columnas amigables
        cols = [c for c in ["id","razon_social","ruc","telefono","email","activo"] if c in df.columns]
        st.dataframe(df[cols] if cols else df, use_container_width=True, height=400)
    else:
        st.info("No hay proveedores registrados.")

with col2:
    st.subheader("Detalles")
    if proveedores:
        ids = [p.get("id") for p in proveedores if isinstance(p, dict) and p.get("id") is not None]
        proveedor_id = st.selectbox("Proveedor", options=ids, format_func=lambda x: next((p.get("razon_social","Proveedor") for p in proveedores if p.get("id") == x), str(x)))
        if proveedor_id:
            # Buscar detalle simple del listado
            p = next((p for p in proveedores if p.get("id") == proveedor_id), None)
            if p:
                st.write(f"**Razón social:** {p.get('razon_social','')}")
                st.write(f"**RUC:** {p.get('ruc','')}")
                st.write(f"**Teléfono:** {p.get('telefono','')}")
                st.write(f"**Email:** {p.get('email','')}")
                st.write(f"**Activo:** {'Sí' if p.get('activo') else 'No'}")
    else:
        st.caption("Sin datos para mostrar detalles")
