import base64
import io
import re
from html import escape
from pathlib import Path
from datetime import datetime

import gspread
import numpy as np
import pandas as pd
import pdfplumber
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from google.oauth2.service_account import Credentials
from PIL import Image

# -----------------------------------------------------------------------------
# CONFIGURACIÓN DE LA PÁGINA Y ESTILOS VISUALES (UI/UX)
# -----------------------------------------------------------------------------
LOGO_RESPALDO = "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"


def _logo_b64():
    """Lee logo.jpg junto al app.py; si no existe, usa el logo incrustado."""
    try:
        return base64.b64encode((Path(__file__).parent / "logo.jpg").read_bytes()).decode()
    except Exception:
        return LOGO_RESPALDO


LOGO_B64 = _logo_b64()


def _icono():
    try:
        return Image.open(io.BytesIO(base64.b64decode(LOGO_B64)))
    except Exception:
        return "📊"


def fnum(valor, decimales=0):
    """Formato colombiano: punto para miles y coma para decimales."""
    return f"{valor:,.{decimales}f}".replace(",", "#").replace(".", ",").replace("#", ".")


def cop(valor):
    return "$" + fnum(valor)


st.set_page_config(page_title="Magic Print | Analytics", page_icon=_icono(), layout="wide", initial_sidebar_state="collapsed")
try:
    st.set_option("client.toolbarMode", "minimal")
except Exception:
    pass

