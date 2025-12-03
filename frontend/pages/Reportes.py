import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from datetime import datetime

st.set_page_config(page_title="Reportes y Análisis", page_icon="📊", layout="wide")

API_URL = os.getenv("API_GATEWAY_URL", "https://api-gateway-018c.onrender.com")
# URL pública para el navegador del usuario
PUBLIC_GATEWAY_URL = os.getenv("PUBLIC_GATEWAY_URL", "https://api-gateway-018c.onrender.com")

# Utilidades de normalización para respuestas inesperadas
def normalize_list_of_dicts(data, keys):
    """Devuelve una lista de dicts con claves keys.
    - Si data es lista de dicts: filtra y proyecta keys.
    - Si data es lista de tuplas/listas: mapea por posición.
    - Si data es lista de escalares u otro tipo: devuelve [].
    """
    result = []
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                result.append({k: item.get(k) for k in keys})
            elif isinstance(item, (list, tuple)) and len(item) >= len(keys):
                mapped = {k: item[i] for i, k in enumerate(keys)}
                result.append(mapped)
    return result

st.title("📊 Reportes y Análisis")
st.markdown("---")

# Funciones auxiliares
def get_dashboard_data():
    try:
        response = requests.get(f"{API_URL}/reportes/dashboard", timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def get_equipos_por_ubicacion():
    try:
        response = requests.get(f"{API_URL}/reportes/equipos-por-ubicacion", timeout=10)
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []

def get_equipos_por_estado():
    try:
        response = requests.get(f"{API_URL}/reportes/equipos-por-estado", timeout=10)
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []

def get_equipos_por_categoria():
    try:
        response = requests.get(f"{API_URL}/reportes/equipos-por-categoria", timeout=10)
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []

def get_costos_mantenimiento(year=None):
    params = {"year": year} if year else {}
    try:
        response = requests.get(f"{API_URL}/reportes/costos-mantenimiento", params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []

def get_equipos_antiguedad():
    try:
        response = requests.get(f"{API_URL}/reportes/equipos-antiguedad", timeout=10)
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []

# Tabs principales
tab1, tab2, tab3, tab4 = st.tabs(["📈 Dashboard", "📊 Gráficos", "📄 Exportar", "🔍 Análisis Avanzado"])

with tab1:
    st.subheader("Dashboard General")
    
    dashboard = get_dashboard_data()
    # Normalizar: se espera un dict; si es lista con un dict, tomar el primero
    if isinstance(dashboard, list):
        dashboard = dashboard[0] if dashboard and isinstance(dashboard[0], dict) else None
    
    if isinstance(dashboard, dict) and dashboard:
        # Métricas principales
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="📦 Total Equipos",
                value=dashboard.get("total_equipos", 0)
            )
        
        with col2:
            st.metric(
                label="✅ Equipos Operativos",
                value=dashboard.get("equipos_operativos", 0)
            )
        
        with col3:
            st.metric(
                label="🔧 En Reparación",
                value=dashboard.get("equipos_reparacion", 0)
            )
        
        with col4:
            disponibilidad = dashboard.get("tasa_disponibilidad", 0)
            st.metric(
                label="📊 Disponibilidad",
                value=f"{disponibilidad}%",
                delta=f"{disponibilidad - 95:.1f}%"
            )
        
        st.markdown("---")
        
        # Segunda fila
        col1, col2, col3 = st.columns(3)
        
        with col1:
            valor = dashboard.get("valor_inventario", 0)
            st.metric(
                label="💰 Valor Inventario",
                value=f"${valor:,.2f}"
            )
        
        with col2:
            st.metric(
                label="🔧 Mantenimientos (Mes)",
                value=dashboard.get("mantenimientos_mes", 0)
            )
        
        with col3:
            costo = dashboard.get("costo_mantenimiento_mes", 0)
            st.metric(
                label="💵 Costo Mantenim. (Mes)",
                value=f"${costo:,.2f}"
            )
    else:
        st.error("No se pudieron cargar los datos del dashboard")

with tab2:
    st.subheader("Gráficos Estadísticos")
    
    # Equipos por ubicación
    st.markdown("### 📍 Equipos por Ubicación")
    data_ubicacion = get_equipos_por_ubicacion()
    if isinstance(data_ubicacion, dict) and 'data' in data_ubicacion:
        data_ubicacion = data_ubicacion['data']
    # Normalizar a lista de dicts con claves esperadas
    data_ubicacion = normalize_list_of_dicts(data_ubicacion, ['ubicacion', 'cantidad'])
    
    # Definir las columnas esperadas para el DataFrame de ubicaciones
    expected_ubicacion_columns = ['ubicacion', 'cantidad']
    
    # Convertir a DataFrame, asegurando el manejo de datos vacíos o escalares
    try:
        df_ubicacion = pd.DataFrame(data_ubicacion if isinstance(data_ubicacion, list) else [])
        # Asegurarse de que todas las columnas esperadas existan
        for col in expected_ubicacion_columns:
            if col not in df_ubicacion.columns:
                df_ubicacion[col] = pd.NA
    except ValueError:
        st.warning("No se pudo crear el DataFrame de equipos por ubicación. Creando un DataFrame vacío.")
        df_ubicacion = pd.DataFrame(columns=expected_ubicacion_columns)
        
    if not df_ubicacion.empty:
        fig1 = px.bar(
            df_ubicacion,
            x='ubicacion',
            y='cantidad',
            title='Distribución de Equipos por Ubicación',
            labels={'ubicacion': 'Ubicación', 'cantidad': 'Cantidad'},
            color='cantidad',
            color_continuous_scale='Blues'
        )
        fig1.update_layout(showlegend=False)
        st.plotly_chart(fig1, use_container_width=True)
    else:
        st.info("No hay datos disponibles para el reporte de equipos por ubicación.")
    
    st.markdown("---")
    
    # Equipos por estado
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🟢 Equipos por Estado")
        data_estado = get_equipos_por_estado()
        if isinstance(data_estado, dict) and 'data' in data_estado:
            data_estado = data_estado['data']
        # Normalizar a lista de dicts con claves esperadas
        data_estado = normalize_list_of_dicts(data_estado, ['estado', 'cantidad'])
        
        # Definir las columnas esperadas para el DataFrame de estados
        expected_estado_columns = ['estado', 'cantidad']

        # Convertir a DataFrame, asegurando el manejo de datos vacíos o escalares
        try:
            df_estado = pd.DataFrame(data_estado if isinstance(data_estado, list) else [])
            # Asegurarse de que todas las columnas esperadas existan
            for col in expected_estado_columns:
                if col not in df_estado.columns:
                    df_estado[col] = pd.NA
        except ValueError:
            st.warning("No se pudo crear el DataFrame de equipos por estado. Creando un DataFrame vacío.")
            df_estado = pd.DataFrame(columns=expected_estado_columns)
            
        if not df_estado.empty:
            fig2 = px.pie(
                df_estado,
                values='cantidad',
                names='estado',
                title='Estado Operativo de Equipos',
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No hay datos disponibles para el reporte de equipos por estado.")
    
    with col2:
        st.markdown("### 📦 Equipos por Categoría")
        data_categoria = get_equipos_por_categoria()
        if isinstance(data_categoria, dict) and 'data' in data_categoria:
            data_categoria = data_categoria['data']
        # Normalizar a lista de dicts con claves esperadas
        data_categoria = normalize_list_of_dicts(data_categoria, ['categoria', 'cantidad'])
        
        # Definir las columnas esperadas para el DataFrame de categorías
        expected_categoria_columns = ['categoria', 'cantidad']

        # Convertir a DataFrame, asegurando el manejo de datos vacíos o escalares
        try:
            df_categoria = pd.DataFrame(data_categoria if isinstance(data_categoria, list) else [])
            # Asegurarse de que todas las columnas esperadas existan
            for col in expected_categoria_columns:
                if col not in df_categoria.columns:
                    df_categoria[col] = pd.NA
        except ValueError:
            st.warning("No se pudo crear el DataFrame de equipos por categoría. Creando un DataFrame vacío.")
            df_categoria = pd.DataFrame(columns=expected_categoria_columns)

        if not df_categoria.empty:
            fig3 = px.pie(
                df_categoria,
                values='cantidad',
                names='categoria',
                title='Distribución por Categoría',
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("No hay datos disponibles para el reporte de equipos por categoría.")
    
    st.markdown("---")
    
    # Costos de mantenimiento
    st.markdown("### 💵 Costos de Mantenimiento")
    
    year_selected = st.selectbox("Seleccionar Año", [2024, 2023, 2022])
    data_costos = get_costos_mantenimiento(year=year_selected)
    # Normalizar estructura esperada
    if isinstance(data_costos, dict) and 'data' in data_costos:
        data_costos = data_costos['data']
    data_costos = normalize_list_of_dicts(
        data_costos if isinstance(data_costos, list) else [],
        ['mes', 'mes_num', 'tipo', 'total_costo', 'cantidad']
    )

    if data_costos:
        try:
            df_costos = pd.DataFrame(data_costos)
        except Exception:
            st.warning("No se pudo crear el DataFrame de costos. Mostrando datos vacíos.")
            df_costos = pd.DataFrame(columns=['mes','mes_num','tipo','total_costo','cantidad'])
        
        if not df_costos.empty:
            # Agrupar por mes
            df_costos_mes = df_costos.groupby('mes')['total_costo'].sum().reset_index()
            
            fig4 = px.line(
                df_costos_mes,
                x='mes',
                y='total_costo',
                title=f'Costos de Mantenimiento por Mes - {year_selected}',
                labels={'mes': 'Mes', 'total_costo': 'Costo Total ($)'},
                markers=True
            )
            st.plotly_chart(fig4, use_container_width=True)
            
            # Gráfico por tipo
            if 'tipo' in df_costos.columns:
                df_costos_tipo = df_costos.groupby('tipo')['total_costo'].sum().reset_index()
                
                fig5 = px.bar(
                    df_costos_tipo,
                    x='tipo',
                    y='total_costo',
                    title='Costos por Tipo de Mantenimiento',
                    labels={'tipo': 'Tipo', 'total_costo': 'Costo Total ($)'},
                    color='total_costo',
                    color_continuous_scale='Reds'
                )
                st.plotly_chart(fig5, use_container_width=True)
    
    st.markdown("---")
    
    # Antigüedad de equipos
    st.markdown("### ⏰ Antigüedad de Equipos")
    data_antiguedad = get_equipos_antiguedad()
    # Normalizar a lista de dicts con claves esperadas
    if isinstance(data_antiguedad, dict) and 'data' in data_antiguedad:
        data_antiguedad = data_antiguedad['data']
    data_antiguedad = normalize_list_of_dicts(
        data_antiguedad if isinstance(data_antiguedad, list) else [],
        ['rango_antiguedad', 'cantidad']
    )
    
    if data_antiguedad:
        try:
            df_antiguedad = pd.DataFrame(data_antiguedad)
        except Exception:
            st.warning("No se pudo crear el DataFrame de antigüedad. Mostrando datos vacíos.")
            df_antiguedad = pd.DataFrame(columns=['rango_antiguedad','cantidad'])
        
        if not df_antiguedad.empty:
            fig6 = px.bar(
                df_antiguedad,
                x='rango_antiguedad',
                y='cantidad',
                title='Distribución de Equipos por Antigüedad',
                labels={'rango_antiguedad': 'Antigüedad', 'cantidad': 'Cantidad'},
                color='cantidad',
                color_continuous_scale='Oranges'
            )
            st.plotly_chart(fig6, use_container_width=True)

with tab3:
    st.subheader("Exportar Reportes")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📄 Exportar a PDF")
        st.write("Genera un reporte completo en formato PDF")
        
        tipo_reporte_pdf = st.selectbox(
            "Tipo de Reporte (PDF)",
            ["equipos", "mantenimientos", "proveedores"]
        )
        
        if st.button("📥 Generar PDF", use_container_width=True):
            with st.spinner("Generando PDF..."):
                try:
                    response = requests.post(
                        f"{API_URL}/reportes/export/pdf",
                        json={"type": tipo_reporte_pdf},
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        fname = result.get('filename')
                        st.success(f"✅ PDF generado: {fname}")
                        if fname:
                            # Descargar vía gateway
                            try:
                                from os.path import basename
                                safe_name = basename(fname)
                                file_resp = requests.get(
                                    f"{API_URL}/reportes/export/file",
                                    params={"filename": safe_name},
                                    timeout=30
                                )
                                if file_resp.status_code == 200:
                                    st.download_button(
                                        label="⬇️ Descargar PDF",
                                        data=file_resp.content,
                                        file_name=safe_name,
                                        mime="application/pdf",
                                        use_container_width=True
                                    )
                                else:
                                    st.info(f"PDF generado en servidor, pero no se pudo descargar automáticamente (HTTP {file_resp.status_code}).")
                                    st.link_button(
                                        label="🔗 Abrir/Descargar PDF",
                                        url=f"{PUBLIC_GATEWAY_URL}/reportes/export/file?filename={safe_name}",
                                        use_container_width=True
                                    )
                            except Exception as de:
                                st.info(f"PDF guardado en servidor. Descarga manual fallida: {de}")
                    else:
                        st.error("Error al generar PDF")
                except Exception as e:
                    st.error(f"Error: {e}")
    
    with col2:
        st.markdown("### 📊 Exportar a Excel")
        st.write("Genera un reporte detallado en formato Excel")
        
        tipo_reporte_excel = st.selectbox(
            "Tipo de Reporte (Excel)",
            ["equipos", "mantenimientos", "proveedores"]
        )
        
        if st.button("📥 Generar Excel", use_container_width=True):
            with st.spinner("Generando Excel..."):
                try:
                    response = requests.post(
                        f"{API_URL}/reportes/export/excel",
                        json={"type": tipo_reporte_excel},
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        fname = result.get('filename')
                        st.success(f"✅ Excel generado: {fname}")
                        if fname:
                            try:
                                from os.path import basename
                                safe_name = basename(fname)
                                file_resp = requests.get(
                                    f"{API_URL}/reportes/export/file",
                                    params={"filename": safe_name},
                                    timeout=30
                                )
                                if file_resp.status_code == 200:
                                    st.download_button(
                                        label="⬇️ Descargar Excel",
                                        data=file_resp.content,
                                        file_name=safe_name,
                                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                        use_container_width=True
                                    )
                                else:
                                    st.info(f"Excel generado en servidor, pero no se pudo descargar automáticamente (HTTP {file_resp.status_code}).")
                                    st.link_button(
                                        label="🔗 Abrir/Descargar Excel",
                                        url=f"{PUBLIC_GATEWAY_URL}/reportes/export/file?filename={safe_name}",
                                        use_container_width=True
                                    )
                            except Exception as de:
                                st.info(f"Excel guardado en servidor. Descarga manual fallida: {de}")
                    else:
                        st.error("Error al generar Excel")
                except Exception as e:
                    st.error(f"Error: {e}")

with tab4:
    st.subheader("🔍 Análisis Avanzado")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 Valor por Categoría")
        data_categoria = get_equipos_por_categoria()
        # Normalizar a lista de dicts con claves esperadas
        if isinstance(data_categoria, dict) and 'data' in data_categoria:
            data_categoria = data_categoria['data']
        data_categoria = normalize_list_of_dicts(
            data_categoria if isinstance(data_categoria, list) else [],
            ['categoria', 'cantidad', 'valor_total']
        )
        
        if data_categoria:
            try:
                df_cat = pd.DataFrame(data_categoria)
            except Exception:
                st.warning("No se pudo crear el DataFrame de valor por categoría. Mostrando datos vacíos.")
                df_cat = pd.DataFrame(columns=['categoria','cantidad','valor_total'])
            
            if not df_cat.empty and 'valor_total' in df_cat.columns:
                fig = go.Figure(data=[go.Bar(
                    x=df_cat['categoria'],
                    y=df_cat['valor_total'],
                    text=df_cat['valor_total'].apply(lambda x: f'${x:,.0f}' if x is not None else ''),
                    textposition='auto',
                )])
                
                fig.update_layout(
                    title='Valor Total por Categoría',
                    xaxis_title='Categoría',
                    yaxis_title='Valor ($)',
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 🔧 Eficiencia de Mantenimiento")
        dashboard = get_dashboard_data()
        # Normalizar: el dashboard debe ser dict
        if isinstance(dashboard, list):
            dashboard = dashboard[0] if dashboard and isinstance(dashboard[0], dict) else None
        
        if isinstance(dashboard, dict) and dashboard:
            disponibilidad = dashboard.get("tasa_disponibilidad", 0)
            
            fig = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=disponibilidad,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "Tasa de Disponibilidad"},
                delta={'reference': 95},
                gauge={
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 70], 'color': "lightgray"},
                        {'range': [70, 90], 'color': "yellow"},
                        {'range': [90, 100], 'color': "lightgreen"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 95
                    }
                }
            ))
            
            st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    st.markdown("### 📈 Tendencias")
    st.info("💡 Análisis predictivo y tendencias estarán disponibles en próximas versiones")

# Footer
st.markdown("---")
st.caption(f"⏰ Última actualización: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
