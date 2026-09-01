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
# 1. DASHBOARD GENERAL
# ---------------------------------------------------------
if opcion == "📊 Dashboard General":
    st.title("📊 Dashboard General - JHANEGSOL")
    st.divider()

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
                st.info("Sin registros de compras.")
        except Exception as e:
            st.error(f"Error al evaluar proveedores: {e}")

# ---------------------------------------------------------
# 2. MAESTRO DE PRODUCTOS (CON FORMULARIO CREAR Y EDITAR)
# ---------------------------------------------------------
elif opcion == "📦 Maestro de Productos":
    st.title("📦 Catálogo Maestro de Productos")
    st.divider()

    # Cargar datos auxiliares para los desplegables
    try:
        marcas_data = supabase.table("marcas").select("id_marca, nombre_marca").execute().data
        modelos_data = supabase.table("modelos").select("id_modelo, nombre_modelo").execute().data
        tipos_data = supabase.table("tipos_producto").select("id_tipo, nombre_tipo").execute().data

        dict_marcas = {m["nombre_marca"]: m["id_marca"] for m in marcas_data} if marcas_data else {}
        dict_modelos = {m["nombre_modelo"]: m["id_modelo"] for m in modelos_data} if modelos_data else {}
        dict_tipos = {t["nombre_tipo"]: t["id_tipo"] for t in tipos_data} if tipos_data else {}
    except Exception as e:
        st.error(f"Error al obtener catalogos de apoyo: {e}")

    # Formulario desplegable
    with st.expander("➕ Registrar / Editar Producto", expanded=False):
        
        # Consultar productos existentes para opción de edición
        prods_existentes = supabase.table("productos_maestro").select("codigo_producto, nombre").execute().data
        dict_prods = {f"{p['codigo_producto']} - {p['nombre']}": p["codigo_producto"] for p in prods_existentes} if prods_existentes else {}
        
        modo = st.radio("Acción:", ["Crear Nuevo Producto", "Editar Producto Existente"], horizontal=True)

        if modo == "Editar Producto Existente" and dict_prods:
            prod_sel = st.selectbox("Selecciona el Producto a editar", list(dict_prods.keys()))
            cod_editar = dict_prods[prod_sel]
            datos_prod = supabase.table("productos_maestro").select("*").eq("codigo_producto", cod_editar).execute().data[0]
        else:
            datos_prod = {}

        with st.form("form_producto", clear_on_submit=False):
            col_a, col_b = st.columns(2)

            with col_a:
                codigo = st.text_input("Código de Producto", value=datos_prod.get("codigo_producto", ""), disabled=(modo == "Editar Producto Existente"))
                nombre = st.text_input("Nombre del Producto", value=datos_prod.get("nombre", ""))
                unidad = st.text_input("Unidad de Medida (ej. UND, KG)", value=datos_prod.get("unidad_medida", "UND"))
                marca_sel = st.selectbox("Marca", list(dict_marcas.keys()) if dict_marcas else ["N/A"])

            with col_b:
                precio = st.number_input("Precio de Venta ($)", min_value=0.0, value=float(datos_prod.get("precio_venta", 0.0)), step=0.5)
                stock = st.number_input("Cantidad en Stock", min_value=0, value=int(datos_prod.get("cantidad_stock", 0)), step=1)
                modelo_sel = st.selectbox("Modelo", list(dict_modelos.keys()) if dict_modelos else ["N/A"])
                tipo_sel = st.selectbox("Tipo de Producto", list(dict_tipos.keys()) if dict_tipos else ["N/A"])

            guardar = st.form_submit_button("💾 Guardar en Supabase")

            if guardar:
                if not codigo or not nombre:
                    st.warning("El código y el nombre son campos obligatorios.")
                else:
                    payload = {
                        "codigo_producto": codigo,
                        "nombre": nombre,
                        "unidad_medida": unidad,
                        "precio_venta": precio,
                        "cantidad_stock": stock,
                        "id_marca": dict_marcas.get(marca_sel),
                        "id_modelo": dict_modelos.get(modelo_sel),
                        "id_tipo": dict_tipos.get(tipo_sel)
                    }

                    try:
                        if modo == "Crear Nuevo Producto":
                            supabase.table("productos_maestro").insert(payload).execute()
                            st.success(f"¡Producto '{nombre}' creado exitosamente!")
                        else:
                            supabase.table("productos_maestro").update(payload).eq("codigo_producto", codigo).execute()
                            st.success(f"¡Producto '{nombre}' actualizado exitosamente!")
                        st.rerun()
                    except Exception as err:
                        st.error(f"Error al guardar en Supabase: {err}")

    # Tabla de Productos Actuales
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
# 5. VENTAS
# ---------------------------------------------------------
elif opcion == "💰 Ventas":
    st.title("💰 Salidas y Ventas a Clientes")
    st.divider()

    try:
        res = supabase.table("detalle_ventas").select("""
            cantidad, precio_unitario, subtotal,
            ventas(numero_factura, fecha, metodo_pago, clientes(nombre)),
            productos(codigo_producto, nombre)
