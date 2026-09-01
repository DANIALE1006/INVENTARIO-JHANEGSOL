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

# Menú de Navegación Lateral
st.sidebar.title("📌 Menú Principal")
opcion = st.sidebar.radio(
    "Selecciona una opción:",
    [
        "📊 Dashboard General",
        "📦 Maestro de Productos",
        "📄 Órdenes de Compra",
        "📥 Recepción con Factura",
        "💰 Registro de Ventas",
        "📋 Consolidado de Movimientos"
    ]
)

# 1. DASHBOARD GENERAL
if opcion == "📊 Dashboard General":
    st.header("📊 Dashboard de Control de Inventario")
    
    # Cargar stock de productos
    res_prod = supabase.table("productos_maestro").select("""
        codigo_producto, nombre, cantidad_stock, precio_venta,
        marcas(nombre_marca), tipos_producto(nombre_tipo)
    """).execute().data
    
    if res_prod:
        df_prod = pd.DataFrame(res_prod)
        df_prod["Marca"] = df_prod["marcas"].apply(lambda x: x["nombre_marca"] if x else "N/A")
        df_prod["Tipo"] = df_prod["tipos_producto"].apply(lambda x: x["nombre_tipo"] if x else "N/A")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Productos", len(df_prod))
        col2.metric("Stock Total Unidades", int(df_prod["cantidad_stock"].sum()))
        col3.metric("Valor Estimado Inventario ($)", f"{float((df_prod['cantidad_stock'] * df_prod['precio_venta']).sum()):,.2f}")
        
        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            fig_marca = px.pie(df_prod, names="Marca", values="cantidad_stock", title="Stock Disponible por Marca")
            st.plotly_chart(fig_marca, use_container_width=True)
        with c2:
            fig_tipo = px.bar(df_prod, x="Tipo", y="cantidad_stock", color="Marca", title="Unidades por Tipo de Producto")
            st.plotly_chart(fig_tipo, use_container_width=True)
    else:
        st.info("No hay productos registrados en la base de datos.")

# 2. MAESTRO DE PRODUCTOS
elif opcion == "📦 Maestro de Productos":
    st.header("📦 Catálogo Maestro de Productos")
    
    res = supabase.table("productos_maestro").select("""
        codigo_producto, nombre, unidad_medida, precio_venta, cantidad_stock,
        marcas(nombre_marca), modelos(nombre_modelo), tipos_producto(nombre_tipo)
    """).execute().data
    
    if res:
        datos = []
        for r in res:
            datos.append({
                "Código": r["codigo_producto"],
                "Producto": r["nombre"],
                "Marca": r["marcas"]["nombre_marca"] if r["marcas"] else "N/A",
                "Modelo": r["modelos"]["nombre_modelo"] if r["modelos"] else "N/A",
                "Tipo": r["tipos_producto"]["nombre_tipo"] if r["tipos_producto"] else "N/A",
                "U.M.": r["unidad_medida"],
                "Precio Venta ($)": r["precio_venta"],
                "Stock Actual": r["cantidad_stock"]
            })
        st.dataframe(pd.DataFrame(datos), use_container_width=True)
    else:
        st.warning("No se encontraron registros de productos.")

# 3. ÓRDENES DE COMPRA
elif opcion == "📄 Órdenes de Compra":
    st.header("📄 Gestión de Órdenes de Compra (OC)")
    
    res_oc = supabase.table("ordenes_compra").select("""
        numero_orden, fecha_emision, estado, total_estimado,
        proveedores(nombre_empresa)
    """).execute().data
    
    if res_oc:
        datos_oc = []
        for o in res_oc:
            datos_oc.append({
                "N° Órden": o["numero_orden"],
                "Fecha Emisión": o["fecha_emision"],
                "Proveedor": o["proveedores"]["nombre_empresa"] if o["proveedores"] else "N/A",
                "Estado": o["estado"],
                "Total Estimado ($)": o["total_estimado"]
            })
        st.dataframe(pd.DataFrame(datos_oc), use_container_width=True)
    else:
        st.info("No existen órdenes de compra registradas.")

# 4. RECEPCIÓN CON FACTURA
elif opcion == "📥 Recepción con Factura":
    st.header("📥 Recepción de Productos por N° Factura")
    
    res_fac = supabase.table("recep_productos_factura").select("""
        numero_factura, fecha_factura, cantidad_ingresada, precio_compra,
        ordenes_compra(numero_orden), productos_maestro(codigo_producto, nombre),
        proveedores(nombre_empresa)
    """).execute().data
    
    if res_fac:
        datos_f = []
        for f in res_fac:
            datos_f.append({
                "N° Factura": f["numero_factura"],
                "Fecha": f["fecha_factura"],
                "N° Orden Compra": f["ordenes_compra"]["numero_orden"] if f["ordenes_compra"] else "SIN OC",
                "Proveedor": f["proveedores"]["nombre_empresa"] if f["proveedores"] else "N/A",
                "Código Prod.": f["productos_maestro"]["codigo_producto"] if f["productos_maestro"] else "",
                "Producto": f["productos_maestro"]["nombre"] if f["productos_maestro"] else "",
                "Cantidad Ingresada": f["cantidad_ingresada"],
                "Precio Compra ($)": f["precio_compra"],
                "Subtotal ($)": f["cantidad_ingresada"] * f["precio_compra"]
            })
        st.dataframe(pd.DataFrame(datos_f), use_container_width=True)
    else:
        st.info("No hay ingresos de mercadería por factura registrados.")

