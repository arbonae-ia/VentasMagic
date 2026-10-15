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
.kpi-value { color:#1C2363; font-size:clamp(18px, 1.6vw, 25px); line-height:1.15; font-weight:700; margin-top:6px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
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
    "SEP": "09", "OCT": "10", "NOV": "11", "DEC": "12",
    "AGO": "08", "OCT": "10"
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
            texto = texto if len(partes[-1]) <= 2 else texto.replace(".", "")
        return float(texto)
    except Exception:
        return 0.0

def convertir_fecha_pdf(fecha):
    partes = limpiar_texto(fecha).replace("−", "-").replace("–", "-").split("-")
    if len(partes) != 3:
        return ""
    try:
        mes_str = partes[1].upper()
        mes = MESES_PDF.get(mes_str, mes_str)
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

    with pdfplumber.open(io.BytesIO(contenido)) as pdf:
        for pagina in pdf.pages:
            texto = (pagina.extract_text() or "").replace("−", "-").replace("–", "-")
            if not texto.strip():
                continue

            # Detectar si es un Traslado (TR) o una Factura de Venta (FM)
            es_traslado = "TR" in texto.upper() or "TRANSFERENCIA" in texto.upper()

            if es_traslado:
                doc_match = re.search(r"Numero\s*:\s*([0-9\-TR]+)", texto, re.I)
                doc_match = doc_match or re.search(r"\b(\d{3}-TR-\d+)\b", texto, re.I)
                if not doc_match:
                    continue
                factura = doc_match.group(1).upper()

                fecha_match = re.search(r"Fecha\s*:\s*(\d{4}-[A-Z]{3}-\d{2})", texto, re.I)
                fecha = convertir_fecha_pdf(fecha_match.group(1)) if fecha_match else ""

                cliente = "Bellatela SAS"
                nit = "800138082"
                ciudad_match = re.search(r"Local\.\s*Destino\s*:\s*[0-9\-]+\s*(.*?)(?:\n|$)", texto, re.I)
                ciudad = limpiar_texto(ciudad_match.group(1)) if ciudad_match else "INTERNO"
                vendedor = "WAGNER GIRALDO PAOLA ANDREA"
                forma_pago = "Contado"

                patron_filas_tr = re.findall(
                    r"(\d{10,15})\s+([A-ZÁÉÍÓÚÑ0-9\-\s]+?)\s+(\d{10,15})\s*\|\s*([\d.,]+)\s*([A-Z]{2,4})\s+([\d.,]+)\s+S\s*([\d.,]+)\s*\|\s*([\d.,]+)",
                    texto
                )
                if not patron_filas_tr:
                    patron_filas_tr = re.findall(
                        r"(\d{10,15})\s+([A-ZÁÉÍÓÚÑ0-9\-\s]+?)\s+([\d.,]+)\s+(?:MTS|UND|KG)\s+([\d.,]+)\s+([\d.,]+)",
                        texto
                    )

                for row in patron_filas_tr:
                    if len(row) >= 8:
                        codigo, descripcion, _, _, unidad, cantidad, _, total = row[:8]
                    elif len(row) >= 5:
                        codigo, descripcion, cantidad, _, total = row[:5]
                        unidad = "MTS"
                    else:
                        continue

                    descripcion = limpiar_texto(descripcion)
                    cantidad_val = convertir_numero(cantidad)
                    total_val = convertir_numero(total)
                    if cantidad_val == 0 or total_val == 0:
                        continue

                    es_crudo = "CRUDO" in descripcion.upper()
                    if es_crudo:
                        registros.append([
                            factura, fecha, cliente, nit, ciudad, vendedor,
                            limpiar_texto(codigo), f"Base: {descripcion}", limpiar_texto(unidad).upper(),
                            cantidad_val, total_val / cantidad_val, total_val, 0.0,
                            forma_pago, "Bases Textiles"
                        ])
                    else:
                        valor_sublimacion = 5000.0 * cantidad_val
                        valor_base_restante = max(0.0, total_val - valor_sublimacion)
                        registros.append([
                            factura, fecha, cliente, nit, ciudad, vendedor,
                            limpiar_texto(codigo), f"Sublimación: {descripcion}", limpiar_texto(unidad).upper(),
                            cantidad_val, 5000.0, valor_sublimacion, 0.0,
                            forma_pago, "Servicio"
                        ])
                        precio_base = valor_base_restante / cantidad_val if cantidad_val > 0 else 0.0
                        registros.append([
                            factura, fecha, cliente, nit, ciudad, vendedor,
                            limpiar_texto(codigo), f"Base: {descripcion}", limpiar_texto(unidad).upper(),
                            cantidad_val, precio_base, valor_base_restante, 0.0,
                            forma_pago, "Bases Textiles"
                        ])
            else:
                # -------------------------------------------------------------
                # EXTRACCIÓN PÁGINA POR PÁGINA PARA FACTURAS DE VENTA (FM)
                # -------------------------------------------------------------
                factura_match = re.search(r"Numero\s*:\s*(?:[A-Za-z]+\s*:\s*)?([A-Z]+-\d+)", texto, re.I)
                factura_match = factura_match or re.search(r"\b(FM-\d+)\b", texto, re.I)
                if not factura_match:
                    continue
                factura = factura_match.group(1).upper()

                fecha_match = re.search(r"Fecha\s*:\s*(\d{4}-[A-Z]{3}-\d{2})", texto, re.I)
                fecha = convertir_fecha_pdf(fecha_match.group(1)) if fecha_match else ""

                cliente_match = re.search(r"Cliente\s*[:]?\s*(.*?)(?:\n|Establecim|Nit|Direccion|$)", texto, re.I)
                cliente = limpiar_texto(cliente_match.group(1)) if cliente_match else "CLIENTE GENERAL"

                nit_match = re.search(r"(?:Nit\s+o\s+C\.C\.|Nit)\s*[:]?\s*([0-9.\-]+)", texto, re.I)
                nit = limpiar_nit(nit_match.group(1)) if nit_match else "0"

                ciudad_match = re.search(r"Ciudad\s*[:]?\s*([A-ZÁÉÍÓÚÑ ]+)", texto, re.I)
                ciudad = limpiar_texto(ciudad_match.group(1)) if ciudad_match else "CALI"

                vendedor_match = re.search(r"Vendedor\s*[:]?\s*(?:[0-9]+\s+)?(.*?)(?:\n|OC\.Nro|$)", texto, re.I)
                vendedor = limpiar_texto(vendedor_match.group(1)) if vendedor_match else ""

                pago_match = re.search(r"(CREDITO\s+\d+\s+DIAS?|CONTADO)", texto, re.I)
                forma_pago = limpiar_texto(pago_match.group(1)) if pago_match else "CONTADO"

                iva_match = re.search(r"Iva%|19\.00", texto)
                iva_porcentaje = 19.0 if iva_match else 0.0

                lineas_texto = texto.split("\n")
                for linea in lineas_texto:
                    match_item = re.search(
                        r"^\s*(\d{5,10})\s+(.+?)\s+([\d.,]+)\s+(MTS|KLS|UND|UN|KG|KGM|SERV|UNIDAD)\s+([\d.,]+)(?:\s+[\d.,]+)?\s+([\d.,]+)",
                        linea, re.I
                    )
                    if match_item:
                        codigo, descripcion, cantidad, unidad, precio, total = match_item.groups()
                        total_val = convertir_numero(total)
                        if total_val > 0:
                            registros.append([
                                factura, fecha, cliente, nit, ciudad, vendedor,
                                limpiar_texto(codigo), limpiar_texto(descripcion),
                                limpiar_texto(unidad).upper(), convertir_numero(cantidad),
                                convertir_numero(precio), total_val, iva_porcentaje,
                                forma_pago, clasificar_tipo_venta(codigo)
                            ])

    if not registros:
        raise ValueError("No se encontraron líneas de productos o servicios válidas en el documento.")
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
    st.subheader("📤 Cargar facturas / TR")
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
                with st.spinner("Procesando el documento..."):
                    st.session_state["registros_pdf"] = extraer_datos_pdf(archivo_pdf)
                st.rerun()
            except Exception as error:
                st.error(f"El documento no es válido o está vacío: {error}")

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
    st.markdown('<div class="section-title">📦 Vista previa del documento</div>', unsafe_allow_html=True)
    df_pdf = pd.DataFrame(registros_pdf, columns=COLUMNAS)
    st.caption(f"Se encontraron {len(df_pdf)} líneas en el documento.")
    st.dataframe(df_pdf, use_container_width=True, hide_index=True)

    informacion = obtener_informacion_duplicados(hoja, registros_pdf)
    repetidas = sorted(informacion["facturas_existentes"])
    nuevas = sorted(informacion["facturas_nuevas"])

    if repetidas:
        st.warning(f"El documento contiene {len(repetidas)} registros ya cargados.")
        c1, c2, c3 = st.columns(3)
        c1.metric("Registros repetidos", len(repetidas))
        c2.metric("Líneas a reemplazar", len(informacion["filas_a_borrar"]))
        c3.metric("Nuevos", len(nuevas))
        with st.expander("Ver repetidos"):
            st.write(", ".join(repetidas))

        if st.button("No cargar este archivo", key="cancelar_archivo_repetido", use_container_width=True):
            st.session_state["registros_pdf"] = None
            st.session_state["uploader_version"] += 1
            st.rerun()

        confirmar = st.checkbox("Confirmo que deseo reemplazar los registros repetidos.")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Cargar solo nuevos", disabled=not nuevas, use_container_width=True):
                try:
                    with st.spinner("Cargando nuevos..."):
                        agregar_facturas_nuevas(hoja, registros_pdf, informacion["facturas_existentes"])
                    st.cache_data.clear()
                    st.session_state["registros_pdf"] = None
                    st.session_state["mensaje_carga"] = "Registros nuevos cargados correctamente."
                    st.rerun()
                except Exception as error:
                    st.error(f"Error: {error}")
        with c2:
            if st.button("Reemplazar repetidos", type="primary", disabled=not confirmar, use_container_width=True):
                try:
                    with st.spinner("Reemplazando..."):
                        reemplazar_facturas(hoja, registros_pdf, informacion["filas_a_borrar"])
                    st.cache_data.clear()
                    st.session_state["registros_pdf"] = None
                    st.session_state["mensaje_carga"] = "Registros reemplazados correctamente."
                    st.rerun()
                except Exception as error:
                    st.error(f"Error: {error}")
    else:
        st.success("No se encontraron registros repetidos. Todos son nuevos.")
        if st.button("Cargar en Google Sheets", type="primary", use_container_width=True):
            try:
                with st.spinner("Cargando..."):
                    hoja.append_rows(registros_pdf, value_input_option="USER_ENTERED")
                st.cache_data.clear()
                st.session_state["registros_pdf"] = None
                st.session_state["mensaje_carga"] = "Documento cargado correctamente."
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
    figura = go.Figure(go.Bar(
        x=d[x], y=d[y].astype(str).str.slice(0, 32), orientation="h", marker_color=color,
        text=textos, textposition="outside", cliponaxis=False,
        hovertemplate="%{y}<br>$%{x:,.0f}<extra></extra>",
    ))
    figura.update_xaxes(showgrid=True, gridcolor="#eef1f5", zeroline=False, tickprefix="$", tickformat="~s")
    figura.update_yaxes(showgrid=False)
    figura.update_layout(margin=dict(l=8, r=115, t=4, b=8))
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
    ("Facturas realizadas", fnum(facturas), "green", f"{fnum(len(df))} líneas de detalle"),
    ("Clientes atendidos", fnum(clientes), "purple", f"En {fnum(df['Ciudad'].nunique())} ciudades"),
    ("Metros vendidos", f"{fnum(cantidad_metros, 2)} m", "orange", "Según unidad facturada"),
    ("Kilos vendidos", f"{fnum(cantidad_kilos, 2)} kg", "cyan", "Según unidad facturada"),
    ("Ticket promedio", cop(ticket), "blue", "Valor promedio por factura"),
]
for col, (titulo, valor, color, nota) in zip(st.columns(6, gap="small"), kpis):
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
