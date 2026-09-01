  
import streamlit as st
import pandas as pd
from supabase import create_client, Client

# Configuración de la página
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
    [
        "📊 Dashboard General", 
        "📦 Maestro de Productos", 
        "🏢 Productos en Almacén", 
        "📄 Órdenes de Compra", 
        "📥 Recepción Facturas (Compras)", 
        "💰 Ventas", 
        "🔄 Devoluciones"
    ]
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
            # Corregido a 'productos(nombre)' según esquema de tu DB
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
# 2. MAESTRO DE PRODUCTOS
# ---------------------------------------------------------
elif opcion == "📦 Maestro de Productos":
    st.title("📦 Catálogo Maestro de Productos")
    st.divider()

    try:
        marcas_data = supabase.table("marcas").select("id_marca, nombre_marca").execute().data
        modelos_data = supabase.table("modelos").select("id_modelo, nombre_modelo").execute().data
        tipos_data = supabase.table("tipos_producto").select("id_tipo, nombre_tipo").execute().data

        dict_marcas = {m["nombre_marca"]: m["id_marca"] for m in marcas_data} if marcas_data else {}
        dict_modelos = {m["nombre_modelo"]: m["id_modelo"] for m in modelos_data} if modelos_data else {}
        dict_tipos = {t["nombre_tipo"]: t["id_tipo"] for t in tipos_data} if tipos_data else {}
    except Exception as e:
        st.error(f"Error al obtener catálogos de apoyo: {e}")

    with st.expander("➕ Registrar / Editar Producto", expanded=False):
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

            guardar = st.form_submit_button("💾 Guardar Producto")

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
# 3. PRODUCTOS EN ALMACÉN
# ---------------------------------------------------------
elif opcion == "🏢 Productos en Almacén":
    st.title("🏢 Inventario Físico y Ubicaciones en Almacén")
    st.divider()

    try:
        res = supabase.table("productos_maestro").select("codigo_producto, nombre, cantidad_stock, unidad_medida, precio_venta").execute().data
        if res:
            df_alm = pd.DataFrame(res)
            df_alm["Valor Total ($)"] = df_alm["cantidad_stock"] * df_alm["precio_venta"]
            df_alm["Estado Stock"] = df_alm["cantidad_stock"].apply(
                lambda x: "🔴 CRÍTICO" if x <= 5 else ("🟡 BAJO" if x <= 15 else "🟢 OK")
            )
            st.dataframe(df_alm, use_container_width=True)
        else:
            st.info("No hay productos en almacén.")
    except Exception as e:
        st.error(f"Error al obtener productos de almacén: {e}")