# 5. REGISTRO DE VENTAS
elif opcion == "💰 Registro de Ventas":
    st.header("💰 Salidas y Ventas a Clientes")
    
    res_v = supabase.table("detalle_ventas").select("""
        cantidad, precio_unitario, subtotal,
        ventas(numero_factura, fecha, metodo_pago, clientes(nombre)),
        productos_maestro(codigo_producto, nombre)
    """).execute().data
    
    if res_v:
        datos_v = []
        for v in res_v:
            datos_v.append({
                "N° Comprobante": v["ventas"]["numero_factura"] if v["ventas"] else "N/A",
                "Fecha": v["ventas"]["fecha"] if v["ventas"] else None,
                "Cliente": v["ventas"]["clientes"]["nombre"] if v["ventas"] and v["ventas"]["clientes"] else "CLIENTE VARIOS",
                "Método Pago": v["ventas"]["metodo_pago"] if v["ventas"] else "N/A",
                "Código Prod.": v["productos_maestro"]["codigo_producto"] if v["productos_maestro"] else "",
                "Producto": v["productos_maestro"]["nombre"] if v["productos_maestro"] else "",
                "Cantidad Vendida": v["cantidad"],
                "Precio Venta ($)": v["precio_unitario"],
                "Total ($)": v["subtotal"]
            })
        st.dataframe(pd.DataFrame(datos_v), use_container_width=True)
    else:
        st.info("No hay ventas registradas.")

# 6. CONSOLIDADO DE MOVIMIENTOS
elif opcion == "📋 Consolidado de Movimientos":
    st.header("📋 Historial Consolidado (Entradas vs Salidas)")
    
    res_compras = supabase.table("recep_productos_factura").select("""
        numero_factura, fecha_factura, cantidad_ingresada, precio_compra,
        proveedores(nombre_empresa), productos_maestro(codigo_producto, nombre, marcas(nombre_marca))
    """).execute().data
    
    res_ventas = supabase.table("detalle_ventas").select("""
        cantidad, precio_unitario, subtotal,
        ventas(numero_factura, fecha, metodo_pago, clientes(nombre)),
        productos_maestro(codigo_producto, nombre, marcas(nombre_marca))
    """).execute().data
    
    filas = []
    
    for c in res_compras:
        filas.append({
            "Tipo": "ENTRADA (COMPRA)",
            "Documento": c["numero_factura"],
            "Fecha": c["fecha_factura"],
            "Entidad": c["proveedores"]["nombre_empresa"] if c["proveedores"] else "PROVEEDOR N/A",
            "Código": c["productos_maestro"]["codigo_producto"] if c["productos_maestro"] else "",
            "Producto": c["productos_maestro"]["nombre"] if c["productos_maestro"] else "",
            "Marca": c["productos_maestro"]["marcas"]["nombre_marca"] if c["productos_maestro"] and c["productos_maestro"]["marcas"] else "",
            "Cantidad": c["cantidad_ingresada"],
            "Precio Unitario": c["precio_compra"],
            "Total ($)": c["cantidad_ingresada"] * c["precio_compra"]
        })
        
    for v in res_ventas:
        filas.append({
            "Tipo": "SALIDA (VENTA)",
            "Documento": v["ventas"]["numero_factura"] if v["ventas"] else "N/A",
            "Fecha": v["ventas"]["fecha"] if v["ventas"] else None,
            "Entidad": v["ventas"]["clientes"]["nombre"] if v["ventas"] and v["ventas"]["clientes"] else "CLIENTE VARIOS",
            "Código": v["productos_maestro"]["codigo_producto"] if v["productos_maestro"] else "",
            "Producto": v["productos_maestro"]["nombre"] if v["productos_maestro"] else "",
            "Marca": v["productos_maestro"]["marcas"]["nombre_marca"] if v["productos_maestro"] and v["productos_maestro"]["marcas"] else "",
            "Cantidad": -v["cantidad"],
            "Precio Unitario": v["precio_unitario"],
            "Total ($)": v["subtotal"]
        })
        
    if filas:
        df_consolidado = pd.DataFrame(filas)
        st.dataframe(df_consolidado, use_container_width=True)
    else:
        st.info("No hay movimientos registrados.")
elif opcion == "Consolidado Movimientos":
    st.header("📋 Historial de Entradas y Salidas")
    df = cargar_movimientos()
    st.dataframe(df, use_container_width=True)
