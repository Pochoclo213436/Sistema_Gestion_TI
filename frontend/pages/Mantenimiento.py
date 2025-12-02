import streamlit as st
import requests
import pandas as pd
import os

st.set_page_config(page_title="Mantenimiento", page_icon="🛠️", layout="wide")

API_URL = os.getenv("API_GATEWAY_URL", "http://api-gateway:8000")

st.title("🛠️ Mantenimientos")
st.markdown("---")

def normalize_tuples(rows, keys):
    out = []
    if isinstance(rows, list):
        for r in rows:
            if isinstance(r, dict):
                out.append({k: r.get(k) for k in keys})
            elif isinstance(r, (list, tuple)):
                d = {}
                for i, k in enumerate(keys):
                    if i < len(r):
                        d[k] = r[i]
                out.append(d)
    return out

@st.cache_data(ttl=15)
def fetch_mantenimientos():
    try:
        r = requests.get(f"{API_URL}/mantenimiento/mantenimientos", timeout=10)
        if r.status_code == 200:
            data = r.json()
            # Admitir {"mantenimientos": [...]}
            if isinstance(data, dict) and "mantenimientos" in data:
                data = data["mantenimientos"]
            # Admitir [lista, 200]
            if isinstance(data, list) and len(data) == 2 and isinstance(data[0], list) and isinstance(data[1], int):
                data = data[0]
            return normalize_tuples(data, ["id","equipo_id","fecha","tipo","costo"]) if isinstance(data, list) else []
    except Exception as e:
        st.warning(f"No se pudo obtener mantenimientos: {e}")
    return []

tab1, tab2 = st.tabs(["📋 Lista", "➕ Nuevo"])

with tab1:
    mantenimientos = fetch_mantenimientos()
    st.subheader("Listado de Mantenimientos")
    if mantenimientos:
        df = pd.DataFrame(mantenimientos)
        st.dataframe(df, use_container_width=True, height=420)
    else:
        st.info("No hay mantenimientos registrados.")

with tab2:
    st.subheader("Registrar Mantenimiento")
    with st.form("form_mant"):
        col1, col2 = st.columns(2)
        with col1:
            equipo_id = st.number_input("ID de Equipo", min_value=1, step=1)
            costo = st.number_input("Costo", min_value=0.0, step=0.1, format="%.2f")
        with col2:
            tipo = st.selectbox("Tipo", ["preventivo","correctivo","calibracion","otro"]) 
        submitted = st.form_submit_button("💾 Guardar", use_container_width=True)

    if submitted:
        try:
            # Este endpoint espera parámetros simples, no JSON
            r = requests.post(
                f"{API_URL}/mantenimiento/mantenimientos",
                params={"equipo_id": int(equipo_id), "tipo": tipo, "costo": float(costo)},
                timeout=10
            )
            if r.status_code == 200:
                st.success("Mantenimiento registrado correctamente")
                st.cache_data.clear()
            else:
                st.error(f"Error al registrar: {r.text}")
        except Exception as e:
            st.error(f"Error de conexión: {e}")