# ---------------------------------------------------------
# 4. ÓRDENES DE COMPRA
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
# 5. RECEPCIÓN FACTURAS (COMPRAS)
# ---------------------------------------------------------
elif opcion == "📥 Recepción Facturas (Compras)":
    st.title("📥 Recepción de Productos y Compras")
    st.divider()

    try:
        prods_data = supabase.table("productos_maestro").select("codigo_producto, nombre, cantidad_stock").execute().data
        provs_data = supabase.table("proveedores").select("id_proveedor, nombre_empresa").execute().data
        ocs_data = supabase.table("ordenes_compra").select("id_orden, numero_orden").execute().data

        dict_prods_compra = {f"{p['codigo_producto']} - {p['nombre']}": (p['codigo_producto'], p.get('cantidad_stock', 0)) for p in prods_data} if prods_data else {}
        dict_provs = {p["nombre_empresa"]: p["id_proveedor"] for p in provs_data} if provs_data else {}
        dict_ocs = {str(o["numero_orden"]): o["id_orden"] for o in ocs_data} if ocs_data else {}
    except Exception as e:
        st.error(f"Error al cargar catálogos para compras: {e}")

    with st.expander("➕ Registrar Nueva Recepción / Compra", expanded=False):
        with st.form("form_compra", clear_on_submit=True):
            col_c1, col_c2 = st.columns(2)

            with col_c1:
                nro_factura = st.text_input("Número de Factura", value="F001-001")
                fecha_fact = st.date_input("Fecha de Factura")
                prod_compra_sel = st.selectbox("Producto Recibido", list(dict_prods_compra.keys()) if dict_prods_compra else ["N/A"])
                prov_sel = st.selectbox("Proveedor", list(dict_provs.keys()) if dict_provs else ["N/A"])

            with col_c2:
                cant_ingresada = st.number_input("Cantidad Ingresada", min_value=1, step=1, value=10)
                precio_compra = st.number_input("Precio de Compra Unitario ($)", min_value=0.0, step=0.5, value=25.0)
                oc_sel = st.selectbox("Órden de Compra Asociada", list(dict_ocs.keys()) if dict_ocs else ["N/A"])

            guardar_compra = st.form_submit_button("📥 Registrar Recepción e Incrementar Stock")

            if guardar_compra:
                if not nro_factura or prod_compra_sel == "N/A":
                    st.warning("El número de factura y el producto son obligatorios.")
                else:
                    cod_prod, stock_actual = dict_prods_compra[prod_compra_sel]
                    payload_compra = {
                        "numero_factura": nro_factura,
                        "fecha_factura": str(fecha_fact),
                        "cantidad_ingresada": cant_ingresada,
                        "precio_compra": precio_compra,
                        "codigo_producto": cod_prod,
                        "id_proveedor": dict_provs.get(prov_sel),
                        "id_orden": dict_ocs.get(oc_sel)
                    }

                    try:
                        supabase.table("recep_productos_factura").insert(payload_compra).execute()
                        nuevo_stock = stock_actual + cant_ingresada
                        supabase.table("productos_maestro").update({"cantidad_stock": nuevo_stock}).eq("codigo_producto", cod_prod).execute()

                        st.success(f"¡Recepción registrada! Stock de {cod_prod} actualizado a {nuevo_stock} unidades.")
                        st.rerun()
                    except Exception as err:
                        st.error(f"Error al registrar compra: {err}")

    st.subheader("📋 Tabla General de Compras / Recepciones")
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
# 6. VENTAS
# ---------------------------------------------------------
elif opcion == "💰 Ventas":
    st.title("💰 Salidas y Ventas a Clientes")
    st.divider()

    try:
        prods_data_v = supabase.table("productos_maestro").select("codigo_producto, nombre, precio_venta, cantidad_stock").execute().data
        clientes_data = supabase.table("clientes").select("id_cliente, nombre").execute().data

        dict_prods_venta = {f"{p['codigo_producto']} - {p['nombre']}": (p['codigo_producto'], float(p.get('precio_venta', 0.0)), int(p.get('cantidad_stock', 0))) for p in prods_data_v} if prods_data_v else {}
        dict_clientes = {c["nombre"]: c["id_cliente"] for c in clientes_data} if clientes_data else {}
    except Exception as e:
        st.error(f"Error al cargar catálogos para ventas: {e}")

    with st.expander("➕ Registrar Nueva Venta", expanded=False):
        with st.form("form_venta", clear_on_submit=True):
            col_v1, col_v2 = st.columns(2)

            with col_v1:
                nro_factura_v = st.text_input("Número de Factura / Boleta", value="V001-001")
                fecha_v = st.date_input("Fecha de Venta")
                cliente_sel = st.selectbox("Cliente", list(dict_clientes.keys()) if dict_clientes else ["N/A"])
                metodo_pago = st.selectbox("Método de Pago", ["Efectivo", "Tarjeta de Crédito/Débito", "Transferencia", "Crédito"])

            with col_v2:
                prod_venta_sel = st.selectbox("Producto a Vender", list(dict_prods_venta.keys()) if dict_prods_venta else ["N/A"])
                cant_vender = st.number_input("Cantidad a Vender", min_value=1, step=1, value=2)

            guardar_venta = st.form_submit_button("💰 Registrar Venta y Descontar Stock")

            if guardar_venta:
                if not nro_factura_v or prod_venta_sel == "N/A":
                    st.warning("El número de factura y el producto son obligatorios.")
                else:
                    cod_prod, precio_u, stock_actual = dict_prods_venta[prod_venta_sel]

                    if cant_vender > stock_actual:
                        st.error(f"Stock insuficiente. Quedan {stock_actual} unidades.")
                    else:
                        try:
                            res_venta = supabase.table("ventas").insert({
                                "numero_factura": nro_factura_v,
                                "fecha": str(fecha_v),
                                "id_cliente": dict_clientes.get(cliente_sel),
                                "metodo_pago": metodo_pago
                            }).execute().data

                            id_venta_gen = res_venta[0]["id_venta"] if res_venta else None
                            subtotal = cant_vender * precio_u

                            supabase.table("detalle_ventas").insert({
                                "id_venta": id_venta_gen,
                                "codigo_producto": cod_prod,
                                "cantidad": cant_vender,
                                "precio_unitario": precio_u,
                                "subtotal": subtotal
                            }).execute()

                            nuevo_stock = stock_actual - cant_vender
                            supabase.table("productos_maestro").update({"cantidad_stock": nuevo_stock}).eq("codigo_producto", cod_prod).execute()

                            st.success(f"¡Venta registrada! Nuevo stock de {cod_prod}: {nuevo_stock} unidades.")
                            st.rerun()
                        except Exception as err:
                            st.error(f"Error al registrar la venta: {err}")

    st.subheader("📋 Tabla General de Ventas")
    try:
        # Corregido a 'productos(codigo_producto, nombre)' según tu DB
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

