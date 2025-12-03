import streamlit as st
import requests
import pandas as pd
import os
from datetime import datetime, date

st.set_page_config(page_title="Gestión de Equipos", page_icon="📦", layout="wide")

API_URL = os.getenv("API_GATEWAY_URL", "https://api-gateway-018c.onrender.com")

st.title("📦 Gestión de Equipos")
st.markdown("---")

# Funciones auxiliares
def get_equipos(categoria=None, estado=None):
    params = {}
    if categoria:
        params['categoria'] = categoria
    if estado:
        params['estado'] = estado
    
    try:
        response = requests.get(f"{API_URL}/equipos/equipos", params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        st.error(f"Error: {e}")
        return []

def get_categorias():
    try:
        response = requests.get(f"{API_URL}/equipos/categorias", timeout=10)
        if response.status_code == 200:
            data = response.json()
            categorias_list = []
            if isinstance(data, list):
                categorias_list = data
            elif isinstance(data, dict):
                if "data" in data and isinstance(data["data"], list):
                    categorias_list = data["data"]
                elif "categorias" in data and isinstance(data["categorias"], list):
                    categorias_list = data["categorias"]
            # Normalizar: quedarnos solo con dicts válidos con id y nombre
            categorias_list = [c for c in categorias_list if isinstance(c, dict) and 'id' in c and 'nombre' in c]
            return categorias_list
        return []
    except Exception as e:
        st.error(f"Error al obtener categorías: {e}")
        return []

def get_ubicaciones():
    try:
        response = requests.get(f"{API_URL}/equipos/ubicaciones", timeout=10)
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []

def get_proveedores():
    try:
        response = requests.get(f"{API_URL}/proveedores/proveedores", timeout=10)
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []

# Tabs principales
tab1, tab2, tab3 = st.tabs(["📋 Lista de Equipos", "➕ Nuevo Equipo", "📊 Estadísticas"])

with tab1:
    st.subheader("Inventario de Equipos")
    
    # Filtros
    col1, col2, col3, col4 = st.columns(4)
    
    categorias = get_categorias()
    # Asegurarse de que cada elemento en 'categorias' sea un diccionario antes de acceder a 'nombre'
    cat_nombres = ["Todas"] + [c['nombre'] for c in categorias if isinstance(c, dict) and 'nombre' in c]
    
    with col1:
        filtro_categoria = st.selectbox("Categoría", cat_nombres)
    
    with col2:
        filtro_estado = st.selectbox("Estado", ["Todos", "operativo", "en_reparacion", "obsoleto", "dado_baja", "en_almacen"])
    
    with col3:
        st.write("")
        st.write("")
        if st.button("🔍 Buscar", use_container_width=True):
            st.rerun()
    
    with col4:
        st.write("")
        st.write("")
        if st.button("🔄 Actualizar", use_container_width=True):
            st.rerun()
    
    # Obtener equipos con filtros
    categoria_filtro = filtro_categoria if filtro_categoria != "Todas" else None
    estado_filtro = filtro_estado if filtro_estado != "Todos" else None
    
    equipos = get_equipos(categoria=categoria_filtro, estado=estado_filtro)
    # Normalizar: asegurar lista de diccionarios
    if isinstance(equipos, dict):
        equipos = [equipos]
    if not isinstance(equipos, list):
        equipos = []
    equipos = [e for e in equipos if isinstance(e, dict)]
    
    if equipos:
        st.success(f"Se encontraron {len(equipos)} equipos")
        
        # Definir las columnas esperadas para asegurar la consistencia del DataFrame
        expected_columns = [
            'codigo_inventario', 'nombre', 'marca', 'modelo',
            'categoria_id', 'numero_serie', 'fecha_compra', 'costo_compra',
            'fecha_garantia_fin', 'proveedor_id', 'ubicacion_actual_id',
            'estado_operativo', 'estado_fisico', 'notas',
            'categoria_nombre', 'ubicacion_nombre', 'proveedor_nombre'
        ]
        
        # Convertir a DataFrame, asegurando que se manejen correctamente los datos o se cree un DF vacío si hay problemas
        try:
            df = pd.DataFrame(equipos if isinstance(equipos, list) else [])
            # Asegurarse de que todas las columnas esperadas existan, añadiéndolas si faltan con pd.NA
            for col in expected_columns:
                if col not in df.columns:
                    df[col] = pd.NA
        except Exception:
            # Si el error persiste (ej. equipos es una lista de escalares), crear un DataFrame vacío
            st.warning("No se pudo crear el DataFrame con los datos recibidos. Creando un DataFrame vacío con columnas esperadas.")
            df = pd.DataFrame(columns=expected_columns)
        
        # Seleccionar columnas relevantes
        columnas_mostrar = ['codigo_inventario', 'nombre', 'marca', 'modelo', 
                           'categoria_nombre', 'estado_operativo', 'ubicacion_nombre']
        
        columnas_disponibles = [col for col in columnas_mostrar if col in df.columns]
        df_mostrar = df[columnas_disponibles]
        
        # Renombrar columnas
        df_mostrar.columns = ['Código', 'Nombre', 'Marca', 'Modelo', 
                              'Categoría', 'Estado', 'Ubicación'][:len(df_mostrar.columns)]
        
        # Aplicar colores según estado
        def color_estado(val):
            if val == 'operativo':
                return 'background-color: #d4edda'
            elif val == 'en_reparacion':
                return 'background-color: #fff3cd'
            elif val == 'obsoleto':
                return 'background-color: #f8d7da'
            return ''
        
        if 'Estado' in df_mostrar.columns:
            st.dataframe(
                df_mostrar.style.applymap(color_estado, subset=['Estado']),
                use_container_width=True,
                height=400
            )
        else:
            st.dataframe(df_mostrar, use_container_width=True, height=400)
        
        # Detalle de equipo seleccionado
        st.markdown("---")
        st.subheader("Detalle de Equipo")
        
        # Filtrar equipos para asegurar que solo contengan diccionarios válidos con 'codigo_inventario'
        valid_equipos = [e for e in equipos if isinstance(e, dict) and 'codigo_inventario' in e]

        equipo_seleccionado = st.selectbox(
            "Seleccionar equipo",
            options=[e['codigo_inventario'] for e in valid_equipos],
            format_func=lambda x: f"{x} - {next((e['nombre'] for e in valid_equipos if e['codigo_inventario'] == x), '')}"
        )
        
        if equipo_seleccionado:
            equipo = next((e for e in equipos if e['codigo_inventario'] == equipo_seleccionado), None)
            
            if equipo:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("#### Información General")
                    st.write(f"**Código:** {equipo.get('codigo_inventario', 'N/A')}")
                    st.write(f"**Nombre:** {equipo.get('nombre', 'N/A')}")
                    st.write(f"**Marca:** {equipo.get('marca', 'N/A')}")
                    st.write(f"**Modelo:** {equipo.get('modelo', 'N/A')}")
                    st.write(f"**Serie:** {equipo.get('numero_serie', 'N/A')}")
                
                with col2:
                    st.markdown("#### Estado")
                    estado = equipo.get('estado_operativo', 'N/A')
                    if estado == 'operativo':
                        st.success(f"🟢 {estado.upper()}")
                    elif estado == 'en_reparacion':
                        st.warning(f"🟡 {estado.upper()}")
                    else:
                        st.error(f"🔴 {estado.upper()}")
                    
                    st.write(f"**Categoría:** {equipo.get('categoria_nombre', 'N/A')}")
                    st.write(f"**Ubicación:** {equipo.get('ubicacion_nombre', 'N/A')}")
                
                with col3:
                    st.markdown("#### Información Económica")
                    st.write(f"**Proveedor:** {equipo.get('proveedor_nombre', 'N/A')}")
                    if equipo.get('fecha_compra'):
                        st.write(f"**Fecha Compra:** {equipo['fecha_compra']}")
                    if equipo.get('costo_compra'):
                        st.write(f"**Costo:** ${equipo['costo_compra']:,.2f}")
                    if equipo.get('fecha_garantia_fin'):
                        st.write(f"**Garantía hasta:** {equipo['fecha_garantia_fin']}")
    else:
        st.info("No se encontraron equipos con los filtros seleccionados")

with tab2:
    st.subheader("Registrar Nuevo Equipo")
    
    with st.form("form_nuevo_equipo"):
        col1, col2 = st.columns(2)
        
        with col1:
            codigo = st.text_input("Código de Inventario*", placeholder="EQ-2024-001")
            nombre = st.text_input("Nombre del Equipo*", placeholder="Laptop Dell Inspiron")
            marca = st.text_input("Marca", placeholder="Dell")
            modelo = st.text_input("Modelo", placeholder="Inspiron 15 3000")
            
            categorias = get_categorias()
            # Filtrar solo categorías válidas con id y nombre
            valid_categorias = [c for c in categorias if isinstance(c, dict) and 'id' in c and 'nombre' in c]
            if not valid_categorias:
                st.warning("No hay categorías disponibles o el formato de categorías es inválido.")
            categoria_id = st.selectbox(
                "Categoría*",
                options=[None] + [c['id'] for c in valid_categorias],
                format_func=lambda x: "Seleccione..." if x is None else next((c['nombre'] for c in valid_categorias if c['id'] == x), '')
            )
        
        with col2:
            numero_serie = st.text_input("Número de Serie", placeholder="ABC123XYZ")
            
            fecha_compra = st.date_input("Fecha de Compra", value=date.today())
            costo_compra = st.number_input("Costo de Compra", min_value=0.0, value=0.0, format="%.2f")
            fecha_garantia = st.date_input("Fecha Fin Garantía", value=date.today())
            
            proveedores = get_proveedores()
            # Filtrar proveedores para asegurar que solo contengan diccionarios válidos con 'id'
            valid_proveedores = [p for p in proveedores if isinstance(p, dict) and 'id' in p]
            
            proveedor_id = st.selectbox(
                "Proveedor",
                options=[None] + [p['id'] for p in valid_proveedores],
                format_func=lambda x: "Ninguno" if x is None else next((p['razon_social'] for p in valid_proveedores if p['id'] == x), '')
            )
            
            ubicaciones = get_ubicaciones()
            # Filtrar ubicaciones para asegurar que solo contengan diccionarios válidos con 'id'
            valid_ubicaciones = [u for u in ubicaciones if isinstance(u, dict) and 'id' in u]

            ubicacion_id = st.selectbox(
                "Ubicación",
                options=[u['id'] for u in valid_ubicaciones],
                format_func=lambda x: next((u['nombre_completo'] for u in valid_ubicaciones if u['id'] == x), '')
            )
            
            estado_operativo = st.selectbox("Estado Operativo", 
                ["operativo", "en_reparacion", "obsoleto", "dado_baja", "en_almacen"])
            estado_fisico = st.selectbox("Estado Físico", 
                ["excelente", "bueno", "regular", "malo"])
        
        notas = st.text_area("Notas / Observaciones", placeholder="Información adicional del equipo...")
        
        submitted = st.form_submit_button("💾 Guardar Equipo", use_container_width=True)

    if submitted:
        if not codigo or not nombre or categoria_id is None:
            st.error("⚠️ Los campos Código, Nombre y Categoría son obligatorios")
        else:
            nuevo_equipo = {
                "codigo_inventario": codigo,
                "nombre": nombre,
                "marca": marca,
                "modelo": modelo,
                "categoria_id": categoria_id,
                "numero_serie": numero_serie,
                "fecha_compra": str(fecha_compra),
                "costo_compra": costo_compra,
                "fecha_garantia_fin": str(fecha_garantia),
                "proveedor_id": proveedor_id,
                "ubicacion_actual_id": ubicacion_id,
                "estado_operativo": estado_operativo,
                "estado_fisico": estado_fisico,
                "notas": notas
            }
            
            try:
                response = requests.post(
                    f"{API_URL}/equipos/equipos",
                    json=nuevo_equipo,
                    timeout=10
                )
                
                if response.status_code == 200:
                    st.success("✅ Equipo registrado exitosamente")
                    st.balloons()
                else:
                    st.error(f"❌ Error al registrar equipo: {response.text}")
            except Exception as e:
                st.error(f"❌ Error de conexión: {e}")

with tab3:
    st.subheader("Estadísticas de Equipos")
    
    equipos = get_equipos()
    # Normalizar: asegurar lista de diccionarios
    if isinstance(equipos, dict):
        equipos = [equipos]
    if not isinstance(equipos, list):
        equipos = []
    equipos = [e for e in equipos if isinstance(e, dict)]
    
    # Definir las columnas esperadas para asegurar la consistencia del DataFrame
    expected_columns = [
        'codigo_inventario', 'nombre', 'marca', 'modelo',
        'categoria_id', 'numero_serie', 'fecha_compra', 'costo_compra',
        'fecha_garantia_fin', 'proveedor_id', 'ubicacion_actual_id',
        'estado_operativo', 'estado_fisico', 'notas',
        'categoria_nombre', 'ubicacion_nombre', 'proveedor_nombre'
    ]
    
    # Convertir a DataFrame, asegurando que se manejen correctamente los datos o se cree un DF vacío si hay problemas
    try:
        df = pd.DataFrame(equipos if isinstance(equipos, list) else [])
        # Asegurarse de que todas las columnas esperadas existan, añadiéndolas si faltan con pd.NA
        for col in expected_columns:
            if col not in df.columns:
                df[col] = pd.NA
    except Exception:
        # Si el error persiste (ej. equipos es una lista de escalares), crear un DataFrame vacío
        st.warning("No se pudo crear el DataFrame de estadísticas con los datos recibidos. Creando un DataFrame vacío con columnas esperadas.")
        df = pd.DataFrame(columns=expected_columns)
    
    if not df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Equipos por Estado")
            if 'estado_operativo' in df.columns:
                estado_counts = df['estado_operativo'].value_counts()
                st.bar_chart(estado_counts)
        
        with col2:
            st.markdown("#### Equipos por Categoría")
            if 'categoria_nombre' in df.columns:
                cat_counts = df['categoria_nombre'].value_counts()
                st.bar_chart(cat_counts)
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Valor del Inventario")
            if 'costo_compra' in df.columns:
                valor_total = df['costo_compra'].sum()
                st.metric("Valor Total", f"${valor_total:,.2f}")
        
        with col2:
            st.markdown("#### Equipos por Ubicación")
            if 'ubicacion_nombre' in df.columns:
                ubic_counts = df['ubicacion_nombre'].value_counts().head(5)
                st.bar_chart(ubic_counts)
    else:
        st.info("No hay datos disponibles para generar estadísticas")