st.markdown("""
<style>
/* Sistema visual inspirado en el dashboard de visitas comerciales */
.stApp { font-family: "Source Sans Pro", "Source Sans 3", sans-serif; }
.stApp { background: #F4F7F9; color: #2D2D2D; }
.stSidebar { background:#ffffff; }
.block-container { max-width: 1180px; padding-top: 2.8rem; padding-bottom: 3rem; }
[data-testid="stVerticalBlockBorderWrapper"] { background:#ffffff; border:1px solid #e1e6ec !important; border-radius:10px; padding:8px 12px !important; box-shadow:0 2px 8px rgba(28,35,99,.06); }
[data-testid="stVerticalBlockBorderWrapper"] > div { background:#ffffff; border-radius:9px; }
.stSubheader, [data-testid="stMarkdownContainer"] h3 { font-size:1.05rem !important; color:#17245f; }
.stSubheader { margin:0 0 .1rem !important; }
.data-status { color:#7a8495; font-size:10px; font-style:italic; line-height:1.25; margin:2px 0 4px; }
.filter-summary { background:#ffffff; border:1px solid #d7dce4; border-left:4px solid #22286d; border-radius:6px; color:#5f6b80; font-size:11px; line-height:1.45; margin:12px 0 4px; padding:7px 10px; }
.filter-summary strong { color:#17245f; }
.brand-header { background: #fff; border-top: 3px solid #22286d; border-radius: 0 0 8px 8px; padding: 16px 24px; margin-bottom: 16px; box-shadow: 0 1px 5px rgba(20,35,70,.08); display:flex; align-items:center; gap:16px; }
.brand-header img { width:64px; height:64px; object-fit:cover; border-radius:12px; }
.main-title { color:#17245f; font-size:27px; font-weight:700; margin:0; }
.main-subtitle { color:#68738b; font-size:13px; margin-top:4px; }
.section-title { color:#1C2363; font-size:18px; font-weight:700; margin:22px 0 10px; padding-left:10px; border-left:4px solid #00BEEA; }
.panel { background:#fff; border:1px solid #d4d9df; border-radius:9px; padding:14px 16px; }
.kpi-card { background:#fff; border:1px solid #dce1e7; border-top:4px solid #22286d; border-radius:8px; padding:13px 15px; min-height:98px; box-shadow:0 2px 5px rgba(24,38,72,.05); overflow:hidden; }
.kpi-card.blue { border-top-color:#22286d; } .kpi-card.green { border-top-color:#008d68; } .kpi-card.purple { border-top-color:#7755c9; } .kpi-card.orange { border-top-color:#f28b30; } .kpi-card.cyan { border-top-color:#13b9dc; }
.kpi-title { color:#65728a; font-size:10px; font-weight:600; text-transform:uppercase; letter-spacing:.2px; line-height:1.2; }
.kpi-value { color:#1C2363; font-size:clamp(18px, 1.55vw, 24px); line-height:1.15; font-weight:700; margin-top:6px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.kpi-row-gap { height:14px; }
.small-note { color:#68738b; font-size:11px; margin-top:3px; }
.mini-badge { display:inline-block; padding:4px 8px; border-radius:5px; background:#eef1fb; color:#22286d; font-size:10px; font-weight:700; }
.stButton > button { border-radius:6px; border-color:#cbd2dc; color:#17245f; }
.stButton > button[kind="primary"] { background:#22286d; color:#fff; border-color:#22286d; }
.stDataFrame { border:1px solid #dce1e7; }
.hd { display:flex; justify-content:space-between; align-items:center; gap:8px; margin:2px 0 2px; }
.hd h2 { margin:0; padding:0; font-size:1.05rem; font-weight:700; color:#1C2363; }
.tag { background:#eef0fa; color:#1C2363; font-size:11px; font-weight:600; border-radius:6px; padding:2px 8px; white-space:nowrap; }
.sub { margin:0 0 10px; color:#6b7280; font-size:12px; }
.sub2 { margin:12px 0 6px; font-size:11px; font-weight:700; color:#6b7280; letter-spacing:.04em; text-transform:uppercase; }
.seg { display:grid; gap:9px; }
.sr { display:grid; grid-template-columns:minmax(100px,160px) 1fr auto; gap:12px; align-items:center; font-size:13px; }
.sr .n { overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.sr .t { height:10px; background:#eef1f5; border-radius:6px; overflow:hidden; }
.sr .t i { display:block; height:100%; border-radius:6px; }
.sr .v { font-weight:700; color:#1C2363; white-space:nowrap; text-align:right; }
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

    unidades_validas = r"MTS|KLS|UND|UN|KG|KGM|SERV|UNIDAD"

    # Formato habitual: código, descripción, piezas, cantidad, unidad,
    # precio, descuento, total e IVA.
    patron_linea_estandar = re.compile(
        r"^\s*\|?\s*(\d{3,10})\s+(.+?)\s+"
        r"(\d+)\s+([\d.,]+)\s+"
        rf"({unidades_validas})\s+"
        r"([\d.,]+)\s+([\d.,]+)\s+([\d.,]+)\s+([\d.,]+)"
        r"\s*\*?\|?\s*$", re.I | re.M
    )

    # Algunas facturas imprimen precio antes de la unidad: código,
    # descripción, piezas, cantidad, precio, unidad, descuento, total e IVA.
    patron_linea_precio_antes_unidad = re.compile(
        r"^\s*\|?\s*(\d{3,10})\s+(.+?)\s+"
        r"(\d+)\s+([\d.,]+)\s+"
        rf"([\d.,]+)\s+({unidades_validas})\s+"
        r"([\d.,]+)\s+([\d.,]+)\s+([\d.,]+)"
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

            for linea_texto in texto.splitlines():
                # Probar primero el formato habitual. En este PDF hay
                # cantidades con separador de miles, como 1,497.00.
                coincidencia = patron_linea_estandar.match(linea_texto)
                if coincidencia:
                    codigo, descripcion, piezas, cantidad, unidad, precio, descuento, total, iva = coincidencia.groups()
                else:
                    coincidencia = patron_linea_precio_antes_unidad.match(linea_texto)
                    if not coincidencia:
                        continue
                    codigo, descripcion, piezas, cantidad, precio, unidad, descuento, total, iva = coincidencia.groups()

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
    st.markdown(f'<img src="data:image/jpeg;base64,{LOGO_B64}" style="width:64px;height:64px;border-radius:12px;object-fit:cover">', unsafe_allow_html=True)

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
    estado_carga = f"Última factura registrada: {numero_ultima_factura} · {fecha_ultima_factura} · {fnum(total_facturas_registradas)} facturas en total"
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
    fila_1 = st.columns(3)
    fila_2 = st.columns([2, 1])
    destinos = {"Ciudad": fila_1[1], "Vendedor": fila_1[2], "Cliente": fila_2[0], "Tipo de venta": fila_2[1]}
    if not df_full.empty and "Fecha" in df_full.columns and not df_full["Fecha"].dropna().empty:
        f_min = df_full["Fecha"].min().date()
        f_max = df_full["Fecha"].max().date()
        with fila_1[0]:
            rango_fechas = st.date_input("Rango de fechas", (f_min, f_max), min_value=f_min, max_value=f_max)
    else:
        rango_fechas = None

    for nombre, opciones in filtros_visibles:
        with destinos[nombre]:
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
# RENDERIZADO DE INDICADORES COMERCIALES
# -----------------------------------------------------------------------------
NAVY, VERDE, CYAN = "#1C2363", "#008257", "#00BEEA"
PALETA = [NAVY, VERDE, CYAN, "#5b66b8", "#4fb596", "#e0457b", "#8a5fd0", "#f08a24", "#7fdcf3", "#2f6fa8"]
total_ventas = ventas or 1
desde, hasta = df["Fecha"].min(), df["Fecha"].max()
periodo = f"{desde:%d/%m/%Y} – {hasta:%d/%m/%Y}" if pd.notna(desde) else "Sin fechas"


def corto(valor):
    return f"${fnum(valor / 1e6, 1)}M" if abs(valor) >= 1e6 else cop(valor)


def tarjeta_kpi(titulo, valor, color, nota=""):
    nota_html = f'<div class="small-note">{nota}</div>' if nota else ""
    return f'<div class="kpi-card {color}"><div class="kpi-title">{titulo}</div><div class="kpi-value">{valor}</div>{nota_html}</div>'


def tarjeta(titulo, sub="", etiqueta=""):
    tag = f'<span class="tag">{escape(etiqueta)}</span>' if etiqueta else ""
    st.markdown(f'<div class="hd"><h2>{escape(titulo)}</h2>{tag}</div><p class="sub">{sub}</p>', unsafe_allow_html=True)


def filas(items, color=None):
    """Lista con barras de color: nombre, barra y valor con porcentaje."""
    if not items:
        return '<p class="sub">Sin datos con los filtros seleccionados.</p>'
    mayor = max(v for _, v in items) or 1
    html = ""
    for i, (nombre, valor) in enumerate(items):
        c = color or PALETA[i % len(PALETA)]
        html += (
            f'<div class="sr"><span class="n" title="{escape(str(nombre))}">{escape(str(nombre))}</span>'
            f'<span class="t"><i style="width:{valor / mayor * 100:.1f}%;background:{c}"></i></span>'
            f'<span class="v">{cop(valor)} ({fnum(valor / total_ventas * 100, 1)}%)</span></div>'
        )
    return f'<div class="seg">{html}</div>'


def mostrar(figura, alto=320, leyenda=False):
    figura.update_layout(
        height=alto, margin=dict(l=8, r=8, t=4, b=8), showlegend=leyenda, separators=",.",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(size=12, color="#2D2D2D"), hoverlabel=dict(bgcolor=NAVY, font_color="#fff"),
        legend=dict(orientation="h", y=-0.12, x=0.5, xanchor="center"),
    )
    st.plotly_chart(figura, use_container_width=True, config={"displayModeBar": False})


def barras_h(datos, x, y, color, n=10):
    d = datos.sort_values(x, ascending=False).head(n).iloc[::-1]
    textos = [f"{corto(v)} - {fnum(v / total_ventas * 100, 0)}%" for v in d[x]]
    maximo = float(d[x].max()) if not d.empty else 1
    figura = go.Figure(go.Bar(
        x=d[x], y=d[y].astype(str).str.slice(0, 32), orientation="h", marker_color=color,
        text=textos, textposition="outside", cliponaxis=False,
        textfont=dict(size=11, color=NAVY),
        hovertemplate="%{y}<br>$%{x:,.0f}<extra></extra>",
    ))
    # Reserva espacio para que el valor del primer lugar no quede cortado.
    figura.update_xaxes(
        showgrid=True, gridcolor="#eef1f5", zeroline=False,
        tickprefix="$", tickformat="~s", range=[0, maximo * 1.25],
    )
    figura.update_yaxes(showgrid=False)
    figura.update_layout(margin=dict(l=8, r=155, t=4, b=8), uniformtext_minsize=9)
    mostrar(figura)


def anillo(items, colores, alto=215):
    total = sum(v for _, v in items)
    figura = go.Figure(go.Pie(
        labels=[str(n) for n, _ in items], values=[v for _, v in items], hole=0.62, sort=False,
        marker=dict(colors=colores, line=dict(color="#ffffff", width=2)), textinfo="percent",
        hovertemplate="%{label}<br>$%{value:,.0f} (%{percent})<extra></extra>",
    ))
    figura.add_annotation(text=f"<b>{corto(total)}</b>", x=0.5, y=0.5, showarrow=False, font=dict(size=15, color=NAVY))
    mostrar(figura, alto=alto, leyenda=True)


def serie(columna):
    if columna not in df.columns:
        return []
    s = df.assign(_k=df[columna].fillna("Sin dato").replace("", "Sin dato")).groupby("_k")["Valor Total"].sum()
    return list(s.sort_values(ascending=False).items())


st.markdown('<div class="section-title">📊 Indicadores comerciales</div>', unsafe_allow_html=True)
kpis = [
    ("Ventas sin IVA", cop(ventas), "blue", periodo),
    ("Facturas realizadas", fnum(facturas), "green"),
    ("Clientes atendidos", fnum(clientes), "purple", f"En {fnum(df['Ciudad'].nunique())} ciudades"),
    ("Metros vendidos", f"{fnum(cantidad_metros, 2)} m", "orange", "Según unidad facturada"),
    ("Kilos vendidos", f"{fnum(cantidad_kilos, 2)} kg", "cyan", "Según unidad facturada"),
    ("Ticket promedio", cop(ticket), "blue", "Valor promedio por factura"),
]
for col, (titulo, valor, color, nota) in zip(
    st.columns([1.35, 0.85, 0.95, 1.05, 1.05, 1.10], gap="small"), kpis
):
    col.markdown(tarjeta_kpi(titulo, valor, color, nota), unsafe_allow_html=True)

st.markdown('<div class="kpi-row-gap"></div>', unsafe_allow_html=True)
extras = [
    ("Forma de pago dominante", forma_pago_principal, "cyan", f"{fnum(forma_pago_porcentaje, 1)}% del valor vendido"),
    ("Tipo de venta dominante", tipo_venta_principal, "purple", f"{fnum(tipo_venta_porcentaje, 1)}% del valor vendido"),
    ("Día de mayor venta", dia_mayor, "green", f"{cop(valor_mayor)} vendidos"),
    ("Día de menor venta", dia_menor, "orange", f"{cop(valor_menor)} vendidos"),
]
for col, (titulo, valor, color, nota) in zip(st.columns(4, gap="small"), extras):
    col.markdown(tarjeta_kpi(titulo, valor, color, nota), unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# BLOQUE DE GRÁFICOS Y ANÁLISIS COMERCIAL
# -----------------------------------------------------------------------------
st.markdown('<div class="section-title">📈 Análisis comercial detallado</div>', unsafe_allow_html=True)

c1, c2 = st.columns([2, 1])
with c1:
    with st.container(border=True):
        tarjeta("Ventas y facturas por día", "Facturas emitidas (barras) y valor vendido (línea)")
        d = (df.groupby("Fecha", as_index=False)
               .agg(ventas=("Valor Total", "sum"), facturas=("Factura #", "nunique"))
               .dropna(subset=["Fecha"]).sort_values("Fecha"))
        dias = d["Fecha"].dt.strftime("%d/%m")
        figura = go.Figure()
        figura.add_bar(x=dias, y=d["facturas"], name="Facturas", marker_color=CYAN,
                       hovertemplate="%{x}<br>%{y} facturas<extra></extra>")
        figura.add_scatter(x=dias, y=d["ventas"], name="Ventas ($)", mode="lines+markers", yaxis="y2",
                           line=dict(color=VERDE, width=3), marker=dict(size=7),
                           hovertemplate="%{x}<br>$%{y:,.0f}<extra></extra>")
        figura.update_layout(
            xaxis=dict(type="category", showgrid=False),
            yaxis=dict(title="Facturas", rangemode="tozero", gridcolor="#eef1f5", tickformat="d"),
            yaxis2=dict(title="Ventas ($)", overlaying="y", side="right", rangemode="tozero",
                        showgrid=False, tickprefix="$", tickformat="~s"),
        )
        mostrar(figura, alto=480, leyenda=True)
with c2:
    with st.container(border=True):
        tarjeta("Tipo de venta y forma de pago", "Participación sobre el valor vendido")
        st.markdown('<p class="sub2">Tipo de venta</p>', unsafe_allow_html=True)
        items = serie("Tipo de Venta")
        if items:
            anillo(items, [VERDE, CYAN, "#5b66b8", "#4fb596"])
        st.markdown('<p class="sub2">Forma de pago</p>', unsafe_allow_html=True)
        items = serie("Forma de Pago")
        if items:
            anillo(items, [NAVY, "#5b66b8", CYAN, "#8a5fd0", "#f08a24"])

c1, c2 = st.columns(2)
with c1:
    with st.container(border=True):
        tarjeta("Top 10 ciudades por ventas", "Valor vendido y participación sobre el total")
        barras_h(df.groupby("Ciudad", as_index=False)["Valor Total"].sum(), "Valor Total", "Ciudad", VERDE)
with c2:
    with st.container(border=True):
        tarjeta("Top 10 artículos más vendidos", "Valor vendido y participación sobre el total")
        barras_h(df.groupby("Descripcion", as_index=False)["Valor Total"].sum(), "Valor Total", "Descripcion", "#5b66b8")

c1, c2 = st.columns(2)
with c1:
    with st.container(border=True):
        top_clientes = serie("Cliente")[:7]
        tarjeta("Ranking de facturación por cliente", "Top 7 clientes por valor vendido", f"{fnum(clientes)} clientes · {corto(ventas)}")
        st.markdown(filas(top_clientes), unsafe_allow_html=True)
with c2:
    with st.container(border=True):
        vendedores = serie("Vendedor")[:10]
        tarjeta("Desempeño por vendedor", "Valor vendido y participación", f"{len(vendedores)} vendedores")
        st.markdown(filas(vendedores), unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# TABLA DE DETALLE
# -----------------------------------------------------------------------------
st.markdown('<div class="section-title">📋 Detalle de facturación</div>', unsafe_allow_html=True)
with st.container(border=True):
    st.dataframe(
        df, use_container_width=True, hide_index=True,
        column_config={"Fecha": st.column_config.DateColumn("Fecha", format="DD/MM/YYYY")},
    )
