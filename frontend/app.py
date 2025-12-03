import streamlit as st
import requests
import os
import pprint
import time # Importar módulo time
from datetime import datetime

# Configuración de la página
st.set_page_config(
    page_title="Sistema de Gestión TI - Universidad",
    page_icon="🖥️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# URL del API Gateway
# Usa API_GATEWAY_URL de la variable de entorno si está definida.
# Si no, usa 'http://api-gateway:8000' si se ejecuta dentro de Docker,
# o 'http://localhost:8000' para desarrollo local.

API_URL = os.getenv("API_GATEWAY_URL", "https://api-gateway-018c.onrender.com")


# Estilos CSS personalizados
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #1f77b4;
    }
    .alert-box {
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .alert-warning {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
    }
    .alert-danger {
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
    }
    </style>
""", unsafe_allow_html=True)

MAX_RETRIES = 5
RETRY_DELAY = 1 # segundos

def fetch_with_retry(url, method="GET", json_data=None, params=None):
    for i in range(MAX_RETRIES):
        try:
            if method == "GET":
                response = requests.get(url, params=params, timeout=10)
            elif method == "POST":
                response = requests.post(url, json=json_data, timeout=10)
            
            response.raise_for_status() # Lanza una excepción para errores HTTP (4xx o 5xx)
            return response
        except requests.exceptions.ConnectionError as e:
            st.warning(f"Intento {i+1}/{MAX_RETRIES}: Error de conexión a {url}. Reintentando en {RETRY_DELAY}s...")
            time.sleep(RETRY_DELAY)
        except requests.exceptions.Timeout as e:
            st.warning(f"Intento {i+1}/{MAX_RETRIES}: Tiempo de espera agotado al conectar con {url}. Reintentando en {RETRY_DELAY}s...")
            time.sleep(RETRY_DELAY)
        except requests.exceptions.RequestException as e:
            st.error(f"Error en la solicitud a {url}: {e}")
            return None # Salir si es otro tipo de error de solicitud
    st.error(f"Error al conectar con {url} después de {MAX_RETRIES} intentos.")
    return None

def get_dashboard_data():
    """Obtiene los datos del dashboard"""
    response = fetch_with_retry(f"{API_URL}/reportes/dashboard")
    if response and response.status_code == 200:
        return response.json()
    return None

def get_notificaciones():
    """Obtiene las notificaciones no leídas"""
    response = fetch_with_retry(f"{API_URL}/agent/notificaciones?leida=false")
    if response and response.status_code == 200:
        data = response.json()
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            return data.get("data", data.get("notificaciones", []))
        return []
    return []

# Título principal
st.markdown('<h1 class="main-header">🖥️ Sistema de Gestión de Equipos de TI</h1>', unsafe_allow_html=True)
st.markdown("### Universidad - Centro de Tecnología de Información")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.image("https://via.placeholder.com/200x80/667eea/ffffff?text=LOGO+UNI", use_column_width=True)
    st.markdown("### 👤 Usuario")
    st.info("**Admin**\nadmin@universidad.edu")
    
    st.markdown("---")
    st.markdown("### 🔔 Notificaciones")
    notificaciones_raw = get_notificaciones()

    # Asegurarse de que notificaciones sea una lista
    if isinstance(notificaciones_raw, list):
        notificaciones = notificaciones_raw
    else:
        st.warning("El formato de las notificaciones es inesperado.")
        notificaciones = []

    st.code(pprint.pformat(notificaciones_raw), language="python")
    st.code(str(type(notificaciones_raw)), language="python")

    # Mostrar notificaciones
    if isinstance(notificaciones, list) and len(notificaciones) > 0:
        st.warning(f"**{len(notificaciones)}** notificaciones pendientes")

        with st.expander("Ver notificaciones"):
            for notif_item in notificaciones[:5]:
                if isinstance(notif_item, dict):
                    titulo = notif_item.get('titulo', 'Sin título')
                    mensaje = notif_item.get('mensaje', '')
                    
                    st.markdown(f"**{str(titulo)}**")
                    st.caption(str(mensaje)[:100])
                    st.divider()
                else:
                    st.caption("Formato inesperado: " + str(type(notif_item)))
    else:
        st.success("Sin notificaciones pendientes")

    
    st.markdown("---")
    st.markdown("### ⚙️ Sistema")
    if st.button("🔄 Ejecutar Agentes", use_container_width=True):
        with st.spinner("Ejecutando agentes..."):
            response = fetch_with_retry(f"{API_URL}/agent/run-all-agents", method="POST")
            if response and response.status_code == 200:
                st.success("Agentes ejecutados correctamente")
            else:
                st.error("Error al ejecutar agentes")

# Dashboard principal
dashboard_data = get_dashboard_data()

# Asegurarse de que dashboard_data sea un diccionario antes de intentar acceder a sus claves
if isinstance(dashboard_data, dict) and dashboard_data:
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📦 Total Equipos",
            value=dashboard_data.get("total_equipos", 0),
            delta=None
        )
    
    with col2:
        disponibilidad = dashboard_data.get("tasa_disponibilidad", 0)
        st.metric(
            label="✅ Disponibilidad",
            value=f"{disponibilidad}%",
            delta=f"{disponibilidad - 95:.1f}%" if disponibilidad else None
        )
    
    with col3:
        valor = dashboard_data.get("valor_inventario", 0)
        st.metric(
            label="💰 Valor Inventario",
            value=f"${valor:,.2f}",
            delta=None
        )
    
    with col4:
        st.metric(
            label="🔧 Mantenimientos (Mes)",
            value=dashboard_data.get("mantenimientos_mes", 0),
            delta=None
        )
    
    st.markdown("---")
    
    # Segunda fila de métricas
    col1, col2, col3 = st.columns(3)
    
    with col1:
        operativos = dashboard_data.get("equipos_operativos", 0)
        st.metric(
            label="🟢 Equipos Operativos",
            value=operativos
        )
    
    with col2:
        reparacion = dashboard_data.get("equipos_reparacion", 0)
        st.metric(
            label="🔴 En Reparación",
            value=reparacion
        )
    
    with col3:
        costo = dashboard_data.get("costo_mantenimiento_mes", 0)
        st.metric(
            label="💵 Costo Mantenim. (Mes)",
            value=f"${costo:,.2f}"
        )
    
    st.markdown("---")
    
    # Información rápida
    st.markdown("### 📊 Información del Sistema")
    
    tab1, tab2, tab3 = st.tabs(["🎯 Resumen", "📈 Estadísticas", "ℹ️ Acerca de"])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Estado del Inventario")
            total = dashboard_data.get("total_equipos", 1)
            operativos = dashboard_data.get("equipos_operativos", 0)
            reparacion = dashboard_data.get("equipos_reparacion", 0)
            
            st.progress(operativos / total if total > 0 else 0)
            st.caption(f"Equipos Operativos: {operativos}/{total}")
            
            if reparacion > 0:
                st.warning(f"⚠️ {reparacion} equipos en reparación")
        
        with col2:
            st.markdown("#### Mantenimientos")
            st.info(f"📅 {dashboard_data.get('mantenimientos_mes', 0)} programados este mes")
            st.info(f"💵 Costo mensual: ${dashboard_data.get('costo_mantenimiento_mes', 0):,.2f}")
    
    with tab2:
        st.markdown("#### Métricas Clave")
        st.json({
            "total_equipos": dashboard_data.get("total_equipos", 0),
            "tasa_disponibilidad": f"{dashboard_data.get('tasa_disponibilidad', 0)}%",
            "valor_inventario": f"${dashboard_data.get('valor_inventario', 0):,.2f}",
            "equipos_operativos": dashboard_data.get("equipos_operativos", 0),
            "equipos_en_reparacion": dashboard_data.get("equipos_reparacion", 0)
        })
    
    with tab3:
        st.markdown("""
        ### Sistema de Gestión de Equipos de TI
        
        **Versión:** 1.0.0  
        **Última actualización:** Noviembre 2024
        
        #### Características:
        - ✅ Gestión integral de inventario
        - ✅ Control de mantenimientos
        - ✅ Administración de proveedores
        - ✅ Reportes y análisis avanzados
        - ✅ Agentes inteligentes de automatización
        - ✅ Alertas y notificaciones en tiempo real
        
        #### Tecnologías:
        - Frontend: Streamlit
        - Backend: Microservicios Python (FastAPI)
        - Base de datos: PostgreSQL
        - Despliegue: Docker & Docker Compose
        
        ---
        **Desarrollado para:** Universidad - Departamento de TI
        """)

else:
    st.error("⚠️ No se pudo conectar con el servidor. Verifique que todos los servicios estén activos.")
    st.info("💡 Ejecute: `docker-compose up -d` para iniciar los servicios")

# Footer
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.caption("📧 Soporte: ti@universidad.edu")
with col2:
    st.caption(f"⏰ {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
with col3:
    st.caption("🔒 Sistema Seguro")
