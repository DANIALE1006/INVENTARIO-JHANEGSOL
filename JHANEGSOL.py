import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client

st.set_page_config(page_title="Sistema de Inventarios (Compra/Venta)", layout="wide")

# Lectura segura de secretos
SUPABASE_URL = st.secrets["https://cwpispkqdphhiibaqnkb.supabase.co"]
SUPABASE_KEY = st.secrets["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImN3cGlzcGtxZHBoaGlpYmFxbmtiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODA2MTAxNDIsImV4cCI6MjA5NjE4NjE0Mn0.oXDl9yU5BoYdH1WpVbJWHyVs8w6Lu5F9AxUxJnFl8CE"]

@st.cache_resource
def conectar_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

try:
    supabase = conectar_supabase()
except Exception as e:
    st.error(f"Error de conexión con Supabase: {e}")
    st.stop()

# Navegación
opcion = st.sidebar.radio("Navegación", ["Dashboard", "Consolidado Movimientos", "Registrar Compra", "Registrar Venta"])

# Función para consolidar Compras y Ventas
def cargar_movimientos():
    c_res = supabase.table("detalle_compras").select("cantidad, precio_unitario, compras(fecha, proveedores(nombre_empresa)), productos(sku, nombre)").execute().data
    v_res = supabase.table("detalle_ventas").select("cantidad, precio_unitario, ventas(fecha, clientes(nombre)), productos(sku, nombre)").execute().data
    
    filas = []
    for c in c_res:
        filas.append({
            "Fecha": c["compras"]["fecha"],
            "Tipo": "COMPRA",
            "SKU": c["productos"]["sku"],
            "Producto": c["productos"]["nombre"],
            "Cantidad": c["cantidad"],
            "Precio Unitario": c["precio_unitario"],
            "Subtotal": c["cantidad"] * c["precio_unitario"],
            "Tercero": c["compras"]["proveedores"]["nombre_empresa"] if c["compras"]["proveedores"] else "N/A"
        })
    for v in v_res:
        filas.append({
            "Fecha": v["ventas"]["fecha"],
            "Tipo": "VENTA",
            "SKU": v["productos"]["sku"],
            "Producto": v["productos"]["nombre"],
            "Cantidad": -v["cantidad"],
            "Precio Unitario": v["precio_unitario"],
            "Subtotal": v["cantidad"] * v["precio_unitario"],
            "Tercero": v["ventas"]["clientes"]["nombre"] if v["ventas"]["clientes"] else "N/A"
        })
    return pd.DataFrame(filas)

if opcion == "Dashboard":
    st.header("📊 Dashboard de Inventarios")
    df = cargar_movimientos()
    if not df.empty:
        col1, col2 = st.columns(2)
        with col1:
            fig_tipo = px.pie(df, names="Tipo", values="Subtotal", title="Proporción Compras vs Ventas ($)")
            st.plotly_chart(fig_tipo, use_container_width=True)
        with col2:
            fig_prod = px.bar(df, x="Producto", y="Cantidad", color="Tipo", title="Flujo de Productos (Unidades)")
            st.plotly_chart(fig_prod, use_container_width=True)
    else:
        st.info("No hay transacciones registradas.")

elif opcion == "Consolidado Movimientos":
    st.header("📋 Historial de Entradas y Salidas")
    df = cargar_movimientos()
    st.dataframe(df, use_container_width=True)
