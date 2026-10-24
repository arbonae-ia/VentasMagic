import base64
import io
import re
from collections import Counter
from html import escape
from pathlib import Path
import calendar
from datetime import date, datetime, timedelta

import gspread
import numpy as np
import pandas as pd
import pdfplumber
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
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
/* =========================================================================
   SISTEMA VISUAL MAGIC PRINT (v13 - tema claro)
   Fondo gris muy claro · tarjetas blancas con borde superior de color
   Colores: azul marino #1C2363 · verde #008257 · cyan #00BEEA
   ========================================================================= */
:root {
  --fondo:#F3F6FA; --card:#FFFFFF; --card2:#FFFFFF; --borde:#E2E7EE;
  --texto:#1C2363; --cuerpo:#2D2D2D; --gris:#5B6478; --navy:#1C2363; --cyan:#00BEEA; --verde:#008257;
  --magenta:#E0218A; --alerta:#D9480F; --suave:#EEF1F5;
}
.stApp { font-family:"Source Sans Pro","Source Sans 3",system-ui,sans-serif; background:var(--fondo); color:var(--cuerpo); }
[data-testid="stHeader"] { background:rgba(243,246,250,.9); }
[data-testid="stSidebar"] { background:#FFFFFF; border-right:1px solid var(--borde); }
[data-testid="stSidebar"] * { color:var(--cuerpo); }
.block-container { max-width:1240px; padding-top:3.6rem; padding-bottom:3rem; }
#MainMenu, footer { visibility:hidden; }
.stApp p, .stApp label, .stApp span, .stApp li { color:inherit; }

/* Contenedores con borde de Streamlit = tarjetas blancas */
[data-testid="stVerticalBlockBorderWrapper"] { background:var(--card); border:1px solid var(--borde) !important; border-radius:12px; padding:10px 14px !important; box-shadow:0 1px 3px rgba(28,35,99,.06); }
[data-testid="stVerticalBlockBorderWrapper"] > div { background:transparent; }
[class*="st-key-tarjeta_"] { background:var(--card); border:1px solid var(--borde) !important; border-radius:12px; padding:14px 18px !important; box-shadow:0 1px 3px rgba(28,35,99,.06); }
/* Filtros compactos: menos relleno y menos espacio entre las dos filas */
.st-key-tarjeta_filtros { padding:8px 16px 10px !important; gap:6px !important; }
.st-key-tarjeta_filtros [data-testid="stWidgetLabel"] { min-height:0; margin-bottom:2px; }
.st-key-tarjeta_filtros [data-testid="stWidgetLabel"] p { font-size:11.5px !important; }
[data-testid="stExpander"] details { background:var(--card); border:1px solid var(--borde); border-radius:12px; }
[data-testid="stExpander"] summary p { color:var(--texto); font-weight:600; }
[data-testid="stExpander"] summary, [data-testid="stExpander"] summary:hover { background:transparent; color:var(--texto); }
.stSubheader, [data-testid="stMarkdownContainer"] h3 { font-size:1rem !important; color:var(--texto); }

/* Campos de filtros */
[data-baseweb="select"] > div, [data-baseweb="input"] > div, .stTextInput input, .stDateInput input {
  background:#FFFFFF !important; border-color:#CFD6E0 !important; color:var(--cuerpo) !important; border-radius:8px !important; }
[data-baseweb="select"] span, [data-baseweb="select"] div { color:var(--cuerpo); }
[data-testid="stDateInputField"], .react-aria-ComboBox > div, .stTextInput [data-baseweb="base-input"], .stTextInput > div > div { background:#FFFFFF !important; border:1px solid #CFD6E0 !important; border-radius:8px !important; }
[data-baseweb="tag"] { background:var(--navy) !important; }
[data-baseweb="tag"] span { color:#FFFFFF !important; }
[data-testid="stWidgetLabel"] p, [data-testid="stVerticalBlockBorderWrapper"] label p { font-size:12px !important; color:var(--gris) !important; font-weight:400; }

/* Encabezado: tarjeta blanca con línea azul marino arriba */
.app-header { display:flex; align-items:center; justify-content:space-between; gap:16px;
  background:#FFFFFF; border:1px solid var(--borde); border-top:3px solid var(--navy); border-radius:4px 4px 12px 12px;
  padding:16px 28px; margin-bottom:14px; box-shadow:0 1px 3px rgba(28,35,99,.06); }
.app-header .marca { display:flex; align-items:center; gap:14px; }
.app-header img { width:60px; height:60px; object-fit:cover; border-radius:12px; }
.main-title { color:var(--navy); font-size:24px; font-weight:700; line-height:1.15; margin:0; }
.main-subtitle { color:var(--gris); font-size:13px; margin-top:4px; }
.app-header .estado { color:var(--gris); font-size:11.5px; text-align:right; line-height:1.4; max-width:340px; }

/* Filtros */
.filtros-titulo { color:var(--navy); font-size:13px; font-weight:700; margin:6px 0 2px; }
.campo-fechas { background:#FFFFFF; border:1px solid #CFD6E0; border-radius:8px; color:var(--cuerpo); font-size:14px; padding:8px 12px; min-height:40px; display:flex; align-items:center; gap:8px; white-space:nowrap; overflow:hidden; }
.campo-fechas small { color:var(--gris); }
.etiqueta-campo { font-size:12px; color:var(--gris); margin:0 0 6px; }
.filter-summary { background:#FFFFFF; border:1px solid var(--borde); border-left:4px solid var(--cyan); border-radius:8px; color:var(--gris); font-size:12px; line-height:1.5; margin:10px 0 4px; padding:7px 12px; }
.filter-summary strong { color:var(--texto); }
.data-status { color:var(--gris); font-size:11px; font-style:italic; line-height:1.3; margin:2px 0 6px; }

/* Títulos de sección */
.section-title { display:flex; align-items:baseline; gap:10px; color:var(--navy); font-size:18px; font-weight:700; margin:26px 0 10px; padding-left:12px; border-left:4px solid var(--navy); }
.section-title small { color:var(--gris); font-size:12px; font-weight:400; }

/* Tarjetas KPI: blancas, borde superior de color, número grande en azul marino */
.kpi-grid { display:grid; grid-template-columns:repeat(auto-fit, minmax(180px, 1fr)); gap:12px; align-items:stretch; margin-bottom:12px; }
.kpi-grid.cinco { grid-template-columns:repeat(auto-fit, minmax(200px, 1fr)); }
.kpi-grid.una { grid-template-columns:1fr; gap:10px; margin-bottom:10px; }
.kpi-card { background:#FFFFFF; border:1px solid var(--borde); border-top:4px solid var(--navy); border-radius:12px; padding:14px 16px; display:flex; flex-direction:column; gap:4px; min-width:0; box-shadow:0 1px 3px rgba(28,35,99,.06); }
.kpi-card.navy { border-top-color:var(--navy); } .kpi-card.verde { border-top-color:var(--verde); } .kpi-card.cyan { border-top-color:var(--cyan); }
.kpi-card.alerta { border-top-color:var(--alerta); }
.kpi-title { color:var(--gris); font-size:13px; font-weight:400; line-height:1.25; }
.kpi-value { color:var(--navy); font-size:clamp(20px, 1.9vw, 28px); font-weight:700; line-height:1.15; overflow-wrap:anywhere; font-variant-numeric:tabular-nums; }
.kpi-value.texto { font-size:clamp(15px, 1.3vw, 19px); }
.kpi-value.verde { color:var(--verde); } .kpi-value.alerta { color:var(--alerta); }
.small-note { color:var(--gris); font-size:12px; line-height:1.35; margin-top:auto; }
.barra { height:8px; background:var(--suave); border-radius:6px; overflow:hidden; margin:4px 0 2px; }
.barra i { display:block; height:100%; border-radius:6px; background:var(--verde); }
.barra.alerta i { background:var(--alerta); }

/* Panel de presupuesto */
.ppto-ayuda { color:var(--gris); font-size:12px; line-height:1.45; }
.ppto-ayuda b { color:var(--texto); }
.aviso { background:var(--suave); border-radius:8px; color:var(--cuerpo); font-size:12.5px; padding:10px 12px; line-height:1.45; }

/* Botones: contorno azul marino; el principal, relleno azul marino */
.stButton > button, .stDownloadButton > button { border-radius:8px; border:1px solid var(--navy); background:#FFFFFF; color:var(--navy); font-weight:600; }
.stButton > button:hover, .stDownloadButton > button:hover { background:#EEF1F8; border-color:var(--navy); color:var(--navy); }
.stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] { background:var(--navy); color:#fff; border-color:var(--navy); }
.stButton > button[kind="primary"]:hover, .stDownloadButton > button[kind="primary"]:hover { background:#2B3486; border-color:#2B3486; color:#fff; }
.stButton > button p, .stDownloadButton > button p { color:inherit; }
.stDataFrame { border:1px solid var(--borde); border-radius:8px; }

/* Tarjetas de gráficos */
[class*="st-key-graf_"] { background:#FFFFFF; border:1px solid var(--borde); border-radius:12px; padding:16px 18px 10px; box-shadow:0 1px 3px rgba(28,35,99,.06); }
[class*="st-key-graf_"] p, [class*="st-key-graf_"] span { color:var(--cuerpo); }
/* Tarjetas lado a lado con la misma altura (gráficos y referencias) */
[data-testid="stLayoutWrapper"]:has(> [class*="st-key-graf_"]),
[data-testid="stLayoutWrapper"]:has(> .st-key-tarjeta_referencias) { flex:1 1 auto; }
[class*="st-key-graf_"], .st-key-tarjeta_referencias { height:100%; }
.st-key-graf_tendencia { justify-content:space-between; }
.st-key-graf_tendencia .aviso { margin-bottom:8px; }

/* Encabezados de tarjetas de gráficos y listas */
.hd { display:flex; justify-content:space-between; align-items:center; gap:8px; margin:2px 0 2px; }
.hd h2 { margin:0; padding:0; font-size:1.05rem; font-weight:700; color:var(--navy) !important; }
.tag { background:#EEF1F8; color:var(--navy) !important; font-size:11px; font-weight:600; border-radius:6px; padding:2px 8px; white-space:nowrap; }
.sub { margin:0 0 10px; color:var(--gris) !important; font-size:12px; }
.seg { display:grid; gap:9px; }
.sr { display:grid; grid-template-columns:minmax(100px,170px) 1fr auto; gap:12px; align-items:center; font-size:13px; color:var(--cuerpo); }
.sr .n { overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.sr .t { height:10px; background:var(--suave); border-radius:6px; overflow:hidden; }
.sr .t i { display:block; height:100%; border-radius:6px; }
.sr .v { font-weight:700; color:var(--navy) !important; white-space:nowrap; text-align:right; font-variant-numeric:tabular-nums; }
</style>
""", unsafe_allow_html=True)

NOMBRE_ARCHIVO = "Base_Datos_Ventas"
NOMBRE_PESTANA = "Hoja1"
# Ventas de años anteriores (2023 en adelante) para los comparativos. Es opcional:
# si la pestaña no existe, el aplicativo funciona igual pero sin comparar.
NOMBRE_PESTANA_HISTORICO = "Historico"
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

CODIGOS_SERVICIO = {"888911", "888912", "888918", "888923", "888916"}
CLASIFICACION_POR_CODIGO = {
    "888918": "Otros servicios",            # Flete
    "888911": "Manipulación de diseños",    # Servicio desarrollo diseño sublimación
}

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


def convertir_cantidad_pdf(valor):
    """Lee cantidades del PDF, donde 54.000 representa 54 metros."""
    texto = limpiar_texto(valor).replace("$", "").replace(" ", "")
    if not texto:
        return 0.0
    if "." in texto and "," not in texto:
        partes = texto.split(".")
        if len(partes) == 2 and len(partes[-1]) == 3:
            try:
                return float(texto)
            except Exception:
                return 0.0
    return convertir_numero(texto)


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


def normalizar_numero_documento(numero):
    numero = limpiar_texto(numero).upper().replace("−", "-").replace("–", "-")
    traslado = re.fullmatch(r"\d+-TR-(\d+)", numero)
    return f"TR-{traslado.group(1)}" if traslado else numero


def clasificar_actividad(descripcion, tipo_venta="", codigo=""):
    texto = limpiar_texto(descripcion).upper()
    tipo = limpiar_texto(tipo_venta).upper()
    codigo_limpio = limpiar_texto(codigo).replace(".0", "")
    if codigo_limpio in CLASIFICACION_POR_CODIGO:
        return CLASIFICACION_POR_CODIGO[codigo_limpio]
    if "SUBLIM" in texto or tipo == "SUBLIMACIÓN":
        return "Sublimación"
    if "CORTE" in texto and "LASER" in texto:
        return "Corte láser"
    if "MANIPUL" in texto or "DISEÑO" in texto:
        return "Manipulación de diseños"
    if "CRUDO" in texto or tipo in {"BASE TEXTIL", "BASES TEXTILES"}:
        return "Base textil"
    if tipo == "SERVICIO":
        return "Otros servicios"
    return "Otros"


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

    # Traslados: código, descripción, lote, local, unidad, cantidad,
    # entrada/salida, precio unitario y valor total.
    patron_linea_traslado = re.compile(
        r"^\s*\|?\s*(\d{8,14})\s+(.+?)\s+"
        r"(\d{6,})\s+(\d{3}-\d{2})\s+"
        rf"({unidades_validas})\s+([\d.,]+)\s+[ES]\s+"
        r"([\d.,]+)\s+([\d.,]+)\s*\|?\s*$", re.I | re.M
    )

    with pdfplumber.open(io.BytesIO(contenido)) as pdf:
        for pagina in pdf.pages:
            texto = (pagina.extract_text() or "").replace("−", "-").replace("–", "-")
            if not texto.strip():
                continue

            factura_match = re.search(r"Numero\s*:\s*([A-Z0-9]+(?:-[A-Z0-9]+)+)", texto, re.I)
            factura_match = factura_match or re.search(r"\b(FM-\d+)\b", texto, re.I)
            if not factura_match:
                continue

            factura = normalizar_numero_documento(factura_match.group(1))
            fecha_match = re.search(r"Fecha\s*:\s*(\d{4}-[A-Z]{3}-\d{2})", texto, re.I)
            cliente_match = re.search(r"Cliente\s*:\s*(.*?)\s*\|", texto, re.I)
            nit_match = re.search(r"Nit\s+o\s+C\.C\.\s*:\s*([0-9.\-]+)", texto, re.I)
            ciudad_match = re.search(r"Ciudad\s*:\s*([A-ZÁÉÍÓÚÑ ]+)", texto, re.I)
            vendedor_match = re.search(r"Vendedor\s*:\s*(?:\d+\s+)?(.*?)\s*\|", texto, re.I)
            pago_match = re.search(r"\|\s*(CREDITO\s+\d+\s+DIAS?|CONTADO)\s*\|", texto, re.I)
            destino_match = re.search(r"Local\.\s*Destino\s*:\s*(?:\d+-\d+\s+)?([^\n|]+)", texto, re.I)
            detalle_match = re.search(r"Detalle\s*:\s*(.*?)(?:\n\+|\Z)", texto, re.I | re.S)
            es_traslado = factura.startswith("TR-")

            fecha = convertir_fecha_pdf(fecha_match.group(1)) if fecha_match else ""
            cliente = limpiar_texto(cliente_match.group(1)) if cliente_match else ""
            nit = limpiar_nit(nit_match.group(1)) if nit_match else ""
            ciudad = limpiar_texto(ciudad_match.group(1)) if ciudad_match else ""
            vendedor = limpiar_texto(vendedor_match.group(1)) if vendedor_match else ""
            forma_pago = limpiar_texto(pago_match.group(1)) if pago_match else ""
            if es_traslado:
                cliente = "Bellatela SAS"
                nit = "800138082"
                ciudad = limpiar_texto(destino_match.group(1)) if destino_match else "NO APLICA"
                vendedor = "WAGNER GIRALDO PAOLA ANDREA"
                forma_pago = "Cruce de cuentas"
                detalle_transferencia = limpiar_texto(detalle_match.group(1)) if detalle_match else ""
                detalle_transferencia = detalle_transferencia.upper()
                es_solo_base = (
                    "CRUDO" in detalle_transferencia or
                    "BASE" in detalle_transferencia
                )

            for linea_texto in texto.splitlines():
                traslado = patron_linea_traslado.match(linea_texto) if es_traslado else None
                if traslado:
                    codigo, descripcion, lote, local, unidad, cantidad, precio, total = traslado.groups()
                    cantidad = convertir_cantidad_pdf(cantidad)
                    precio = convertir_numero(precio)
                    total = convertir_numero(total)
                    descripcion = limpiar_texto(descripcion)
                    if not codigo or total == 0:
                        continue

                    if es_solo_base:
                        registros.append([
                            factura, fecha, cliente, nit, ciudad, vendedor,
                            limpiar_texto(codigo), f"Base - {descripcion}",
                            limpiar_texto(unidad).upper(), cantidad, precio, total,
                            0, forma_pago, "Base textil"
                        ])
                    else:
                        valor_sublimacion = cantidad * 5000
                        valor_base = max(total - valor_sublimacion, 0)
                        precio_base = valor_base / cantidad if cantidad else 0
                        registros.extend([
                            [
                                factura, fecha, cliente, nit, ciudad, vendedor,
                                limpiar_texto(codigo), f"Sublimación - {descripcion}",
                                "MTS", cantidad, 5000, valor_sublimacion,
                                0, forma_pago, "Sublimación"
                            ],
                            [
                                factura, fecha, cliente, nit, ciudad, vendedor,
                                limpiar_texto(codigo), f"Base - {descripcion}",
                                "MTS", cantidad, precio_base, valor_base,
                                0, forma_pago, "Base textil"
                            ],
                        ])
                    continue

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
                    forma_pago, clasificar_actividad(descripcion, clasificar_tipo_venta(codigo), codigo)
                ])

    if not registros:
        raise ValueError("No se encontraron líneas de productos o servicios.")
    return registros

def clave_linea(registro):
    """Crea una clave estable para comparar líneas sin duplicarlas."""
    posiciones_numericas = {9, 10, 11, 12}
    clave = []
    for posicion, valor in enumerate(registro):
        if posicion in posiciones_numericas:
            clave.append(f"{convertir_numero(valor):.6f}")
        else:
            clave.append(limpiar_texto(valor).upper())
    return tuple(clave)


def obtener_informacion_duplicados(hoja, registros_pdf):
    datos = hoja.get_all_values()
    facturas_pdf = {limpiar_texto(r[0]) for r in registros_pdf}
    if len(datos) < 2:
        return {
            "facturas_existentes": set(), "filas_a_borrar": [],
            "facturas_nuevas": facturas_pdf, "registros_nuevos": registros_pdf,
            "lineas_repetidas": 0,
        }

    encabezados = [limpiar_texto(x) for x in datos[0]]
    if "Factura #" not in encabezados:
        raise ValueError("No existe la columna 'Factura #' en Google Sheets.")
    posicion = encabezados.index("Factura #")
    existentes, filas = set(), []
    claves_existentes = Counter()
    for numero_fila, fila in enumerate(datos[1:], start=2):
        if len(fila) > posicion:
            factura = limpiar_texto(fila[posicion])
            if factura in facturas_pdf:
                existentes.add(factura)
                filas.append(numero_fila)
                claves_existentes[clave_linea(fila)] += 1

    claves_pdf = Counter(clave_linea(registro) for registro in registros_pdf)
    claves_nuevas = claves_pdf - claves_existentes
    registros_nuevos = []
    pendientes = Counter(claves_nuevas)
    for registro in registros_pdf:
        clave = clave_linea(registro)
        if pendientes[clave] > 0:
            registros_nuevos.append(registro)
            pendientes[clave] -= 1

    return {
        "facturas_existentes": existentes,
        "filas_a_borrar": filas,
        "facturas_nuevas": facturas_pdf - existentes,
        "registros_nuevos": registros_nuevos,
        "lineas_repetidas": len(registros_pdf) - len(registros_nuevos),
    }

def agregar_facturas_nuevas(hoja, registros_nuevos):
    if registros_nuevos:
        hoja.append_rows(registros_nuevos, value_input_option="USER_ENTERED")
    return registros_nuevos

def reemplazar_facturas(hoja, registros_pdf, filas_a_borrar):
    for fila in sorted(filas_a_borrar, reverse=True):
        hoja.delete_rows(fila)
    hoja.append_rows(registros_pdf, value_input_option="USER_ENTERED")

def mover_encabezado_al_inicio(datos):
    """Si la fila de títulos no está en la fila 1 (por ejemplo, porque alguien
    ordenó la hoja incluyéndola), la busca y la deja de primera."""
    if not datos or "Valor Total" in [limpiar_texto(x) for x in datos[0]]:
        return datos
    for posicion, fila in enumerate(datos):
        textos = [limpiar_texto(x) for x in fila]
        if "Factura #" in textos and "Valor Total" in textos:
            return [datos[posicion]] + datos[:posicion] + datos[posicion + 1:]
    return datos


@st.cache_data(ttl=30)
def cargar_datos():
    hoja = conectar_hoja()
    return preparar_tabla(mover_encabezado_al_inicio(hoja.get_all_values()))


def fecha_desde_celda(valor):
    """Convierte una fecha de Google Sheets (número de serie o texto) a fecha."""
    if isinstance(valor, (int, float)) and not isinstance(valor, bool):
        return pd.Timestamp("1899-12-30") + pd.Timedelta(days=float(valor))
    texto = limpiar_texto(valor)
    if not texto:
        return pd.NaT
    if re.match(r"^\d{4}-\d{2}-\d{2}", texto):
        return pd.to_datetime(texto[:10], format="%Y-%m-%d", errors="coerce")
    return pd.to_datetime(texto, dayfirst=True, errors="coerce")


@st.cache_data(ttl=600)
def cargar_historico():
    """Lee la pestaña Historico (ventas 2023 en adelante). Si no existe, devuelve una tabla vacía."""
    hoja = conectar_hoja()
    try:
        pestana = hoja.spreadsheet.worksheet(NOMBRE_PESTANA_HISTORICO)
    except Exception:
        return pd.DataFrame(columns=COLUMNAS)
    # Valores sin formato: números como números y fechas como número de serie,
    # así no dependen de la configuración regional de la hoja.
    datos = pestana.get_all_values(value_render_option="UNFORMATTED_VALUE",
                                   date_time_render_option="SERIAL_NUMBER")
    datos = mover_encabezado_al_inicio(datos)
    if len(datos) < 2:
        return pd.DataFrame(columns=COLUMNAS)
    encabezados = [limpiar_texto(x) for x in datos[0]]
    posicion_fecha = encabezados.index("Fecha") if "Fecha" in encabezados else None
    fechas = [fecha_desde_celda(f[posicion_fecha]) if posicion_fecha is not None and len(f) > posicion_fecha else pd.NaT
              for f in datos[1:]]
    tabla = preparar_tabla([encabezados] + [[limpiar_texto(v) for v in f] for f in datos[1:]])
    if posicion_fecha is not None:
        tabla["Fecha"] = pd.to_datetime(pd.Series(fechas, index=tabla.index), errors="coerce")
    return tabla[[c for c in tabla.columns if c in COLUMNAS or c == "_Actividad"]]


def preparar_tabla(datos):
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
        es_traslado = df["Factura #"].astype(str).str.upper().str.startswith("TR-") if "Factura #" in df.columns else pd.Series(False, index=df.index)
        tipos_calculados = df["Codigo Articulo"].apply(clasificar_tipo_venta)
        if "Tipo de Venta" not in df.columns:
            df["Tipo de Venta"] = tipos_calculados
        else:
            df.loc[~es_traslado, "Tipo de Venta"] = tipos_calculados.loc[~es_traslado]
    if "Descripcion" in df.columns:
        tipos = df["Tipo de Venta"] if "Tipo de Venta" in df.columns else [""] * len(df)
        codigos = df["Codigo Articulo"] if "Codigo Articulo" in df.columns else [""] * len(df)
        df["_Actividad"] = [
            clasificar_actividad(desc, tipo, codigo)
            for desc, tipo, codigo in zip(df["Descripcion"], tipos, codigos)
        ]
        # La clasificación se muestra en el campo existente de Google Sheets;
        # _Actividad se conserva solo para cálculos internos del dashboard.
        df["Tipo de Venta"] = df["_Actividad"]
    return df


# -----------------------------------------------------------------------------
# PRESUPUESTO MENSUAL (pestaña "Presupuesto" en el mismo Google Sheets)
# -----------------------------------------------------------------------------
NOMBRE_PESTANA_PRESUPUESTO = "Presupuesto"
ENCABEZADO_PRESUPUESTO = ["Mes", "Presupuesto", "Actualizado"]


def hoja_presupuesto(hoja_ventas, crear=False):
    """Devuelve la pestaña Presupuesto; si no existe y crear=True, la crea."""
    libro = hoja_ventas.spreadsheet
    try:
        return libro.worksheet(NOMBRE_PESTANA_PRESUPUESTO)
    except gspread.exceptions.WorksheetNotFound:
        if not crear:
            return None
        nueva = libro.add_worksheet(title=NOMBRE_PESTANA_PRESUPUESTO, rows=100, cols=3)
        nueva.update(values=[ENCABEZADO_PRESUPUESTO], range_name="A1:C1")
        return nueva


@st.cache_data(ttl=60)
def cargar_presupuestos(_hoja_ventas):
    """Lee los presupuestos guardados: {"2026-10": 373580000.0, ...}."""
    try:
        pestana = hoja_presupuesto(_hoja_ventas)
        if pestana is None:
            return {}
        presupuestos = {}
        for fila in pestana.get_all_values()[1:]:
            if len(fila) >= 2 and limpiar_texto(fila[0]):
                presupuestos[limpiar_texto(fila[0])] = convertir_numero(fila[1])
        return presupuestos
    except Exception:
        return {}


def guardar_presupuesto(hoja_ventas, mes, valor):
    pestana = hoja_presupuesto(hoja_ventas, crear=True)
    marca = datetime.now().strftime("%Y-%m-%d %H:%M")
    filas = pestana.get_all_values()
    for numero_fila, fila in enumerate(filas[1:], start=2):
        if fila and limpiar_texto(fila[0]) == mes:
            pestana.update(values=[[mes, valor, marca]], range_name=f"A{numero_fila}:C{numero_fila}")
            return
    pestana.append_row([mes, valor, marca], value_input_option="RAW")


# -----------------------------------------------------------------------------
# DÍAS HÁBILES (lunes a viernes, sin festivos de Colombia - Ley 51 de 1983)
# El personal comercial trabaja de lunes a viernes. Ojo: el informe de la
# gerencia cuenta lunes a sábado, así que sus días hábiles son más.
# -----------------------------------------------------------------------------
def _domingo_pascua(anio):
    a = anio % 19; b = anio // 100; c = anio % 100
    d = b // 4; e = b % 4; f = (b + 8) // 25; g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30; i = c // 4; k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7; m = (a + 11 * h + 22 * l) // 451
    mes = (h + l - 7 * m + 114) // 31
    dia = ((h + l - 7 * m + 114) % 31) + 1
    return date(anio, mes, dia)


def _siguiente_lunes(dia):
    return dia + timedelta(days=(7 - dia.weekday()) % 7)


def festivos_colombia(anio):
    pascua = _domingo_pascua(anio)
    festivos = {
        date(anio, 1, 1), date(anio, 5, 1), date(anio, 7, 20), date(anio, 8, 7),
        date(anio, 12, 8), date(anio, 12, 25),
        pascua - timedelta(days=3), pascua - timedelta(days=2),        # Jueves y Viernes Santo
        pascua + timedelta(days=43), pascua + timedelta(days=64),      # Ascensión y Corpus Christi
        pascua + timedelta(days=71),                                   # Sagrado Corazón
    }
    for mes, dia in [(1, 6), (3, 19), (6, 29), (8, 15), (10, 12), (11, 1), (11, 11)]:
        festivos.add(_siguiente_lunes(date(anio, mes, dia)))
    return festivos


def es_dia_habil(dia):
    return dia.weekday() < 5 and dia not in festivos_colombia(dia.year)


def dias_habiles(desde, hasta):
    """Días hábiles entre dos fechas, ambas incluidas."""
    if hasta < desde:
        return 0
    return sum(1 for n in range((hasta - desde).days + 1) if es_dia_habil(desde + timedelta(days=n)))


def es_traslado_serie(datos):
    if "Factura #" not in datos.columns:
        return pd.Series(False, index=datos.index)
    return datos["Factura #"].astype(str).str.upper().str.startswith("TR-")

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
hoja = conectar_hoja()
if hoja is None:
    st.stop()

# -----------------------------------------------------------------------------
# CARGA DE PDF EN LA BARRA LATERAL Y FILTROS DE ANÁLISIS
# -----------------------------------------------------------------------------
df_full = cargar_datos()
if not df_full.empty and "Valor Total" not in df_full.columns:
    st.error("La pestaña Hoja1 de Google Sheets no tiene la fila de títulos (Factura #, Fecha, Cliente, ..., "
             "Valor Total). Revisa que la fila 1 tenga los títulos y vuelve a cargar la página.")
    st.stop()

# Se suman las ventas históricas (pestaña Historico) que no estén ya en Hoja1.
# Hoja1 sigue siendo la base donde se cargan los PDF; el histórico solo se lee.
try:
    df_historico = cargar_historico()
except Exception:
    df_historico = pd.DataFrame(columns=COLUMNAS)
if not df_historico.empty:
    facturas_hoja1 = set(df_full["Factura #"].astype(str).str.strip()) if "Factura #" in df_full.columns else set()
    df_historico = df_historico[~df_historico["Factura #"].astype(str).str.strip().isin(facturas_hoja1)]
    df_full = pd.concat([df_historico, df_full], ignore_index=True)
# Hay histórico cuando la base trae ventas de años anteriores al último, ya sea en la pestaña
# Historico o cargadas directamente en Hoja1.
hay_historico = bool(not df_full.empty and "Fecha" in df_full.columns and df_full["Fecha"].notna().any()
                     and df_full["Fecha"].dt.year.min() < df_full["Fecha"].dt.year.max())

if not df_full.empty and "Fecha" in df_full.columns and df_full["Fecha"].notna().any():
    indice_ultima_factura = df_full["Fecha"].idxmax()
    fecha_ultima_factura = df_full.loc[indice_ultima_factura, "Fecha"].strftime("%d/%m/%Y")
    numero_ultima_factura = str(df_full.loc[indice_ultima_factura, "Factura #"]) if "Factura #" in df_full.columns else "No disponible"
    total_facturas_registradas = df_full["Factura #"].nunique() if "Factura #" in df_full.columns else 0
    estado_carga = f"Última factura registrada: {numero_ultima_factura} · {fecha_ultima_factura} · {fnum(total_facturas_registradas)} facturas en total"
else:
    estado_carga = "Aún no hay facturas registradas en la base de datos"

st.markdown(f"""
<div class="app-header">
  <div class="marca">
    <img src="data:image/jpeg;base64,{LOGO_B64}" alt="Magic Print">
    <div>
      <div class="main-title">Magic Print Analytics</div>
      <div class="main-subtitle">Seguimiento de ventas, presupuesto y desempeño comercial</div>
    </div>
  </div>
  <div class="estado">{escape(estado_carga)}</div>
</div>
""", unsafe_allow_html=True)

if st.session_state.get("mensaje_carga"):
    st.success(st.session_state.pop("mensaje_carga"))

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

FILTROS_CON_LISTA = ("Ciudad", "Vendedor", "Cliente", "Tipo de venta")


def limpiar_filtros():
    """Deja todos los filtros como al abrir la app: mes actual y todas las opciones."""
    st.session_state["periodo_sel"] = "Mes actual"
    for nombre in FILTROS_CON_LISTA:
        st.session_state[f"filtro_{nombre}"] = []
    for clave in ("mes_sel", "anio_sel", "f_desde", "f_hasta"):
        st.session_state.pop(clave, None)


with st.container(border=True, key="tarjeta_filtros"):
    ciudades_opc = sorted(df_full["Ciudad"].dropna().astype(str).unique()) if "Ciudad" in df_full.columns else []
    vendedores_opc = sorted(df_full["Vendedor"].dropna().astype(str).unique()) if "Vendedor" in df_full.columns else []
    clientes_opc = sorted(df_full["Cliente"].dropna().astype(str).unique()) if "Cliente" in df_full.columns else []
    tipos_venta_opc = sorted(df_full["Tipo de Venta"].dropna().astype(str).unique()) if "Tipo de Venta" in df_full.columns else []
    sel_ciudades, sel_vendedores, sel_clientes, sel_tipo_venta = [], [], [], []

    opciones_filtro = [("Ciudad", ciudades_opc), ("Vendedor", vendedores_opc), ("Cliente", clientes_opc), ("Tipo de venta", tipos_venta_opc)]
    filtros_visibles = [(nombre, opciones) for nombre, opciones in opciones_filtro if opciones]
    # Solo dos filas. Fila 1: periodo, fechas y "Limpiar filtros". Fila 2: ciudad, vendedor, cliente y tipo de venta.
    fila_1 = st.columns([1.2, 1, 1, 1.2, 0.5, 1], gap="small", vertical_alignment="bottom")
    with fila_1[5]:
        st.button("Limpiar filtros", on_click=limpiar_filtros, use_container_width=True, key="limpiar_filtros")
    fila_2 = st.columns(4, gap="small")
    destinos = {"Ciudad": fila_2[0], "Vendedor": fila_2[1], "Cliente": fila_2[2], "Tipo de venta": fila_2[3]}
    if not df_full.empty and "Fecha" in df_full.columns and not df_full["Fecha"].dropna().empty:
        f_min = df_full["Fecha"].min().date()
        f_max = df_full["Fecha"].max().date()
        hoy = datetime.today().date()
        ultimo = min(f_max, hoy)
        nombres_mes = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio",
                       "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

        def fin_de_mes(dia):
            return dia.replace(day=calendar.monthrange(dia.year, dia.month)[1])

        opciones_periodo = ["Mes actual", "Mes anterior", "Últimos 7 días", "Últimos 30 días",
                            "Año actual", "Elegir un año", "Elegir un mes", "Rango personalizado"]
        with fila_1[0]:
            periodo_sel = st.selectbox("Periodo", opciones_periodo, index=0, key="periodo_sel")

        if periodo_sel == "Mes actual":
            inicio_p, fin_p = ultimo.replace(day=1), ultimo
        elif periodo_sel == "Mes anterior":
            fin_p = ultimo.replace(day=1) - timedelta(days=1)
            inicio_p = fin_p.replace(day=1)
        elif periodo_sel == "Últimos 7 días":
            inicio_p, fin_p = ultimo - timedelta(days=6), ultimo
        elif periodo_sel == "Últimos 30 días":
            inicio_p, fin_p = ultimo - timedelta(days=29), ultimo
        elif periodo_sel == "Año actual":
            inicio_p, fin_p = ultimo.replace(month=1, day=1), ultimo
        else:
            inicio_p, fin_p = ultimo.replace(day=1), ultimo

        # El cuarto campo cambia según el periodo: año o mes a elegir
        with fila_1[3]:
            if periodo_sel == "Elegir un año":
                anios_disp = sorted({d.year for d in df_full["Fecha"].dropna().dt.date}, reverse=True)
                anio_elegido = st.selectbox("Año", anios_disp, index=0, key="anio_sel")
                inicio_p, fin_p = date(anio_elegido, 1, 1), date(anio_elegido, 12, 31)
            elif periodo_sel == "Elegir un mes":
                meses_disp = sorted({(d.year, d.month) for d in df_full["Fecha"].dropna().dt.date}, reverse=True)
                etiquetas_mes = [f"{nombres_mes[m]} {a}" for a, m in meses_disp]
                mes_sel = st.selectbox("Mes", etiquetas_mes, index=0, key="mes_sel")
                a, m = meses_disp[etiquetas_mes.index(mes_sel)]
                inicio_p, fin_p = date(a, m, 1), fin_de_mes(date(a, m, 1))

        # "Desde" y "Hasta" siempre visibles. Con un periodo elegido muestran sus fechas;
        # si se cambian a mano, el periodo pasa a "Rango personalizado".
        def a_rango_personalizado():
            st.session_state["periodo_sel"] = "Rango personalizado"

        if periodo_sel == "Rango personalizado":
            inicio_p = st.session_state.get("f_desde", inicio_p)
            fin_p = st.session_state.get("f_hasta", fin_p)
        inicio_p = min(max(inicio_p, f_min), f_max)
        fin_p = min(max(fin_p, f_min), f_max)
        st.session_state["f_desde"], st.session_state["f_hasta"] = inicio_p, fin_p
        with fila_1[1]:
            inicio_p = st.date_input("Desde", min_value=f_min, max_value=f_max, format="DD/MM/YYYY",
                                     key="f_desde", on_change=a_rango_personalizado)
        with fila_1[2]:
            fin_p = st.date_input("Hasta", min_value=f_min, max_value=f_max, format="DD/MM/YYYY",
                                  key="f_hasta", on_change=a_rango_personalizado)
        if inicio_p > fin_p:   # si quedaron al revés, se ordenan
            inicio_p, fin_p = fin_p, inicio_p
        rango_fechas = (inicio_p, fin_p)
    else:
        rango_fechas = None

    for nombre, opciones in filtros_visibles:
        with destinos[nombre]:
            seleccion = st.multiselect(nombre, opciones, placeholder="Todos", key=f"filtro_{nombre}")
            if nombre == "Ciudad":
                sel_ciudades = seleccion
            elif nombre == "Vendedor":
                sel_vendedores = seleccion
            elif nombre == "Cliente":
                sel_clientes = seleccion
            elif nombre == "Tipo de venta":
                sel_tipo_venta = seleccion

# Aplicar filtros al DataFrame
def aplicar_filtros(datos, rango=None):
    """Filtros de ciudad, vendedor, cliente y tipo de venta, y el rango de fechas si se indica."""
    if isinstance(rango, (tuple, list)) and len(rango) == 2:
        datos = datos[(datos["Fecha"].dt.date >= rango[0]) & (datos["Fecha"].dt.date <= rango[1])]
    if sel_ciudades:
        datos = datos[datos["Ciudad"].astype(str).isin(sel_ciudades)]
    if sel_vendedores:
        datos = datos[datos["Vendedor"].astype(str).isin(sel_vendedores)]
    if sel_clientes:
        datos = datos[datos["Cliente"].astype(str).isin(sel_clientes)]
    if sel_tipo_venta:
        datos = datos[datos["Tipo de Venta"].astype(str).isin(sel_tipo_venta)]
    return datos


def un_anio_antes(dia):
    try:
        return dia.replace(year=dia.year - 1)
    except ValueError:  # 29 de febrero
        return dia.replace(year=dia.year - 1, day=28)


df = df_full.copy()
if df.empty:
    st.info("Google Sheets está conectado, pero todavía no contiene registros.")
df = aplicar_filtros(df, rango_fechas if isinstance(rango_fechas, tuple) else None)

# Mismo periodo del año anterior, con los mismos filtros (para los comparativos)
rango_anterior = None
if isinstance(rango_fechas, (tuple, list)) and len(rango_fechas) == 2:
    rango_anterior = (un_anio_antes(rango_fechas[0]), un_anio_antes(rango_fechas[1]))
df_ant = aplicar_filtros(df_full, rango_anterior) if rango_anterior else df_full.iloc[0:0]
hay_comparativo = hay_historico and rango_anterior is not None and not df_ant.empty

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
    st.markdown('<div class="section-title">Vista previa del PDF</div>', unsafe_allow_html=True)
    df_pdf = pd.DataFrame(registros_pdf, columns=COLUMNAS)
    st.caption(f"Se encontraron {len(df_pdf)} líneas de {df_pdf['Factura #'].nunique()} facturas.")
    st.dataframe(df_pdf, use_container_width=True, hide_index=True)

    informacion = obtener_informacion_duplicados(hoja, registros_pdf)
    repetidas = sorted(informacion["facturas_existentes"])
    nuevas = sorted(informacion["facturas_nuevas"])
    registros_nuevos = informacion["registros_nuevos"]

    if repetidas:
        st.warning(f"El PDF contiene {len(repetidas)} facturas ya cargadas.")
        c1, c2, c3 = st.columns(3)
        c1.metric("Facturas repetidas", len(repetidas))
        c2.metric("Líneas repetidas", informacion["lineas_repetidas"])
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
            if st.button("Cargar solo facturas nuevas", use_container_width=True):
                if not registros_nuevos:
                    st.info("No hay líneas nuevas para cargar. Todos los registros de este PDF ya están registrados.")
                else:
                    try:
                        with st.spinner("Cargando facturas nuevas..."):
                            agregar_facturas_nuevas(hoja, registros_nuevos)
                        st.cache_data.clear()
                        st.session_state["registros_pdf"] = None
                        st.session_state["mensaje_carga"] = f"Se cargaron {len(registros_nuevos)} líneas nuevas correctamente."
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

# -----------------------------------------------------------------------------
# RESUMEN EJECUTIVO: PRESUPUESTO VS. VENTAS DEL MES
# -----------------------------------------------------------------------------
# Colores de series para fondo oscuro (derivados del logo y la paleta de marca)
NAVY, VERDE, CYAN = "#1C2363", "#008257", "#00BEEA"
MAGENTA = "#E0218A"
ALERTA = "#FF8A5B"
# Los gráficos van sobre tarjetas blancas: textos oscuros y cuadrícula gris clara
TXT, TXT_SUAVE, GRID = "#2D2D2D", "#5B6478", "#E9EBF2"
MESES_ES = ["", "enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
            "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def kpi_html(titulo, valor, color="navy", nota="", clase_valor="", barra=None, barra_alerta=False):
    """Tarjeta KPI en HTML. barra = porcentaje (0-100) para dibujar una barra de avance."""
    barra_html = ""
    if barra is not None:
        ancho = max(0.0, min(float(barra), 100.0))
        barra_html = f'<div class="barra{" alerta" if barra_alerta else ""}"><i style="width:{ancho:.1f}%"></i></div>'
    nota_html = f'<div class="small-note">{nota}</div>' if nota else ""
    return (f'<div class="kpi-card {color}"><div class="kpi-title">{escape(titulo)}</div>'
            f'<div class="kpi-value {clase_valor}">{escape(str(valor))}</div>{barra_html}{nota_html}</div>')


def rejilla_kpi(tarjetas, clase=""):
    return f'<div class="kpi-grid {clase}">{"".join(tarjetas)}</div>'


SUBE, BAJA = "#008257", "#D9480F"   # flechas de variación (tema claro)
SUBE_CLARO, BAJA_CLARO = "#008257", "#D9480F"   # sobre tarjetas blancas


def pct_variacion(actual, anterior):
    if not anterior:
        return None
    return (actual - anterior) / abs(anterior) * 100


def flecha(actual, anterior, claro=False, nuevo="nuevo"):
    """Texto corto en HTML: ▲ 12,3% / ▼ 4,0% / nuevo."""
    variacion = pct_variacion(actual, anterior)
    sube, baja = (SUBE_CLARO, BAJA_CLARO) if claro else (SUBE, BAJA)
    if variacion is None:
        return f'<span style="color:{sube};font-weight:700">{nuevo}</span>' if actual else ""
    color = sube if variacion >= 0 else baja
    return (f'<span style="color:{color};font-weight:700">'
            f'{"▲" if variacion >= 0 else "▼"} {fnum(abs(variacion), 1)}%</span>')


if not df_full.empty and "Fecha" in df_full.columns and df_full["Fecha"].notna().any():
    if isinstance(rango_fechas, (tuple, list)) and len(rango_fechas) == 2:
        fecha_ref = rango_fechas[1]
    else:
        fecha_ref = df_full["Fecha"].max().date()
    inicio_mes = fecha_ref.replace(day=1)
    fin_mes = fecha_ref.replace(day=calendar.monthrange(fecha_ref.year, fecha_ref.month)[1])
    corte = fecha_ref
    clave_mes = inicio_mes.strftime("%Y-%m")
    nombre_mes = f"{MESES_ES[inicio_mes.month].capitalize()} {inicio_mes.year}"

    # Con "Año actual" (o un rango personalizado que cruza meses) el resumen cubre todo el periodo:
    # el presupuesto es la suma de los meses del periodo y el mes del corte cuenta completo,
    # porque es la meta de cierre. Si el periodo empieza a mitad de mes, ese mes se prorratea.
    inicio_periodo = inicio_mes
    if (isinstance(rango_fechas, (tuple, list)) and len(rango_fechas) == 2
            and st.session_state.get("periodo_sel") in ("Año actual", "Elegir un año", "Rango personalizado")
            and rango_fechas[0] < inicio_mes):
        inicio_periodo = rango_fechas[0]
    varios_meses = inicio_periodo < inicio_mes
    if varios_meses:
        mes_ini, mes_fin = MESES_ES[inicio_periodo.month].capitalize(), MESES_ES[corte.month].capitalize()
        nombre_periodo = (f"{mes_ini}–{mes_fin} {corte.year}" if inicio_periodo.year == corte.year
                          else f"{mes_ini} {inicio_periodo.year}–{mes_fin} {corte.year}")
    else:
        nombre_periodo = nombre_mes

    del_mes = df_full[(df_full["Fecha"].dt.date >= inicio_periodo) & (df_full["Fecha"].dt.date <= corte)]
    traslado_mes = es_traslado_serie(del_mes)
    ventas_mes = float(del_mes.loc[~traslado_mes, "Valor Total"].sum())
    traslados_mes = float(del_mes.loc[traslado_mes, "Valor Total"].sum())
    documentos_traslado = del_mes.loc[traslado_mes, "Factura #"].nunique() if "Factura #" in del_mes.columns else 0

    presupuestos = cargar_presupuestos(hoja)
    tramos = []   # (desde, fin del mes, clave "AAAA-MM", presupuesto del tramo)
    dia = inicio_periodo
    while dia <= fin_mes:
        fin_tramo = dia.replace(day=calendar.monthrange(dia.year, dia.month)[1])
        clave = dia.strftime("%Y-%m")
        valor = float(presupuestos.get(clave, 0) or 0)
        if dia.day > 1 and valor:
            habiles_del_mes = dias_habiles(dia.replace(day=1), fin_tramo)
            valor = valor * dias_habiles(dia, fin_tramo) / habiles_del_mes if habiles_del_mes else 0
        tramos.append((dia, fin_tramo, clave, valor))
        dia = fin_tramo + timedelta(days=1)
    presupuesto = sum(t[3] for t in tramos)
    meses_sin_presupuesto = [t for t in tramos if not t[3]]

    # El cumplimiento solo compara las ventas de los meses que tienen presupuesto registrado
    fechas_periodo = del_mes["Fecha"].dt.date
    con_presupuesto = pd.Series(False, index=del_mes.index)
    for desde_t, hasta_t, _, valor in tramos:
        if valor:
            con_presupuesto |= (fechas_periodo >= desde_t) & (fechas_periodo <= hasta_t)
    ventas_comparables = float(del_mes.loc[~traslado_mes & con_presupuesto, "Valor Total"].sum())

    habiles_mes = dias_habiles(inicio_periodo, fin_mes)
    habiles_transcurridos = dias_habiles(inicio_periodo, corte)
    habiles_restantes = max(habiles_mes - habiles_transcurridos, 0)
    ritmo_actual = ventas_mes / habiles_transcurridos if habiles_transcurridos else 0
    meta_al_dia = sum(valor * dias_habiles(desde_t, min(corte, hasta_t)) / dias_habiles(desde_t, hasta_t)
                      for desde_t, hasta_t, _, valor in tramos if valor and dias_habiles(desde_t, hasta_t))

    def mes_corto(clave):
        anio, mes = clave.split("-")
        return f"{MESES_ES[int(mes)][:3]} {anio}"

    st.markdown(
        f'<div class="section-title">Resumen ejecutivo <small>{nombre_periodo} · corte {corte:%d/%m/%Y} · '
        f'{habiles_transcurridos} de {habiles_mes} días hábiles</small></div>',
        unsafe_allow_html=True,
    )

    if varios_meses:
        registrados = len(tramos) - len(meses_sin_presupuesto)
        titulo_ppto = (f"Presupuesto de {nombre_periodo}: " + (cop(presupuesto) if presupuesto else "sin registrar")
                       + f" · {registrados} de {len(tramos)} meses registrados")
    else:
        titulo_ppto = f"Presupuesto de {nombre_mes}: " + (cop(presupuesto) if presupuesto else "sin registrar")
    with st.expander(titulo_ppto, expanded=not presupuesto or bool(varios_meses and meses_sin_presupuesto)):
        if varios_meses:
            c_txt, c_mes, c_val, c_btn = st.columns([1.8, 0.9, 1.2, 0.8])
        else:
            c_txt, c_val, c_btn = st.columns([2.2, 1.3, 0.9])
        with c_txt:
            if varios_meses:
                faltan = ", ".join(mes_corto(t[2]) for t in meses_sin_presupuesto)
                st.markdown(
                    '<div class="ppto-ayuda">El presupuesto del periodo es la <b>suma de los meses</b> de la pestaña '
                    '<b>Presupuesto</b> (sin IVA). Elige un mes para registrarlo o corregirlo.'
                    + (f' <b>Sin presupuesto:</b> {faltan}; sus ventas no entran al cumplimiento.' if faltan else '')
                    + '</div>', unsafe_allow_html=True)
            else:
                st.markdown(
                    '<div class="ppto-ayuda">Escribe el <b>presupuesto de ventas sin IVA</b> asignado al mes. '
                    'Se guarda en la pestaña <b>Presupuesto</b> del Google Sheets. El mes es el de la '
                    '<b>fecha final</b> del filtro; para registrar otro mes, cambia esa fecha.</div>',
                    unsafe_allow_html=True,
                )
        clave_editar = clave_mes
        if varios_meses:
            with c_mes:
                claves = [t[2] for t in tramos]
                inicial = claves.index(meses_sin_presupuesto[0][2]) if meses_sin_presupuesto else len(claves) - 1
                clave_editar = st.selectbox("Mes", claves, index=inicial, format_func=mes_corto, key="ppto_mes_sel")
        valor_guardado = float(presupuestos.get(clave_editar, 0) or 0)
        nombre_editar = f"{MESES_ES[int(clave_editar[5:])].capitalize()} {clave_editar[:4]}"
        with c_val:
            texto_presupuesto = st.text_input(
                f"Presupuesto {clave_editar}", value=fnum(valor_guardado) if valor_guardado else "",
                placeholder="Ej: 373.580.000", key=f"ppto_{clave_editar}",
            )
        with c_btn:
            if st.button("Guardar", type="primary", use_container_width=True, key=f"guardar_ppto_{clave_editar}"):
                valor_presupuesto = convertir_numero(texto_presupuesto)
                if valor_presupuesto <= 0:
                    st.error("Escribe un valor mayor que cero.")
                else:
                    try:
                        guardar_presupuesto(hoja, clave_editar, valor_presupuesto)
                        cargar_presupuestos.clear()
                        st.session_state["mensaje_carga"] = f"Presupuesto de {nombre_editar} guardado: {cop(valor_presupuesto)}."
                        st.rerun()
                    except Exception as error:
                        st.error(f"No fue posible guardar el presupuesto: {error}")

    nota_ventas = f"Sin IVA y sin traslados · {inicio_periodo:%d/%m} al {corte:%d/%m/%Y}"
    nota_traslados = f"{fnum(documentos_traslado)} documentos TR · no suman al cumplimiento"
    nota_parcial = ""
    if varios_meses and meses_sin_presupuesto and presupuesto:
        nota_parcial = (f"<br>Solo meses con presupuesto ({cop(ventas_comparables)} vendidos); "
                        f"faltan {len(meses_sin_presupuesto)} meses")
    if presupuesto:
        cumplimiento = ventas_comparables / presupuesto * 100
        cumplimiento_al_dia = ventas_comparables / meta_al_dia * 100 if meta_al_dia else 0
        brecha = presupuesto - ventas_comparables
        if brecha > 0:
            ritmo_requerido = brecha / habiles_restantes if habiles_restantes else brecha
            atrasado = ritmo_requerido > ritmo_actual
            tarjetas = [
                kpi_html("Ventas acumuladas", cop(ventas_mes), "navy", nota_ventas),
                kpi_html("Cumplimiento", f"{fnum(cumplimiento, 1)}%", "verde",
                         f"Al día: {fnum(cumplimiento_al_dia, 1)}% (meta al día {cop(meta_al_dia)})" + nota_parcial,
                         barra=cumplimiento, barra_alerta=cumplimiento_al_dia < 100),
                kpi_html("Brecha presupuestal", cop(brecha), "cyan",
                         f"Presupuesto {cop(presupuesto)} menos ventas"),
                kpi_html("Ritmo requerido por día hábil", cop(ritmo_requerido), "alerta" if atrasado else "verde",
                         (f"{habiles_restantes} días hábiles restantes · ritmo actual {cop(ritmo_actual)}/día"
                          if habiles_restantes else "No quedan días hábiles en el mes"),
                         clase_valor="alerta" if atrasado else "verde"),
                kpi_html("Traslados a Bellatela", cop(traslados_mes), "navy", nota_traslados),
            ]
        else:
            tarjetas = [
                kpi_html("Ventas acumuladas", cop(ventas_mes), "navy", nota_ventas),
                kpi_html("Cumplimiento", f"{fnum(cumplimiento, 1)}%", "verde",
                         f"Al día: {fnum(cumplimiento_al_dia, 1)}%" + nota_parcial, clase_valor="verde", barra=100),
                kpi_html("Brecha presupuestal", "Meta cumplida", "verde",
                         f"Excedente de {cop(-brecha)} sobre {cop(presupuesto)}", clase_valor="verde texto"),
                kpi_html("Ritmo requerido por día hábil", "$0", "verde", f"Ritmo actual {cop(ritmo_actual)}/día"),
                kpi_html("Traslados a Bellatela", cop(traslados_mes), "navy", nota_traslados),
            ]
    else:
        sin_dato = "Registra el presupuesto del periodo" if varios_meses else "Registra el presupuesto del mes"
        tarjetas = [
            kpi_html("Ventas acumuladas", cop(ventas_mes), "navy", nota_ventas),
            kpi_html("Cumplimiento", "— %", "verde", sin_dato),
            kpi_html("Brecha presupuestal", "— $", "cyan", sin_dato),
            kpi_html("Ritmo requerido por día hábil", "— $", "verde", sin_dato),
            kpi_html("Traslados a Bellatela", cop(traslados_mes), "navy", nota_traslados),
        ]
    st.markdown(rejilla_kpi(tarjetas, "cinco"), unsafe_allow_html=True)

    # --- Tendencia del periodo: acumulado real, ruta del presupuesto y proyección ---
    # Si faltan meses con presupuesto, la línea real solo suma esos meses para comparar contra la ruta.
    dias_mes = [inicio_periodo + timedelta(days=n) for n in range((fin_mes - inicio_periodo).days + 1)]
    ventas_grafico = del_mes.loc[~traslado_mes & con_presupuesto] if presupuesto else del_mes.loc[~traslado_mes]
    vendido_grafico = ventas_comparables if presupuesto else ventas_mes
    diario = ventas_grafico.groupby(ventas_grafico["Fecha"].dt.date)["Valor Total"].sum()
    acumulado_real, total_corrido = [], 0.0
    for dia in dias_mes:
        if dia > corte:
            break
        total_corrido += float(diario.get(dia, 0))
        acumulado_real.append(total_corrido)
    proyeccion_cierre = vendido_grafico + ritmo_actual * habiles_restantes

    # Ruta del presupuesto: cada mes reparte su meta en sus días hábiles
    ruta, meta_corrida = [], 0.0
    cuota_diaria = {clave: valor / dias_habiles(desde_t, hasta_t)
                    for desde_t, hasta_t, clave, valor in tramos if valor and dias_habiles(desde_t, hasta_t)}
    for dia in dias_mes:
        if es_dia_habil(dia):
            meta_corrida += cuota_diaria.get(dia.strftime("%Y-%m"), 0)
        ruta.append(meta_corrida)

    # Mismo mes en los años anteriores: al mismo día y el mes completo (sin traslados)
    def mismo_dia_en(anio, dia):
        try:
            return dia.replace(year=anio)
        except ValueError:  # 29 de febrero
            return dia.replace(year=anio, day=28)

    def en_millones(valor):
        return f"${fnum(valor / 1e6, 1)}M"

    comparables = []   # (año, ventas al mismo día, ventas del mes completo)
    if hay_historico:
        ventas_sin_traslados = df_full.loc[~es_traslado_serie(df_full) & df_full["Fecha"].notna()]
        fechas_validas = ventas_sin_traslados["Fecha"].dt.date
        salto = corte.year - inicio_periodo.year   # el periodo puede empezar el año anterior
        for anio in range(int(ventas_sin_traslados["Fecha"].dt.year.min()), inicio_periodo.year):
            ini_a, corte_a = mismo_dia_en(anio, inicio_periodo), mismo_dia_en(anio + salto, corte)
            fin_a = corte_a.replace(day=calendar.monthrange(corte_a.year, corte_a.month)[1])
            del_anio = ventas_sin_traslados.loc[(fechas_validas >= ini_a) & (fechas_validas <= fin_a)]
            if del_anio.empty:
                continue
            comparables.append((anio,
                                float(del_anio.loc[del_anio["Fecha"].dt.date <= corte_a, "Valor Total"].sum()),
                                float(del_anio["Valor Total"].sum())))
    if comparables:
        promedio_al_dia = sum(c[1] for c in comparables) / len(comparables)
        promedio_mes = sum(c[2] for c in comparables) / len(comparables)
        anios_txt = f"{comparables[0][0]}–{comparables[-1][0]}" if len(comparables) > 1 else str(comparables[0][0])
        detalle_anios = "<br>".join(
            f"{anio}: {en_millones(al_dia)} · este año {flecha(ventas_mes, al_dia)}"
            for anio, al_dia, _ in reversed(comparables))
        if varios_meses:
            titulo_historico = (f"{MESES_ES[inicio_periodo.month].capitalize()}–{MESES_ES[corte.month]} "
                                f"{anios_txt} al mismo día (promedio)")
            nota_completo = f"Hasta fin de {MESES_ES[corte.month]}, promedio"
        else:
            titulo_historico = f"{MESES_ES[inicio_mes.month].capitalize()} {anios_txt} al mismo día (promedio)"
            nota_completo = "Mes completo, promedio"
        ventas_historicas_html = kpi_html(
            titulo_historico, cop(promedio_al_dia), "cyan",
            f"Este año {flecha(ventas_mes, promedio_al_dia)} vs el promedio<br>{detalle_anios}"
            f"<br>{nota_completo}: {en_millones(promedio_mes)}")
    else:
        ventas_historicas_html = kpi_html("Ventas históricas comparables", "Sin histórico", "cyan",
                                          "Agrega ventas de años anteriores en Google Sheets", clase_valor="texto")

    c_graf, c_ref = st.columns([2.1, 1])
    with c_graf:
        with st.container(key="graf_tendencia"):
            st.markdown('<div class="hd"><h2>Tendencia de ventas y proyección de cierre</h2>'
                        f'<span class="tag">{nombre_periodo}</span></div>'
                        '<p class="sub">Ventas acumuladas sin traslados frente a la ruta del presupuesto por día hábil'
                        + (' (solo meses con presupuesto)' if presupuesto and meses_sin_presupuesto else '') + '</p>',
                        unsafe_allow_html=True)
            figura = go.Figure()
            if presupuesto and habiles_mes:
                figura.add_scatter(x=dias_mes, y=ruta, name="Ruta del presupuesto", mode="lines",
                                   line=dict(color=CYAN, width=2, dash="dot"),
                                   hovertemplate="%{x|%d/%m}<br>Meta acumulada $%{y:,.0f}<extra></extra>")
            figura.add_scatter(x=dias_mes[:len(acumulado_real)], y=acumulado_real, name="Ventas acumuladas",
                               mode="lines" if varios_meses else "lines+markers",
                               line=dict(color=NAVY, width=3), marker=dict(size=5),
                               hovertemplate="%{x|%d/%m}<br>Vendido $%{y:,.0f}<extra></extra>")
            if habiles_transcurridos and corte < fin_mes:
                dias_futuros = [d for d in dias_mes if d >= corte]
                valores_proyeccion = [vendido_grafico + ritmo_actual * dias_habiles(corte + timedelta(days=1), d)
                                      for d in dias_futuros]
                figura.add_scatter(x=dias_futuros, y=valores_proyeccion, name="Proyección al ritmo actual",
                                   mode="lines", line=dict(color=VERDE, width=2, dash="dash"),
                                   hovertemplate="%{x|%d/%m}<br>Proyección $%{y:,.0f}<extra></extra>")
            if presupuesto:
                figura.add_hline(y=presupuesto, line=dict(color=ALERTA, width=1), opacity=0.6,
                                 annotation_text=f"Presupuesto {cop(presupuesto)}", annotation_position="top left",
                                 annotation_font=dict(size=11, color=ALERTA))
            figura.update_layout(
                height=360, margin=dict(l=8, r=8, t=10, b=8), separators=",.",
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(size=12, color=TXT), hoverlabel=dict(bgcolor=NAVY, font_color="#fff"),
                legend=dict(orientation="h", y=-0.15, x=0.5, xanchor="center"),
                xaxis=dict(showgrid=False, tickformat="%d/%m"),
                yaxis=dict(gridcolor=GRID, tickprefix="$", tickformat="~s", rangemode="tozero"),
            )
            st.plotly_chart(figura, use_container_width=True, config={"displayModeBar": False})
            st.markdown('<div class="aviso">La proyección reparte el ritmo actual en los días hábiles que faltan '
                        '(lunes a viernes sin festivos). Es una referencia: todavía no considera la estacionalidad '
                        'ni la forma habitual en que se distribuyen las ventas dentro del mes.</div>',
                        unsafe_allow_html=True)
    with c_ref:
        with st.container(border=True, key="tarjeta_referencias"):
            st.markdown('<div class="hd"><h2>Referencias para la meta</h2></div>'
                        '<p class="sub">Tres puntos de comparación para leer el resultado</p>',
                        unsafe_allow_html=True)
            referencias = [
                kpi_html("Presupuesto asignado", cop(presupuesto) if presupuesto else "Sin registrar", "navy",
                         "Qué resultado exige la dirección", clase_valor="" if presupuesto else "texto"),
                ventas_historicas_html,
                kpi_html("Proyección de cierre", cop(proyeccion_cierre) if habiles_transcurridos else "Sin datos", "verde",
                         (f"{fnum(proyeccion_cierre / presupuesto * 100, 1)}% del presupuesto · " if presupuesto and habiles_transcurridos else "")
                         + "ritmo actual por día hábil" + (f" · cierre de {MESES_ES[corte.month]}" if varios_meses else "")),
            ]
            st.markdown(rejilla_kpi(referencias, "una"), unsafe_allow_html=True)

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
es_metro = unidades.isin({"MTS", "MT", "M"}) if not unidades.empty else pd.Series(dtype=bool)
actividad = df["_Actividad"] if "_Actividad" in df.columns else pd.Series("Otros", index=df.index)
cantidad_metros_sublimacion = df.loc[es_metro & actividad.eq("Sublimación"), "Cantidad"].sum() if not unidades.empty else 0
cantidad_metros_base = df.loc[es_metro & actividad.eq("Base textil"), "Cantidad"].sum() if not unidades.empty else 0
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
PALETA = [NAVY, CYAN, VERDE, "#5B6BC0", "#FFC145", "#66D8F2", "#F06BB4", "#7FE0BE", "#B9AEFF", "#FFD98A"]
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


def filas(items, color=None, anterior=None, diferencia=False, colores=None):
    """Lista con barras de color: nombre, barra y valor con porcentaje.
    anterior = {nombre: valor del año anterior} agrega la variación;
    diferencia=True agrega además cuánto subió o bajó en pesos;
    colores = lista de colores (los del gráfico de anillo) y un punto de color junto al nombre."""
    if not items:
        return '<p class="sub">Sin datos con los filtros seleccionados.</p>'
    mayor = max(v for _, v in items) or 1
    html = ""
    for i, (nombre, valor) in enumerate(items):
        c = colores[i % len(colores)] if colores else (color or PALETA[i % len(PALETA)])
        punto = f'<b style="color:{c};font-size:15px">●</b> ' if colores else ""
        html += (
            f'<div class="sr"><span class="n" title="{escape(str(nombre))}">{punto}{escape(str(nombre))}</span>'
            f'<span class="t"><i style="width:{valor / mayor * 100:.1f}%;background:{c}"></i></span>'
            f'<span class="v">{cop(valor)} ({fnum(valor / total_ventas * 100, 1)}%)'
            f'{" " + flecha(valor, anterior.get(nombre, 0), claro=True) if anterior is not None else ""}'
            f'{" " + con_signo(valor - anterior.get(nombre, 0)) if anterior is not None and diferencia else ""}</span></div>'
        )
    # El espacio final evita que la última fila quede cortada por el borde de la tarjeta
    return f'<div class="seg">{html}</div><div style="height:18px"></div>'


def con_signo(valor):
    """Diferencia en pesos con signo, en millones si es grande: +$26,0M / −$158,3M."""
    return ("+" if valor >= 0 else "−") + corto(abs(valor))


def mostrar(figura, alto=320, leyenda=False):
    figura.update_layout(
        height=alto, margin=dict(l=8, r=8, t=4, b=8), showlegend=leyenda, separators=",.",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(size=12, color=TXT), hoverlabel=dict(bgcolor=NAVY, font_color="#fff"),
        legend=dict(orientation="h", y=-0.12, x=0.5, xanchor="center"),
    )
    st.plotly_chart(figura, use_container_width=True, config={"displayModeBar": False})


def barras_h(datos, x, y, color, n=10, anterior=None):
    d = datos.sort_values(x, ascending=False).head(n).iloc[::-1]
    textos = [f"{corto(v)} - {fnum(v / total_ventas * 100, 0)}%" for v in d[x]]
    if anterior is not None:
        textos = [f"{t} {flecha(v, anterior.get(nombre, 0), claro=True)}" for t, v, nombre in zip(textos, d[x], d[y])]
    maximo = float(d[x].max()) if not d.empty else 1
    figura = go.Figure(go.Bar(
        x=d[x], y=d[y].astype(str).str.slice(0, 32), orientation="h", marker_color=color,
        text=textos, textposition="outside", cliponaxis=False,
        textfont=dict(size=11, color=TXT),
        hovertemplate="%{y}<br>$%{x:,.0f}<extra></extra>",
    ))
    # Reserva espacio para que el valor del primer lugar no quede cortado.
    figura.update_xaxes(
        showgrid=True, gridcolor=GRID, zeroline=False,
        tickprefix="$", tickformat="~s", range=[0, maximo * (1.6 if anterior is not None else 1.25)],
    )
    figura.update_yaxes(showgrid=False)
    figura.update_layout(margin=dict(l=8, r=215 if anterior is not None else 155, t=4, b=8), uniformtext_minsize=9)
    mostrar(figura)


def anillo(items, colores, alto=215, leyenda=True):
    total = sum(v for _, v in items)
    figura = go.Figure(go.Pie(
        labels=[str(n) for n, _ in items], values=[v for _, v in items], hole=0.62, sort=False,
        marker=dict(colors=colores, line=dict(color="#FFFFFF", width=2)), textinfo="percent",
        textfont=dict(color="#FFFFFF", size=12),
        hovertemplate="%{label}<br>$%{value:,.0f} (%{percent})<extra></extra>",
    ))
    figura.add_annotation(text=f"<b>{corto(total)}</b>", x=0.5, y=0.5, showarrow=False, font=dict(size=15, color=TXT))
    mostrar(figura, alto=alto, leyenda=leyenda)


def anillos_en_linea(items_tipo, items_pago):
    figura = make_subplots(
        rows=1, cols=2, specs=[[{"type": "domain"}, {"type": "domain"}]],
        horizontal_spacing=0.04,
    )
    for indice, (items, colores, titulo) in enumerate([
        (items_tipo, [VERDE, CYAN, NAVY, "#7FC9B0", "#9FE6F6", "#8A90B8"], "Tipo de venta"),
        (items_pago, [NAVY, CYAN, VERDE, "#8A90B8", "#7FC9B0", "#9FE6F6"], "Forma de pago"),
    ], start=1):
        total = sum(valor for _, valor in items)
        figura.add_trace(go.Pie(
            labels=[str(nombre) for nombre, _ in items],
            values=[valor for _, valor in items],
            hole=0.62, sort=False, textinfo="percent",
            marker=dict(colors=colores, line=dict(color="#ffffff", width=2)),
            hovertemplate="%{label}<br>$%{value:,.0f} (%{percent})<extra></extra>",
            name=titulo,
        ), row=1, col=indice)
        x_centro = 0.25 if indice == 1 else 0.75
        figura.add_annotation(
            text=f"<b>{titulo}</b>", x=x_centro, y=0.98,
            xref="paper", yref="paper", showarrow=False,
            font=dict(size=11, color="#1C2363"),
        )
        figura.add_annotation(
            text=f"<b>{corto(total)}</b>", x=x_centro, y=0.50,
            xref="paper", yref="paper", showarrow=False,
            font=dict(size=13, color=NAVY),
        )
    mostrar(figura, alto=430, leyenda=True)


def serie(columna):
    if columna not in df.columns:
        return []
    s = df.assign(_k=df[columna].fillna("Sin dato").replace("", "Sin dato")).groupby("_k")["Valor Total"].sum()
    return list(s.sort_values(ascending=False).items())


es_traslado_filtro = es_traslado_serie(df)
ventas_clientes = df.loc[~es_traslado_filtro, "Valor Total"].sum()
ventas_traslados = df.loc[es_traslado_filtro, "Valor Total"].sum()


def precio_por_metro(datos):
    metros = datos["Cantidad"].sum()
    return datos["Valor Total"].sum() / metros if metros else 0


def metricas_basicas(datos):
    """Las mismas cifras de los indicadores, para comparar con el año anterior."""
    traslado = es_traslado_serie(datos)
    unidad = datos["Unidad"].fillna("").astype(str).str.upper().str.strip() if "Unidad" in datos.columns else pd.Series("", index=datos.index)
    metro = unidad.isin({"MTS", "MT", "M"})
    act = datos["_Actividad"] if "_Actividad" in datos.columns else pd.Series("Otros", index=datos.index)
    n_facturas = datos["Factura #"].nunique()
    return {
        "ventas": datos.loc[~traslado, "Valor Total"].sum(),
        "facturas": n_facturas,
        "clientes": datos["Cliente"].nunique(),
        "ticket": datos["Valor Total"].sum() / n_facturas if n_facturas else 0,
        "metros_sub": datos.loc[metro & act.eq("Sublimación"), "Cantidad"].sum(),
        "precio_m_sub": precio_por_metro(datos.loc[~traslado & metro & act.eq("Sublimación")]),
        "metros_base": datos.loc[metro & act.eq("Base textil"), "Cantidad"].sum(),
        "kilos": datos.loc[unidad.isin({"KLS", "KG", "KGM", "KILO", "KILOS"}), "Cantidad"].sum(),
    }


m_actual = metricas_basicas(df)
if hay_comparativo:
    m_ant = metricas_basicas(df_ant)
    anio_ant = rango_anterior[0].year

    def vs(clave, actual):
        return f"{flecha(actual, m_ant[clave])} vs {anio_ant}"
else:
    def vs(clave, actual):
        return ""


def con_vs(nota, clave, actual):
    comparacion = vs(clave, actual)
    return f"{nota} · {comparacion}" if comparacion else nota
titulo_comparativo = (f" · comparado con {rango_anterior[0]:%d/%m/%Y} – {rango_anterior[1]:%d/%m/%Y}"
                      if hay_comparativo else "")
st.markdown(f'<div class="section-title">Indicadores comerciales <small>{periodo} · según los filtros{titulo_comparativo}</small></div>',
            unsafe_allow_html=True)
indicadores = [
    kpi_html("Ventas a clientes", cop(ventas_clientes), "navy", con_vs("Sin IVA y sin traslados", "ventas", ventas_clientes)),
    kpi_html("Traslados a Bellatela", cop(ventas_traslados), "cyan", f"Total con traslados: {cop(ventas)}"),
    kpi_html("Facturas realizadas", fnum(facturas), "verde", con_vs("Documentos en el periodo", "facturas", facturas)),
    kpi_html("Clientes atendidos", fnum(clientes), "navy", con_vs(f"En {fnum(df['Ciudad'].nunique())} ciudades", "clientes", clientes)),
    kpi_html("Ticket promedio", cop(ticket), "verde", con_vs("Valor promedio por factura", "ticket", ticket)),
    kpi_html("Metros de sublimación", f"{fnum(cantidad_metros_sublimacion, 2)} m", "cyan", con_vs("Según actividad facturada", "metros_sub", cantidad_metros_sublimacion)),
    kpi_html("Precio por metro de sublimación", cop(m_actual["precio_m_sub"]), "verde",
             con_vs("Valor vendido entre metros vendidos", "precio_m_sub", m_actual["precio_m_sub"])),
    kpi_html("Metros de base textil", f"{fnum(cantidad_metros_base, 2)} m", "navy", con_vs("Según actividad facturada", "metros_base", cantidad_metros_base)),
    kpi_html("Kilos vendidos", f"{fnum(cantidad_kilos, 2)} kg", "verde", con_vs("Según unidad facturada", "kilos", cantidad_kilos)),
    kpi_html("Forma de pago dominante", forma_pago_principal, "cyan",
             f"{fnum(forma_pago_porcentaje, 1)}% del valor vendido", clase_valor="texto"),
    kpi_html("Tipo de venta dominante", tipo_venta_principal, "navy",
             f"{fnum(tipo_venta_porcentaje, 1)}% del valor vendido", clase_valor="texto"),
    kpi_html("Día de mayor venta", dia_mayor, "verde", f"{cop(valor_mayor)} vendidos", clase_valor="texto"),
    kpi_html("Día de menor venta", dia_menor, "cyan", f"{cop(valor_menor)} vendidos", clase_valor="texto"),
]
st.markdown(rejilla_kpi(indicadores), unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# BLOQUE DE GRÁFICOS Y ANÁLISIS COMERCIAL
# -----------------------------------------------------------------------------
st.markdown('<div class="section-title">Análisis comercial detallado</div>', unsafe_allow_html=True)

with st.container(key="graf_diario"):
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
        yaxis=dict(rangemode="tozero", gridcolor=GRID, tickformat="d"),
        yaxis2=dict(overlaying="y", side="right", rangemode="tozero",
                    showgrid=False, tickprefix="$", tickformat=".3~s"),
    )
    mostrar(figura, alto=430, leyenda=True)

if hay_historico and isinstance(rango_fechas, (tuple, list)) and len(rango_fechas) == 2:
    with st.container(key="graf_mensual"):
        anio_actual = rango_fechas[1].year
        anios = [anio_actual - 1, anio_actual]
        base_mensual = aplicar_filtros(df_full)
        base_mensual = base_mensual.loc[~es_traslado_serie(base_mensual) & base_mensual["Fecha"].dt.year.isin(anios)]
        mensual = (base_mensual.groupby([base_mensual["Fecha"].dt.year, base_mensual["Fecha"].dt.month])["Valor Total"]
                   .sum().unstack(0).reindex(index=range(1, 13), columns=anios).fillna(0))
        tarjeta(f"Ventas mes a mes: {anios[1]} frente a {anios[0]}",
                "Ventas sin traslados con los filtros de ciudad, vendedor, cliente y tipo de venta (no aplica el filtro de fechas)",
                f"{anios[1]}: {corto(mensual[anios[1]].sum())} · {anios[0]}: {corto(mensual[anios[0]].sum())}")
        etiquetas = [m.capitalize()[:3] for m in MESES_ES[1:]]
        figura = go.Figure()
        for anio, color in zip(anios, ["#B7BCCB", NAVY]):
            valores = mensual[anio].tolist()
            if anio == anio_actual:   # sin barras en meses que aún no llegan
                valores = [v if m <= rango_fechas[1].month else None for m, v in zip(range(1, 13), valores)]
            figura.add_bar(x=etiquetas, y=valores, name=str(anio), marker_color=color,
                           text=[corto(v) if v else "" for v in valores], textposition="outside",
                           textfont=dict(size=10, color=TXT), cliponaxis=False,
                           hovertemplate="%{x} " + str(anio) + "<br>$%{y:,.0f}<extra></extra>")
        figura.update_layout(barmode="group", bargap=0.25,
                             xaxis=dict(showgrid=False), yaxis=dict(gridcolor=GRID, tickprefix="$", tickformat="~s"))
        mostrar(figura, alto=380, leyenda=True)

c1, c2 = st.columns(2)
with c1:
    with st.container(key="graf_tipo"):
        items_tipo = serie("Tipo de Venta")
        tarjeta("Ventas por tipo de venta", "Participación sobre el valor vendido", f"{len(items_tipo)} tipos")
        if items_tipo:
            colores_anillo = [NAVY, CYAN, VERDE, "#5B6BC0", "#FFC145", "#66D8F2", "#F06BB4"]
            anillo(items_tipo, colores_anillo, alto=300, leyenda=False)
            # La lista hace de leyenda: cada fila con el color de su parte del anillo
            if hay_comparativo:
                st.markdown(f'<p class="sub">Valor, participación y variación contra {anio_ant}</p>'
                            + filas(items_tipo, anterior=df_ant.groupby("Tipo de Venta")["Valor Total"].sum().to_dict(),
                                    diferencia=True, colores=colores_anillo), unsafe_allow_html=True)
            else:
                st.markdown(filas(items_tipo, colores=colores_anillo), unsafe_allow_html=True)
with c2:
    with st.container(key="graf_pago"):
        items_pago = serie("Forma de Pago")
        tarjeta("Ventas por forma de pago", "Participación sobre el valor vendido", f"{len(items_pago)} formas")
        if items_pago:
            colores_anillo = [VERDE, CYAN, NAVY, "#5B6BC0", "#FFC145", "#66D8F2", "#F06BB4"]
            anillo(items_pago, colores_anillo, alto=300, leyenda=False)
            # La lista hace de leyenda: cada fila con el color de su parte del anillo
            if hay_comparativo:
                st.markdown(f'<p class="sub">Valor, participación y variación contra {anio_ant}</p>'
                            + filas(items_pago, anterior=df_ant.groupby("Forma de Pago")["Valor Total"].sum().to_dict(),
                                    diferencia=True, colores=colores_anillo), unsafe_allow_html=True)
            else:
                st.markdown(filas(items_pago, colores=colores_anillo), unsafe_allow_html=True)

c1, c2 = st.columns(2)
with c1:
    with st.container(key="graf_ciudades"):
        tarjeta("Top 10 ciudades por ventas", "Valor vendido, participación y variación contra el año anterior" if hay_comparativo else "Valor vendido y participación sobre el total")
        barras_h(df.groupby("Ciudad", as_index=False)["Valor Total"].sum(), "Valor Total", "Ciudad", VERDE,
                 anterior=(df_ant.groupby("Ciudad")["Valor Total"].sum().to_dict() if hay_comparativo else None))
with c2:
    with st.container(key="graf_articulos"):
        tarjeta("Top 10 artículos más vendidos", "Valor vendido, participación y variación contra el año anterior" if hay_comparativo else "Valor vendido y participación sobre el total")
        barras_h(df.groupby("Descripcion", as_index=False)["Valor Total"].sum(), "Valor Total", "Descripcion", NAVY,
                 anterior=(df_ant.groupby("Descripcion")["Valor Total"].sum().to_dict() if hay_comparativo else None))

c1, c2 = st.columns(2)
with c1:
    with st.container(key="graf_clientes"):
        top_clientes = serie("Cliente")[:10]
        tarjeta("Ranking de facturación por cliente", "Top 10 clientes por valor vendido y variación contra el año anterior" if hay_comparativo else "Top 10 clientes por valor vendido", f"{fnum(clientes)} clientes · {corto(ventas)}")
        st.markdown(filas(top_clientes, anterior=(df_ant.groupby("Cliente")["Valor Total"].sum().to_dict() if hay_comparativo else None)), unsafe_allow_html=True)
with c2:
    with st.container(key="graf_vendedores"):
        vendedores = serie("Vendedor")[:10]
        tarjeta("Desempeño por vendedor", "Valor vendido, participación y variación contra el año anterior" if hay_comparativo else "Valor vendido y participación", f"{len(vendedores)} vendedores")
        st.markdown(filas(vendedores, anterior=(df_ant.groupby("Vendedor")["Valor Total"].sum().to_dict() if hay_comparativo else None)), unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# CLIENTES: CONCENTRACIÓN Y ROTACIÓN (contra el mismo periodo del año anterior)
# -----------------------------------------------------------------------------
if hay_comparativo:
    st.markdown(f'<div class="section-title">Clientes: concentración y rotación <small>{periodo} frente al '
                f'mismo periodo de {anio_ant} · sin traslados</small></div>', unsafe_allow_html=True)
    por_cliente = df.loc[~es_traslado_serie(df)].groupby("Cliente")["Valor Total"].sum()
    por_cliente_ant = df_ant.loc[~es_traslado_serie(df_ant)].groupby("Cliente")["Valor Total"].sum()
    venta_actual, venta_ant = float(por_cliente.sum()), float(por_cliente_ant.sum())

    def peso_top10(valores):
        return valores.nlargest(10).sum() / valores.sum() * 100 if valores.sum() else 0

    peso_hoy, peso_antes = peso_top10(por_cliente), peso_top10(por_cliente_ant)
    nuevos = por_cliente[~por_cliente.index.isin(por_cliente_ant.index)]
    perdidos = por_cliente_ant[~por_cliente_ant.index.isin(por_cliente.index)]
    repiten = por_cliente[por_cliente.index.isin(por_cliente_ant.index)]
    repiten_ant = por_cliente_ant[por_cliente_ant.index.isin(por_cliente.index)]

    if not nuevos.empty:
        mayor_nuevo, valor_mayor_nuevo = nuevos.idxmax(), float(nuevos.max())
        tarjeta_nuevo = kpi_html(
            "Mayor cliente nuevo", str(mayor_nuevo).title(), "cyan",
            f"Compró {corto(valor_mayor_nuevo)} ({fnum(valor_mayor_nuevo / venta_actual * 100, 1)}% del total)<br>"
            f"Sin él, las ventas irían {flecha(venta_actual - valor_mayor_nuevo, venta_ant)} vs {anio_ant}",
            clase_valor="texto")
    else:
        tarjeta_nuevo = kpi_html("Mayor cliente nuevo", "Ninguno", "cyan", "No hay clientes nuevos en el periodo",
                                 clase_valor="texto")
    diferencia_peso = peso_hoy - peso_antes
    st.markdown(rejilla_kpi([
        kpi_html("Peso de los 10 mayores clientes", f"{fnum(peso_hoy, 1)}%", "navy",
                 f"En {anio_ant}: {fnum(peso_antes, 1)}% · "
                 f"<b>{'+' if diferencia_peso >= 0 else '−'}{fnum(abs(diferencia_peso), 1)} puntos</b>"),
        tarjeta_nuevo,
        kpi_html("Clientes que no volvieron", fnum(len(perdidos)), "alerta",
                 f"Compraron {corto(perdidos.sum())} en {anio_ant}", clase_valor="alerta"),
        kpi_html("Clientes nuevos", fnum(len(nuevos)), "verde",
                 f"Compraron {corto(nuevos.sum())} en este periodo", clase_valor="verde"),
        kpi_html("Clientes que repiten", fnum(len(repiten)), "navy",
                 f"{corto(repiten.sum())} · {flecha(repiten.sum(), repiten_ant.sum())} vs {anio_ant}"),
    ], "cinco"), unsafe_allow_html=True)

    c1, c2 = st.columns([1.4, 1])
    with c1:
        with st.container(key="graf_puente"):
            tarjeta(f"De las ventas de {anio_ant} a las de este periodo",
                    "Cuánto se perdió por clientes que no volvieron, cuánto aportaron los nuevos y cómo cambiaron los que repiten",
                    f"{con_signo(venta_actual - venta_ant)}")
            pasos = [(f"Ventas {anio_ant}", venta_ant, "absolute"),
                     ("No volvieron", -float(perdidos.sum()), "relative"),
                     ("Nuevos", float(nuevos.sum()), "relative"),
                     ("Repiten (cambio)", float(repiten.sum() - repiten_ant.sum()), "relative"),
                     (f"Ventas {rango_fechas[1].year}", venta_actual, "total")]
            figura = go.Figure(go.Waterfall(
                x=[p[0] for p in pasos], y=[p[1] for p in pasos], measure=[p[2] for p in pasos],
                text=[corto(p[1]) if p[2] != "relative" else con_signo(p[1]) for p in pasos],
                textposition="outside", cliponaxis=False, textfont=dict(size=11, color=TXT),
                connector=dict(line=dict(color=GRID)),
                increasing=dict(marker=dict(color=VERDE)), decreasing=dict(marker=dict(color=ALERTA)),
                totals=dict(marker=dict(color=NAVY)),
                hovertemplate="%{x}<br>$%{y:,.0f}<extra></extra>",
            ))
            figura.update_layout(xaxis=dict(showgrid=False),
                                 yaxis=dict(gridcolor=GRID, tickprefix="$", tickformat="~s",
                                            range=[0, max(venta_ant, venta_actual) * 1.25]))
            mostrar(figura, alto=360)
    with c2:
        with st.container(key="graf_perdidos"):
            tarjeta(f"Mayores clientes que no volvieron", f"Lo que compraron en {anio_ant}",
                    f"{fnum(len(perdidos))} clientes")
            lista = perdidos.sort_values(ascending=False).head(8)
            if lista.empty:
                st.markdown('<p class="sub">Todos los clientes del año anterior volvieron a comprar.</p>',
                            unsafe_allow_html=True)
            else:
                mayor = float(lista.max()) or 1
                st.markdown('<div class="seg">' + "".join(
                    f'<div class="sr"><span class="n" title="{escape(str(n))}">{escape(str(n))}</span>'
                    f'<span class="t"><i style="width:{v / mayor * 100:.1f}%;background:{ALERTA}"></i></span>'
                    f'<span class="v">{cop(v)}</span></div>' for n, v in lista.items())
                    + '</div><div style="height:18px"></div>',
                    unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# TABLA DE DETALLE
# -----------------------------------------------------------------------------
st.markdown('<div class="section-title">Detalle de facturación</div>', unsafe_allow_html=True)
def detalle_a_excel(datos, titulo_periodo):
    """Convierte el detalle filtrado en un archivo Excel (.xlsx) con formato."""
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter
    salida = io.BytesIO()
    datos = datos.copy()
    if "Fecha" in datos.columns:
        datos["Fecha"] = pd.to_datetime(datos["Fecha"], errors="coerce").dt.date
    with pd.ExcelWriter(salida, engine="openpyxl") as escritor:
        datos.to_excel(escritor, index=False, sheet_name="Detalle", startrow=2)
        hoja_xl = escritor.sheets["Detalle"]
        hoja_xl["A1"] = f"Magic Print - Detalle de facturación ({titulo_periodo})"
        hoja_xl["A1"].font = Font(bold=True, size=13, color="1C2363")
        relleno = PatternFill("solid", fgColor="1C2363")
        formatos = {"Fecha": "DD/MM/YYYY", "Cantidad": "#,##0.00", "Precio Unitario": "$#,##0",
                    "Valor Total": "$#,##0;-$#,##0", "% IVA": "0"}
        for posicion, columna in enumerate(datos.columns, start=1):
            celda = hoja_xl.cell(row=3, column=posicion)
            celda.font = Font(bold=True, color="FFFFFF")
            celda.fill = relleno
            celda.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            letra = get_column_letter(posicion)
            ancho = max([len(str(columna))] + [len(str(v)) for v in datos[columna].head(500)]) + 2
            hoja_xl.column_dimensions[letra].width = min(max(ancho, 10), 45)
            if columna in formatos:
                for fila in range(4, len(datos) + 4):
                    hoja_xl.cell(row=fila, column=posicion).number_format = formatos[columna]
        hoja_xl.freeze_panes = "A4"
        hoja_xl.auto_filter.ref = f"A3:{get_column_letter(len(datos.columns))}{len(datos) + 3}"
    return salida.getvalue()


with st.container(border=True, key="tarjeta_detalle"):
    df_detalle = df.drop(columns=["_Actividad"], errors="ignore")
    c_info, c_boton = st.columns([3, 1])
    with c_info:
        st.markdown(f'<p class="sub">{fnum(len(df_detalle))} líneas según los filtros · {periodo}</p>',
                    unsafe_allow_html=True)
    with c_boton:
        nombre_archivo = "Detalle_facturacion_MagicPrint"
        if isinstance(rango_fechas, (tuple, list)) and len(rango_fechas) == 2:
            nombre_archivo += f"_{rango_fechas[0]:%Y%m%d}_{rango_fechas[1]:%Y%m%d}"
        st.download_button(
            "⬇ Descargar Excel", data=detalle_a_excel(df_detalle, periodo),
            file_name=f"{nombre_archivo}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True, type="primary",
        )
    st.dataframe(
        df_detalle, use_container_width=True, hide_index=True,
        column_config={"Fecha": st.column_config.DateColumn("Fecha", format="DD/MM/YYYY")},
    )