# ---------------------------------------------------------
# 7. DEVOLUCIONES
# ---------------------------------------------------------
elif opcion == "🔄 Devoluciones":
    st.title("🔄 Registro y Control de Devoluciones")
    st.divider()

    try:
        prods_data_dev = supabase.table("productos_maestro").select("codigo_producto, nombre, cantidad_stock").execute().data
        dict_prods_dev = {f"{p['codigo_producto']} - {p['nombre']}": (p['codigo_producto'], p.get('cantidad_stock', 0)) for p in prods_data_dev} if prods_data_dev else {}
    except Exception as e:
        st.error(f"Error al cargar lista de productos: {e}")

    with st.expander("➕ Registrar Devolución de Producto", expanded=False):
        with st.form("form_devolucion", clear_on_submit=True):
            col_d1, col_d2 = st.columns(2)

            with col_d1:
                nro_factura_dev = st.text_input("N° Factura / Boleta Afectada")
                prod_dev_sel = st.selectbox("Producto Devuelto", list(dict_prods_dev.keys()) if dict_prods_dev else ["N/A"])
                tipo_devolucion = st.selectbox("Tipo de Devolución", ["Devolución de Cliente", "Devolución a Proveedor"])

            with col_d2:
                cant_dev = st.number_input("Cantidad Devuelta", min_value=1, step=1, value=1)
                motivo = st.text_area("Motivo de Devolución", value="Defecto de fábrica / Empaque dañado")

            guardar_dev = st.form_submit_button("🔄 Guardar Devolución")

            if guardar_dev:
                if not nro_factura_dev or prod_dev_sel == "N/A":
                    st.warning("El número de factura y el producto son obligatorios.")
                else:
                    cod_prod, stock_actual = dict_prods_dev[prod_dev_sel]
                    
                    # Ajuste de stock según tipo
                    if tipo_devolucion == "Devolución de Cliente":
                        nuevo_stock = stock_actual + cant_dev  # Vuelve al inventario
                    else:
                        nuevo_stock = max(0, stock_actual - cant_dev)  # Sale hacia el proveedor

                    try:
                        # Insertar registro de devolución
                        supabase.table("devoluciones").insert({
                            "numero_factura": nro_factura_dev,
                            "codigo_producto": cod_prod,
                            "cantidad": cant_dev,
                            "tipo_devolucion": tipo_devolucion,
                            "motivo": motivo
                        }).execute()

                        # Actualizar stock
                        supabase.table("productos_maestro").update({"cantidad_stock": nuevo_stock}).eq("codigo_producto", cod_prod).execute()

                        st.success(f"¡Devolución registrada! Stock ajustado a {nuevo_stock} unidades.")
                        st.rerun()
                    except Exception as err:
                        st.error(f"Error al registrar devolución en Supabase: {err}")

    st.subheader("📋 Tabla General de Devoluciones")
    try:
        res = supabase.table("devoluciones").select("*").execute().data
        if res:
            st.dataframe(res, use_container_width=True)
        else:
            st.info("No hay devoluciones registradas.")
    except Exception as e:
        st.error(f"Error al consultar devoluciones: {e}")
