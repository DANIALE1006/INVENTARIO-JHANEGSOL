import streamlit as st
from supabase import create_client, Client

# Configuración de la página en Streamlit
st.set_page_config(
    page_title="Sistema de Control de Inventarios (JHANEGSOL)",
    layout="wide"
)

# Configuración de conexión a Supabase
SUPABASE_URL = "https://cwpispkqdphhiibaqnkb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImN3cGlzcGtxZHBoaGlpYmFxbmtiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODA2MTAxNDIsImV4cCI6MjA5NjE4NjE0Mn0.oXDl9yU5BoYdH1WpVbJWHyVs8w6Lu5F9AxUxJnFl8CE"
@st.cache_resource
def init_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

try:
    supabase = init_supabase()
except Exception as e:
    st.error(f"Error de conexión con Supabase: {e}")
    st.stop()

# Menú lateral
opcion = st.sidebar.selectbox(
    "Navegación",
    ["📊 Dashboard General", "📦 Maestro de Productos", "📄 Órdenes de Compra", "📥 Recepción Facturas", "💰 Ventas"]
)

# ---------------------------------------------------------
# 1. DASHBOARD GENERAL (CON ANALÍTICAS SOLICITADAS)
# ---------------------------------------------------------
if opcion == "📊 Dashboard General":
    st.title("📊 Dashboard General - JHANEGSOL")
    st.divider()

    # Métricas Globales
    try:
        res_prod = supabase.table("productos_maestro").select("cantidad_stock, precio_venta").execute().data
        total_prods = len(res_prod)
        stock_total = sum(r.get("cantidad_stock", 0) for r in res_prod)
        valor_total = sum(r.get("cantidad_stock", 0) * r.get("precio_venta", 0) for r in res_prod)
    except Exception:
        total_prods, stock_total, valor_total = 0, 0, 0.0

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Productos", total_prods)
    col2.metric("Stock Total Unidades", stock_total)
    col3.metric("Valor Estimado Inventario", f"${valor_total:,.2f}")

    st.divider()
    c_left, c_mid, c_right = st.columns(3)

    # A. Productos más vendidos
    with c_left:
        st.subheader("🔥 Productos Más Vendidos")
        try:
            res_v = supabase.table("detalle_ventas").select("cantidad, productos(nombre)").execute().data
            if res_v:
                df_v = pd.DataFrame(res_v)
                df_v["Producto"] = df_v["productos"].apply(lambda x: x.get("nombre") if isinstance(x, dict) else "N/A")
                top_ventas = df_v.groupby("Producto")["cantidad"].sum().reset_index()
                top_ventas = top_ventas.sort_values(by="cantidad", ascending=False).head(5)
                st.dataframe(top_ventas, use_container_width=True, hide_index=True)
            else:
                st.info("Sin registro de ventas.")
        except Exception as e:
            st.error(f"Error al procesar ventas: {e}")

    # B. Productos más comprados
    with c_mid:
        st.subheader("📦 Productos Más Comprados")
        try:
            res_c = supabase.table("recep_productos_factura").select("cantidad_ingresada, productos_maestro(nombre)").execute().data
            if res_c:
                df_c = pd.DataFrame(res_c)
                df_c["Producto"] = df_c["productos_maestro"].apply(lambda x: x.get("nombre") if isinstance(x, dict) else "N/A")
                top_compras = df_c.groupby("Producto")["cantidad_ingresada"].sum().reset_index()
                top_compras.columns = ["Producto", "Unidades Compradas"]
                top_compras = top_compras.sort_values(by="Unidades Compradas", ascending=False).head(5)
                st.dataframe(top_compras, use_container_width=True, hide_index=True)
            else:
                st.info("Sin registro de recepciones.")
        except Exception as e:
            st.error(f"Error al procesar recepciones: {e}")

    # C. Proveedores con mejores precios (menor precio unitario promedio)
    with c_right:
        st.subheader("🏷️ Mejores Precios de Proveedores")
        try:
            res_p = supabase.table("recep_productos_factura").select("precio_compra, proveedores(nombre_empresa)").execute().data
            if res_p:
                df_p = pd.DataFrame(res_p)
                df_p["Proveedor"] = df_p["proveedores"].apply(lambda x: x.get("nombre_empresa") if isinstance(x, dict) else "N/A")
                best_prov = df_p.groupby("Proveedor")["precio_compra"].mean().reset_index()
                best_prov.columns = ["Proveedor", "Precio Promedio"]
                best_prov = best_prov.sort_values(by="Precio Promedio", ascending=True).head(5)
                best_prov["Precio Promedio"] = best_prov["Precio Promedio"].map("${:,.2f}".format)
                st.dataframe(best_prov, use_container_width=True, hide_index=True)
            else:
                st.info("Sin registros de compras a proveedores.")
        except Exception as e:
            st.error(f"Error al evaluar proveedores: {e}")

# ---------------------------------------------------------
# 2. MAESTRO DE PRODUCTOS
# ---------------------------------------------------------
elif opcion == "📦 Maestro de Productos":
    st.title("📦 Catálogo Maestro de Productos")
    st.divider()

    try:
        res = supabase.table("productos_maestro").select("""
            codigo_producto, nombre, unidad_medida, precio_venta, cantidad_stock,
            marcas(nombre_marca), modelos(nombre_modelo), tipos_producto(nombre_tipo)
        """).execute().data
        if res:
            st.dataframe(res, use_container_width=True)
        else:
            st.info("No hay productos registrados.")
    except Exception as e:
        st.error(f"Error al consultar productos: {e}")

# ---------------------------------------------------------
# 3. ÓRDENES DE COMPRA
# ---------------------------------------------------------
elif opcion == "📄 Órdenes de Compra":
    st.title("📄 Gestión de Órdenes de Compra (OC)")
    st.divider()

    try:
        res = supabase.table("ordenes_compra").select("""
            numero_orden, fecha_emision, estado, total_estimado,
            proveedores(nombre_empresa)
        """).execute().data
        if res:
            st.dataframe(res, use_container_width=True)
        else:
            st.info("No hay órdenes de compra registradas.")
    except Exception as e:
        st.error(f"Error al consultar órdenes de compra: {e}")

# ---------------------------------------------------------
# 4. RECEPCIÓN FACTURAS
# ---------------------------------------------------------
elif opcion == "📥 Recepción Facturas":
    st.title("📥 Recepción de Productos por N° Factura")
    st.divider()

    try:
        res = supabase.table("recep_productos_factura").select("""
            numero_factura, fecha_factura, cantidad_ingresada, precio_compra,
            ordenes_compra(numero_orden), productos_maestro(codigo_producto, nombre),
            proveedores(nombre_empresa)
        """).execute().data
        if res:
            st.dataframe(res, use_container_width=True)
        else:
            st.info("No hay recepciones registradas.")
    except Exception as e:
        st.error(f"Error al consultar recepciones: {e}")

# ---------------------------------------------------------
# 5. VENTAS (RELACIÓN CORREGIDA A 'productos')
# ---------------------------------------------------------
elif opcion == "💰 Ventas":
    st.title("💰 Salidas y Ventas a Clientes")
    st.divider()

    try:
        res = supabase.table("detalle_ventas").select("""
            cantidad, precio_unitario, subtotal,
            ventas(numero_factura, fecha, metodo_pago, clientes(nombre)),
            productos(codigo_producto, nombre)
        """).execute().data
        if res:
            st.dataframe(res, use_container_width=True)
        else:
            st.info("No hay ventas registradas.")
    except Exception as e:
        st.error(f"Error al consultar ventas: {e}")

