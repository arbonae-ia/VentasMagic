import io
import re
from datetime import datetime

import gspread
import numpy as np
import pandas as pd
import pdfplumber
import plotly.express as px
import streamlit as st
from google.oauth2.service_account import Credentials

# -----------------------------------------------------------------------------
# CONFIGURACIÓN DE LA PÁGINA Y ESTILOS VISUALES (UI/UX)
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Magic Print | Analytics", page_icon="logo.jpg", layout="wide", initial_sidebar_state="collapsed")
try:
    st.set_option("client.toolbarMode", "minimal")
except Exception:
    pass

st.markdown("""
<style>
/* Sistema visual inspirado en el dashboard de visitas comerciales */
html, body, [class*="css"] { font-family: "Arial Narrow", Arial, sans-serif; }
.stApp { background: #f1f3f5; color: #17245f; }
.stSidebar { background:#ffffff; }
.block-container { max-width: 1180px; padding-top: 2.8rem; padding-bottom: 3rem; }
[data-testid="stVerticalBlockBorderWrapper"] { background:#ffffff; border:1.5px solid #22286d !important; border-radius:9px; padding:5px 10px !important; }
[data-testid="stVerticalBlockBorderWrapper"] > div { background:#ffffff; border-radius:9px; }
.stSubheader, [data-testid="stMarkdownContainer"] h3 { font-size:1.05rem !important; color:#17245f; }
.stSubheader { margin:0 0 .1rem !important; }
.data-status { color:#7a8495; font-family:"Arial Narrow", Arial, sans-serif; font-size:10px; font-style:italic; line-height:1.25; margin:2px 0 4px; }
.filter-summary { background:#ffffff; border:1px solid #d7dce4; border-left:4px solid #22286d; border-radius:6px; color:#5f6b80; font-size:11px; line-height:1.45; margin:12px 0 4px; padding:7px 10px; }
.filter-summary strong { color:#17245f; }
.brand-header { background: #fff; border-top: 3px solid #22286d; border-radius: 0 0 8px 8px; padding: 16px 24px; margin-bottom: 16px; box-shadow: 0 1px 5px rgba(20,35,70,.08); display:flex; align-items:center; gap:16px; }
.brand-header img { width:64px; height:64px; object-fit:cover; border-radius:12px; }
.main-title { color:#17245f; font-size:27px; font-weight:700; margin:0; }
.main-subtitle { color:#68738b; font-size:13px; margin-top:4px; }
.section-title { color:#17245f; font-size:17px; font-weight:700; margin:18px 0 10px; }
.panel { background:#fff; border:1px solid #d4d9df; border-radius:9px; padding:14px 16px; }
.kpi-card { background:#fff; border:1px solid #dce1e7; border-top:4px solid #22286d; border-radius:8px; padding:13px 15px; min-height:98px; box-shadow:0 2px 5px rgba(24,38,72,.05); overflow:hidden; }
.kpi-card.blue { border-top-color:#22286d; } .kpi-card.green { border-top-color:#008d68; } .kpi-card.purple { border-top-color:#7755c9; } .kpi-card.orange { border-top-color:#f28b30; } .kpi-card.cyan { border-top-color:#13b9dc; }
.kpi-title { color:#65728a; font-size:10px; font-weight:600; text-transform:uppercase; letter-spacing:.2px; line-height:1.2; }
.kpi-value { color:#17245f; font-size:clamp(20px, 1.55vw, 25px); line-height:1.08; font-weight:700; margin-top:7px; white-space:normal; overflow-wrap:anywhere; }
.kpi-row-gap { height:14px; }
.small-note { color:#68738b; font-size:11px; margin-top:3px; }
.mini-badge { display:inline-block; padding:4px 8px; border-radius:5px; background:#eef1fb; color:#22286d; font-size:10px; font-weight:700; }
.stButton > button { border-radius:6px; border-color:#cbd2dc; color:#17245f; }
.stButton > button[kind="primary"] { background:#22286d; color:#fff; border-color:#22286d; }
.stDataFrame { border:1px solid #dce1e7; }
#MainMenu, footer { visibility:hidden; }

/* Ocultar elementos predeterminados de Streamlit */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

NOMBRE_ARCHIVO = "Base_Datos_Ventas"
NOMBRE_PESTANA = "Hoja1"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

COLUMNAS = [
    "Factura #", "Fecha", "Cliente", "Nit", "Ciudad", "Vendedor",
    "Codigo Articulo", "Descripcion", "Unidad", "Cantidad",
    "Precio Unitario", "Valor Total", "% IVA", "Forma de Pago",
    "Tipo de Venta"
]

MESES_PDF = {
    "JAN": "01", "FEB": "02", "MAR": "03", "APR": "04",
    "MAY": "05", "JUN": "06", "JUL": "07", "AUG": "08",
    "SEP": "09", "OCT": "10", "NOV": "11", "DEC": "12"
}

CODIGOS_SERVICIO = {"888912", "888923", "888916"}

# -----------------------------------------------------------------------------
# FUNCIONES DE CONEXIÓN Y ETL
# -----------------------------------------------------------------------------
@st.cache_resource
def conectar_hoja():
    try:
        credenciales = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"], scopes=SCOPES
        )
        cliente = gspread.authorize(credenciales)
        return cliente.open(NOMBRE_ARCHIVO).worksheet(NOMBRE_PESTANA)
    except Exception as error:
        st.error(f"No fue posible conectar con Google Sheets: {error}")
        return None

def limpiar_texto(valor):
    if valor is None:
        return ""
    return re.sub(r"\s+", " ", str(valor).replace("\xa0", " ")).strip()

def limpiar_nit(valor):
    return re.sub(r"[^0-9]", "", limpiar_texto(valor))

def convertir_numero(valor):
    texto = limpiar_texto(valor).replace("$", "").replace(" ", "")
    if not texto:
        return 0.0
    try:
        if "," in texto and "." in texto:
            texto = (texto.replace(".", "").replace(",", ".")
                     if texto.rfind(",") > texto.rfind(".")
                     else texto.replace(",", ""))
        elif "," in texto:
            partes = texto.split(",")
            texto = (texto.replace(".", "").replace(",", ".")
                     if len(partes[-1]) <= 2 else texto.replace(",", ""))
        elif "." in texto:
            partes = texto.split(".")
            # Un punto seguido de 1 o 2 dígitos representa decimales
            # (por ejemplo, 0.5 o 47.5). Con 3 dígitos representa miles
            # (por ejemplo, 12.170).
            texto = texto if len(partes[-1]) <= 2 else texto.replace(".", "")
        return float(texto)
    except Exception:
        return 0.0

def convertir_fecha_pdf(fecha):
    partes = limpiar_texto(fecha).replace("−", "-").replace("–", "-").split("-")
    if len(partes) != 3:
        return ""
    try:
        mes = MESES_PDF.get(partes[1].upper(), partes[1])
        return datetime.strptime(
            f"{partes[0]}-{mes}-{partes[2].zfill(2)}", "%Y-%m-%d"
        ).strftime("%Y-%m-%d")
    except Exception:
        return ""

def clasificar_tipo_venta(codigo):
    return "Servicio" if limpiar_texto(codigo) in CODIGOS_SERVICIO else "Bases Textiles"

def extraer_datos_pdf(archivo_pdf):
    registros = []
    contenido = archivo_pdf.read()
    if not contenido:
        raise ValueError("El archivo PDF está vacío.")

    patron_linea = re.compile(
        r"^\s*\|?\s*(\d{3,10})\s+(.+?)\s+"
        r"(\d+(?:[.,]\d+)?)\s+(\d+(?:[.,]\d+)?)\s+"
        r"(MTS|KLS|UND|UN|KG|KGM|SERV|UNIDAD)\s+"
        r"([\d.,]+)\s+([\d.,]+)\s+([\d.,]+)\s+([\d.,]+)"
        r"\s*\*?\|?\s*$", re.I | re.M
    )

    with pdfplumber.open(io.BytesIO(contenido)) as pdf:
        for pagina in pdf.pages:
            texto = (pagina.extract_text() or "").replace("−", "-").replace("–", "-")
            if not texto.strip():
                continue

            factura_match = re.search(r"Numero\s*:\s*([A-Z]+-\d+)", texto, re.I)
            factura_match = factura_match or re.search(r"\b(FM-\d+)\b", texto, re.I)
            if not factura_match:
                continue

            factura = factura_match.group(1).upper()
            fecha_match = re.search(r"Fecha\s*:\s*(\d{4}-[A-Z]{3}-\d{2})", texto, re.I)
            cliente_match = re.search(r"Cliente\s*:\s*(.*?)\s*\|", texto, re.I)
            nit_match = re.search(r"Nit\s+o\s+C\.C\.\s*:\s*([0-9.\-]+)", texto, re.I)
            ciudad_match = re.search(r"Ciudad\s*:\s*([A-ZÁÉÍÓÚÑ ]+)", texto, re.I)
            vendedor_match = re.search(r"Vendedor\s*:\s*(?:\d+\s+)?(.*?)\s*\|", texto, re.I)
            pago_match = re.search(r"\|\s*(CREDITO\s+\d+\s+DIAS?|CONTADO)\s*\|", texto, re.I)

            fecha = convertir_fecha_pdf(fecha_match.group(1)) if fecha_match else ""
            cliente = limpiar_texto(cliente_match.group(1)) if cliente_match else ""
            nit = limpiar_nit(nit_match.group(1)) if nit_match else ""
            ciudad = limpiar_texto(ciudad_match.group(1)) if ciudad_match else ""
            vendedor = limpiar_texto(vendedor_match.group(1)) if vendedor_match else ""
            forma_pago = limpiar_texto(pago_match.group(1)) if pago_match else ""

            for linea in patron_linea.findall(texto):
                codigo, descripcion, piezas, cantidad, unidad, precio, descuento, total, iva = linea
                total = convertir_numero(total)
                if not codigo or total == 0:
                    continue
                registros.append([
                    factura, fecha, cliente, nit, ciudad, vendedor,
                    limpiar_texto(codigo), limpiar_texto(descripcion),
                    limpiar_texto(unidad).upper(), convertir_numero(cantidad),
                    convertir_numero(precio), total, convertir_numero(iva),
                    forma_pago, clasificar_tipo_venta(codigo)
                ])

    if not registros:
        raise ValueError("No se encontraron líneas de productos o servicios.")
    return registros

def obtener_informacion_duplicados(hoja, registros_pdf):
    datos = hoja.get_all_values()
    facturas_pdf = {limpiar_texto(r[0]) for r in registros_pdf}
    if len(datos) < 2:
        return {"facturas_existentes": set(), "filas_a_borrar": [], "facturas_nuevas": facturas_pdf}

    encabezados = [limpiar_texto(x) for x in datos[0]]
    if "Factura #" not in encabezados:
        raise ValueError("No existe la columna 'Factura #' en Google Sheets.")
    posicion = encabezados.index("Factura #")
    existentes, filas = set(), []
    for numero_fila, fila in enumerate(datos[1:], start=2):
        if len(fila) > posicion and limpiar_texto(fila[posicion]) in facturas_pdf:
            existentes.add(limpiar_texto(fila[posicion]))
            filas.append(numero_fila)
    return {
        "facturas_existentes": existentes,
        "filas_a_borrar": filas,
        "facturas_nuevas": facturas_pdf - existentes,
    }

def agregar_facturas_nuevas(hoja, registros_pdf, facturas_existentes):
    nuevos = [r for r in registros_pdf if limpiar_texto(r[0]) not in facturas_existentes]
    if nuevos:
        hoja.append_rows(nuevos, value_input_option="USER_ENTERED")
    return nuevos

def reemplazar_facturas(hoja, registros_pdf, filas_a_borrar):
    for fila in sorted(filas_a_borrar, reverse=True):
        hoja.delete_rows(fila)
    hoja.append_rows(registros_pdf, value_input_option="USER_ENTERED")

@st.cache_data(ttl=30)
def cargar_datos():
    hoja = conectar_hoja()
    datos = hoja.get_all_values()
    if not datos:
        return pd.DataFrame(columns=COLUMNAS)

    encabezados = [limpiar_texto(x) for x in datos[0]]
    if len(datos) == 1:
        return pd.DataFrame(columns=encabezados)

    filas = []
    for fila in datos[1:]:
        fila = list(fila)
        fila.extend([""] * (len(encabezados) - len(fila)))
        filas.append(fila[:len(encabezados)])
    df = pd.DataFrame(filas, columns=encabezados)

    for columna in ["Cantidad", "Precio Unitario", "Valor Total", "% IVA"]:
        if columna in df.columns:
            df[columna] = df[columna].apply(convertir_numero)
    if "Fecha" in df.columns:
        df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
    if "Codigo Articulo" in df.columns:
        df["Codigo Articulo"] = (df["Codigo Articulo"].astype(str)
                                  .str.replace(".0", "", regex=False).str.strip())
        df["Tipo de Venta"] = df["Codigo Articulo"].apply(clasificar_tipo_venta)
    return df

# -----------------------------------------------------------------------------
# ESTADOS DE SESIÓN (Inicialización segura)
# -----------------------------------------------------------------------------
if "registros_pdf" not in st.session_state:
    st.session_state["registros_pdf"] = None
if "mensaje_carga" not in st.session_state:
    st.session_state["mensaje_carga"] = ""
if "uploader_version" not in st.session_state:
    st.session_state["uploader_version"] = 0

# -----------------------------------------------------------------------------
# ENCABEZADO PRINCIPAL CON LOGOTIPO
# -----------------------------------------------------------------------------
col_izq, col_der = st.columns([8, 1])
with col_izq:
    st.markdown("""
        <div class="main-title">Magic Print Analytics</div>
        <div class="main-subtitle">Seguimiento de ventas, facturación y desempeño comercial</div>
    """, unsafe_allow_html=True)
with col_der:
    st.image("logo.jpg", width=64)

if st.session_state.get("mensaje_carga"):
    st.success(st.session_state.pop("mensaje_carga"))

hoja = conectar_hoja()
if hoja is None:
    st.stop()

# -----------------------------------------------------------------------------
# CARGA DE PDF EN LA BARRA LATERAL Y FILTROS DE ANÁLISIS
# -----------------------------------------------------------------------------
df_full = cargar_datos()

if not df_full.empty and "Fecha" in df_full.columns and df_full["Fecha"].notna().any():
    indice_ultima_factura = df_full["Fecha"].idxmax()
    fecha_ultima_factura = df_full.loc[indice_ultima_factura, "Fecha"].strftime("%d/%m/%Y")
    numero_ultima_factura = str(df_full.loc[indice_ultima_factura, "Factura #"]) if "Factura #" in df_full.columns else "No disponible"
    total_facturas_registradas = df_full["Factura #"].nunique() if "Factura #" in df_full.columns else 0
    estado_carga = f"Última factura registrada: {numero_ultima_factura} · {fecha_ultima_factura} · {total_facturas_registradas:,} facturas en total"
else:
    estado_carga = "Aún no hay facturas registradas en la base de datos"

with st.sidebar:
    st.subheader("📤 Cargar facturas PDF")
    st.markdown(f'<div class="data-status">{estado_carga}</div>', unsafe_allow_html=True)
    archivo_pdf = st.file_uploader(
        "Selecciona un archivo PDF",
        type=["pdf"],
        key=f"archivo_pdf_{st.session_state['uploader_version']}"
    )
    if archivo_pdf:
        st.success(f"Archivo seleccionado: {archivo_pdf.name}")
        if st.button("Procesar PDF", type="primary", use_container_width=True):
            try:
                with st.spinner("Procesando el PDF..."):
                    st.session_state["registros_pdf"] = extraer_datos_pdf(archivo_pdf)
                st.rerun()
            except Exception as error:
                st.error("El PDF no corresponde a una factura válida o está vacío.")

with st.container(border=True):
    st.subheader("🔍 Filtros de análisis")
    ciudades_opc = sorted(df_full["Ciudad"].dropna().astype(str).unique()) if "Ciudad" in df_full.columns else []
    vendedores_opc = sorted(df_full["Vendedor"].dropna().astype(str).unique()) if "Vendedor" in df_full.columns else []
    clientes_opc = sorted(df_full["Cliente"].dropna().astype(str).unique()) if "Cliente" in df_full.columns else []
    tipos_venta_opc = sorted(df_full["Tipo de Venta"].dropna().astype(str).unique()) if "Tipo de Venta" in df_full.columns else []
    sel_ciudades, sel_vendedores, sel_clientes, sel_tipo_venta = [], [], [], []

    opciones_filtro = [("Ciudad", ciudades_opc), ("Vendedor", vendedores_opc), ("Cliente", clientes_opc), ("Tipo de venta", tipos_venta_opc)]
    filtros_visibles = [(nombre, opciones) for nombre, opciones in opciones_filtro if opciones]
    columnas_filtros = st.columns(1 + len(filtros_visibles))
    if not df_full.empty and "Fecha" in df_full.columns and not df_full["Fecha"].dropna().empty:
        f_min = df_full["Fecha"].min().date()
        f_max = df_full["Fecha"].max().date()
        with columnas_filtros[0]:
            rango_fechas = st.date_input("Rango de fechas", (f_min, f_max), min_value=f_min, max_value=f_max)
    else:
        rango_fechas = None

    for posicion, (nombre, opciones) in enumerate(filtros_visibles, start=1):
        with columnas_filtros[posicion]:
            seleccion = st.multiselect(nombre, opciones)
            if nombre == "Ciudad":
                sel_ciudades = seleccion
            elif nombre == "Vendedor":
                sel_vendedores = seleccion
            elif nombre == "Cliente":
                sel_clientes = seleccion
            elif nombre == "Tipo de venta":
                sel_tipo_venta = seleccion

# Aplicar filtros al DataFrame
df = df_full.copy()
if df.empty:
    st.info("Google Sheets está conectado, pero todavía no contiene registros.")

if isinstance(rango_fechas, tuple) and len(rango_fechas) == 2:
    df = df[(df["Fecha"].dt.date >= rango_fechas[0]) & (df["Fecha"].dt.date <= rango_fechas[1])]
if sel_ciudades:
    df = df[df["Ciudad"].astype(str).isin(sel_ciudades)]
if sel_vendedores:
    df = df[df["Vendedor"].astype(str).isin(sel_vendedores)]
if sel_clientes:
    df = df[df["Cliente"].astype(str).isin(sel_clientes)]
if sel_tipo_venta:
    df = df[df["Tipo de Venta"].astype(str).isin(sel_tipo_venta)]

periodo_resumen = "Todos los periodos"
if isinstance(rango_fechas, (tuple, list)) and len(rango_fechas) == 2:
    periodo_resumen = f"{rango_fechas[0].strftime('%d/%m/%Y')} – {rango_fechas[1].strftime('%d/%m/%Y')}"
ciudad_resumen = ", ".join(sel_ciudades) if sel_ciudades else "Todas"
vendedor_resumen = ", ".join(sel_vendedores) if sel_vendedores else "Todos"
cliente_resumen = ", ".join(sel_clientes) if sel_clientes else "Todos"
tipo_resumen = ", ".join(sel_tipo_venta) if sel_tipo_venta else "Todos"
st.markdown(
    f'<div class="filter-summary"><strong>Analizando:</strong> Periodo: {periodo_resumen} &nbsp;·&nbsp; '
    f'Ciudad: {ciudad_resumen} &nbsp;·&nbsp; Vendedor: {vendedor_resumen} &nbsp;·&nbsp; '
    f'Cliente: {cliente_resumen} &nbsp;·&nbsp; Tipo de venta: {tipo_resumen}</div>',
    unsafe_allow_html=True
)

# -----------------------------------------------------------------------------
# GESTIÓN DE VISTA PREVIA Y CARGA A GOOGLE SHEETS
# -----------------------------------------------------------------------------
registros_pdf = st.session_state["registros_pdf"]
if registros_pdf:
    st.markdown('<div class="section-title">📦 Vista previa del PDF</div>', unsafe_allow_html=True)
    df_pdf = pd.DataFrame(registros_pdf, columns=COLUMNAS)
    st.caption(f"Se encontraron {len(df_pdf)} líneas de {df_pdf['Factura #'].nunique()} facturas.")
    st.dataframe(df_pdf, use_container_width=True, hide_index=True)

    informacion = obtener_informacion_duplicados(hoja, registros_pdf)
    repetidas = sorted(informacion["facturas_existentes"])
    nuevas = sorted(informacion["facturas_nuevas"])

    if repetidas:
        st.warning(f"El PDF contiene {len(repetidas)} facturas ya cargadas.")
        c1, c2, c3 = st.columns(3)
        c1.metric("Facturas repetidas", len(repetidas))
        c2.metric("Líneas repetidas", len(informacion["filas_a_borrar"]))
        c3.metric("Facturas nuevas", len(nuevas))
        with st.expander("Ver facturas repetidas"):
            st.write(", ".join(repetidas))

        if st.button("No cargar este archivo", key="cancelar_archivo_repetido", use_container_width=True):
            st.session_state["registros_pdf"] = None
            st.session_state["uploader_version"] += 1
            st.rerun()

        confirmar = st.checkbox("Confirmo que deseo reemplazar las facturas repetidas.")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Cargar solo facturas nuevas", disabled=not nuevas, use_container_width=True):
                try:
                    with st.spinner("Cargando facturas nuevas..."):
                        agregar_facturas_nuevas(hoja, registros_pdf, informacion["facturas_existentes"])
                    st.cache_data.clear()
                    st.session_state["registros_pdf"] = None
                    st.session_state["mensaje_carga"] = f"Se cargaron {len(nuevas)} facturas nuevas correctamente."
                    st.rerun()
                except Exception as error:
                    st.error(f"Error: {error}")
        with c2:
            if st.button("Reemplazar facturas repetidas", type="primary", disabled=not confirmar, use_container_width=True):
                try:
                    with st.spinner("Reemplazando facturas repetidas..."):
                        reemplazar_facturas(hoja, registros_pdf, informacion["filas_a_borrar"])
                    st.cache_data.clear()
                    st.session_state["registros_pdf"] = None
                    st.session_state["mensaje_carga"] = f"Se reemplazaron {len(repetidas)} facturas correctamente."
                    st.rerun()
                except Exception as error:
                    st.error(f"Error: {error}")
    else:
        st.success("No se encontraron facturas repetidas. Todas son nuevas.")
        if st.button("Cargar facturas en Google Sheets", type="primary", use_container_width=True):
            try:
                with st.spinner("Cargando facturas..."):
                    hoja.append_rows(registros_pdf, value_input_option="USER_ENTERED")
                st.cache_data.clear()
                st.session_state["registros_pdf"] = None
                st.session_state["mensaje_carga"] = "Las facturas fueron cargadas correctamente."
                st.rerun()
            except Exception as error:
                st.error(f"Error: {error}")

if df.empty:
    st.stop()

# -----------------------------------------------------------------------------
# CÁLCULOS DE MÉTRICAS Y KPIS
# -----------------------------------------------------------------------------
ventas = df["Valor Total"].sum()
facturas = df["Factura #"].nunique()
clientes = df["Cliente"].nunique()
cantidad = df["Cantidad"].sum()
ticket = ventas / facturas if facturas else 0
unidades = df["Unidad"].fillna("").astype(str).str.upper().str.strip() if "Unidad" in df.columns else pd.Series(dtype=str)
cantidad_metros = df.loc[unidades.isin({"MTS", "MT", "M"}), "Cantidad"].sum() if not unidades.empty else 0
cantidad_kilos = df.loc[unidades.isin({"KLS", "KG", "KGM", "KILO", "KILOS"}), "Cantidad"].sum() if not unidades.empty else 0
forma_pago_principal = df["Forma de Pago"].fillna("Sin dato").replace("", "Sin dato").value_counts().index[0] if "Forma de Pago" in df.columns and not df.empty else "Sin dato"
tipo_venta_principal = df["Tipo de Venta"].fillna("Sin dato").replace("", "Sin dato").value_counts().index[0] if "Tipo de Venta" in df.columns and not df.empty else "Sin dato"
if "Forma de Pago" in df.columns and not df.empty:
    valores_por_forma_pago = df.assign(_forma_pago=df["Forma de Pago"].fillna("Sin dato").replace("", "Sin dato")).groupby("_forma_pago")["Valor Total"].sum().sort_values(ascending=False)
    forma_pago_principal = valores_por_forma_pago.index[0]
    forma_pago_porcentaje = valores_por_forma_pago.iloc[0] / ventas * 100 if ventas else 0
else:
    forma_pago_porcentaje = 0
if "Tipo de Venta" in df.columns and not df.empty:
    valores_por_tipo_venta = df.assign(_tipo_venta=df["Tipo de Venta"].fillna("Sin dato").replace("", "Sin dato")).groupby("_tipo_venta")["Valor Total"].sum().sort_values(ascending=False)
    tipo_venta_principal = valores_por_tipo_venta.index[0]
    tipo_venta_porcentaje = valores_por_tipo_venta.iloc[0] / ventas * 100 if ventas else 0
else:
    tipo_venta_porcentaje = 0

ventas_dia = df.groupby("Fecha", as_index=False)["Valor Total"].sum().dropna()
if ventas_dia.empty:
    dia_mayor, valor_mayor, dia_menor, valor_menor = "Sin datos", 0, "Sin datos", 0
else:
    mayor = ventas_dia.loc[ventas_dia["Valor Total"].idxmax()]
    menor = ventas_dia.loc[ventas_dia["Valor Total"].idxmin()]
    dia_mayor, valor_mayor = mayor["Fecha"].strftime("%d/%m/%Y"), mayor["Valor Total"]
    dia_menor, valor_menor = menor["Fecha"].strftime("%d/%m/%Y"), menor["Valor Total"]

# -----------------------------------------------------------------------------
# RENDERIZADO DE INDICADORES COMERCIALES (KPI CARDS UNIFORMES)
# -----------------------------------------------------------------------------
st.markdown('<div class="section-title">📊 Indicadores comerciales</div>', unsafe_allow_html=True)
kpis = [
    ("Ventas sin IVA", f"${ventas:,.0f}", "blue"),
    ("Facturas realizadas", f"{facturas:,.0f}", "green"),
    ("Clientes atendidos", f"{clientes:,.0f}", "purple"),
    ("Metros vendidos", f"{cantidad_metros:,.2f} m", "orange"),
    ("Kilos vendidos", f"{cantidad_kilos:,.2f} kg", "cyan"),
    ("Ticket promedio", f"${ticket:,.0f}", "blue"),
]
cols = st.columns(6, gap="small")
for col, (titulo, valor, color) in zip(cols, kpis):
    with col:
        st.markdown(f'<div class="kpi-card {color}"><div class="kpi-title">{titulo}</div><div class="kpi-value">{valor}</div></div>', unsafe_allow_html=True)

st.markdown('<div class="kpi-row-gap"></div>', unsafe_allow_html=True)
cols_extra = st.columns(4, gap="medium")
with cols_extra[0]:
    st.markdown(f'<div class="kpi-card cyan"><div class="kpi-title">Forma de pago dominante</div><div class="kpi-value">{forma_pago_principal}</div><div class="small-note">{forma_pago_porcentaje:.1f}% del valor vendido</div></div>', unsafe_allow_html=True)
with cols_extra[1]:
    st.markdown(f'<div class="kpi-card purple"><div class="kpi-title">Tipo de venta dominante</div><div class="kpi-value">{tipo_venta_principal}</div><div class="small-note">{tipo_venta_porcentaje:.1f}% del valor vendido</div></div>', unsafe_allow_html=True)

with cols_extra[2]:
    st.markdown(f'<div class="kpi-card green"><div class="kpi-title">Día de mayor venta</div><div class="kpi-value">{dia_mayor}</div><div class="small-note">${valor_mayor:,.0f} vendidos</div></div>', unsafe_allow_html=True)
with cols_extra[3]:
    st.markdown(f'<div class="kpi-card orange"><div class="kpi-title">Día de menor venta</div><div class="kpi-value">{dia_menor}</div><div class="small-note">${valor_menor:,.0f} vendidos</div></div>', unsafe_allow_html=True)

def mostrar_grafico(figura):
    figura.update_layout(
        height=320,
        margin=dict(l=12, r=12, t=42, b=18),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="#ffffff",
        font=dict(family="Arial Narrow, Arial, sans-serif", size=11, color="#44516d"),
        title=dict(font=dict(size=15, color="#17245f"), x=0.02, xanchor="left"),
        showlegend=False,
        xaxis=dict(showgrid=False, zeroline=False, linecolor="#d8dee7"),
        yaxis=dict(showgrid=True, gridcolor="#edf0f4", zeroline=False, linecolor="#d8dee7")
    )
    figura.update_xaxes(title_text=None)
    figura.update_yaxes(title_text=None)
    st.plotly_chart(figura, use_container_width=True)

# -----------------------------------------------------------------------------
# BLOQUE DE GRÁFICOS Y ANÁLISIS COMERCIAL
# -----------------------------------------------------------------------------
st.markdown('<div class="section-title">📈 Análisis comercial detallado</div>', unsafe_allow_html=True)

c1, c2 = st.columns(2)
with c1:
    with st.container(border=True):
        datos = df.groupby("Fecha", as_index=False)["Valor Total"].sum().sort_values("Fecha")
        datos["Ventas (miles)"] = datos["Valor Total"] / 1000
        figura = px.line(
            datos,
            x="Fecha",
            y="Ventas (miles)",
            markers=True,
            title="Evolución diaria de ventas",
            color_discrete_sequence=["#008d68"]
        )
        figura.update_traces(line=dict(width=3), marker=dict(size=7))
        figura.update_xaxes(tickformat="%d/%m", title_text="")
        figura.update_yaxes(tickformat="$,.0f", ticksuffix=" mil", title_text="")
        mostrar_grafico(figura)
with c2:
    with st.container(border=True):
        datos = df.groupby("Ciudad", as_index=False)["Valor Total"].sum().sort_values("Valor Total", ascending=False).head(10)
        datos["Ventas (miles)"] = datos["Valor Total"] / 1000
        datos["Etiqueta"] = datos["Ventas (miles)"].map(lambda valor: f"${valor:,.0f} mil")
        figura = px.bar(
            datos,
            x="Ventas (miles)",
            y="Ciudad",
            orientation="h",
            title="Top 10 ciudades por ventas",
            text="Etiqueta",
            color_discrete_sequence=["#08b7d8"]
        )
        figura.update_traces(width=0.55)
        figura.update_layout(margin=dict(l=125, r=115, t=42, b=18))
        figura.update_xaxes(tickformat="$,.0f", ticksuffix=" mil", title_text=None)
        figura.update_yaxes(categoryorder="total ascending", title_text=None)
        mostrar_grafico(figura)

c1, c2 = st.columns(2)
with c1:
    with st.container(border=True):
        datos = df.groupby("Vendedor", as_index=False)["Valor Total"].sum().sort_values("Valor Total", ascending=False)
        datos["Ventas (miles)"] = datos["Valor Total"] / 1000
        figura = px.bar(datos, x="Ventas (miles)", y="Vendedor", orientation="h", title="Desempeño por vendedor", color_discrete_sequence=["#22286d"])
        figura.update_traces(width=0.55)
        figura.update_xaxes(tickformat="$,.0f", ticksuffix=" mil", title_text=None)
        mostrar_grafico(figura)
with c2:
    with st.container(border=True):
        datos = df.groupby("Descripcion", as_index=False)["Valor Total"].sum().sort_values("Valor Total", ascending=False).head(10)
        datos["Ventas (miles)"] = datos["Valor Total"] / 1000
        datos["Etiqueta"] = datos["Ventas (miles)"].map(lambda valor: f"${valor:,.0f} mil")
        figura = px.bar(datos, x="Ventas (miles)", y="Descripcion", orientation="h", title="Top 10 artículos más vendidos", text="Etiqueta", color_discrete_sequence=["#7755c9"])
        figura.update_traces(width=0.55)
        figura.update_layout(margin=dict(l=145, r=115, t=42, b=18))
        figura.update_xaxes(tickformat="$,.0f", ticksuffix=" mil", title_text=None)
        figura.update_yaxes(categoryorder="total ascending", title_text=None)
        mostrar_grafico(figura)

# -----------------------------------------------------------------------------
# TABLA DE DETALLE
# -----------------------------------------------------------------------------
st.markdown('<div class="section-title">📋 Detalle de facturación</div>', unsafe_allow_html=True)
with st.container(border=True):
    st.dataframe(df, use_container_width=True, hide_index=True)
