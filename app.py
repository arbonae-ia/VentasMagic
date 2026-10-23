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
   SISTEMA VISUAL MAGIC PRINT (v5 - tema oscuro inspirado en el logo)
   Fondo índigo profundo · tarjetas violeta oscuro · acentos cyan, verde y magenta
   ========================================================================= */
:root {
  --fondo:#110A2B; --fondo2:#170F38; --card:#1C1445; --card2:#241A55; --borde:#33296E;
  --texto:#ECEAF7; --gris:#A8A2CC; --cyan:#00BEEA; --verde:#1DBF8A; --magenta:#E0218A;
  --violeta:#8E7DFF; --alerta:#FF8A5B; --suave:#2A2060;
}
.stApp { font-family:"Source Sans Pro","Source Sans 3",system-ui,sans-serif;
  background:radial-gradient(1200px 600px at 10% -10%, #2A0F4F 0%, rgba(17,10,43,0) 60%), var(--fondo);
  color:var(--texto); }
[data-testid="stHeader"] { background:rgba(17,10,43,.85); }
[data-testid="stSidebar"] { background:var(--fondo2); border-right:1px solid var(--borde); }
.block-container { max-width:1240px; padding-top:2.2rem; padding-bottom:3rem; }
#MainMenu, footer { visibility:hidden; }
.stApp p, .stApp label, .stApp span, .stApp li { color:inherit; }

/* Contenedores con borde de Streamlit = tarjetas oscuras */
[data-testid="stVerticalBlockBorderWrapper"] { background:var(--card); border:1px solid var(--borde) !important; border-radius:14px; padding:10px 14px !important; box-shadow:0 6px 24px rgba(0,0,0,.25); }
[data-testid="stVerticalBlockBorderWrapper"] > div { background:transparent; }
[data-testid="stExpander"] details { background:var(--card); border:1px solid var(--borde); border-radius:12px; }
[data-testid="stExpander"] summary p { color:var(--texto); font-weight:600; }
.stSubheader, [data-testid="stMarkdownContainer"] h3 { font-size:1rem !important; color:var(--texto); }

/* Campos de filtros */
[data-baseweb="select"] > div, [data-baseweb="input"] > div, .stTextInput input, .stDateInput input {
  background:var(--card2) !important; border-color:var(--borde) !important; color:var(--texto) !important; }
[data-baseweb="tag"] { background:var(--cyan) !important; color:#0B0620 !important; }
[data-testid="stWidgetLabel"] p, [data-testid="stVerticalBlockBorderWrapper"] label p { font-size:12px !important; color:var(--gris) !important; font-weight:600; }

/* Encabezado */
.app-header { display:flex; align-items:center; justify-content:space-between; gap:16px;
  background:linear-gradient(100deg, #3B0D5C 0%, #1C1445 55%, #120B33 100%);
  border:1px solid var(--borde); border-radius:14px; padding:14px 20px; margin-bottom:14px; box-shadow:0 6px 24px rgba(0,0,0,.3); }
.app-header .marca { display:flex; align-items:center; gap:14px; }
.app-header img { width:56px; height:56px; object-fit:cover; border-radius:12px; box-shadow:0 0 0 1px rgba(255,255,255,.12); }
.main-title { color:#FFFFFF; font-size:26px; font-weight:700; line-height:1.1; margin:0; }
.main-subtitle { color:var(--gris); font-size:13px; margin-top:3px; }
.app-header .estado { color:var(--gris); font-size:11.5px; text-align:right; line-height:1.4; max-width:340px; }

/* Filtros */
.filtros-titulo { color:var(--cyan); font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:.08em; margin:0 0 2px; }
.campo-fechas { background:var(--card2); border:1px solid var(--borde); border-radius:8px; color:var(--texto); font-size:14px; padding:8px 12px; min-height:40px; display:flex; align-items:center; gap:8px; white-space:nowrap; overflow:hidden; }
.campo-fechas small { color:var(--gris); }
.etiqueta-campo { font-size:12px; color:var(--gris); font-weight:600; margin:0 0 6px; }
.filter-summary { background:var(--card); border:1px solid var(--borde); border-left:4px solid var(--cyan); border-radius:8px; color:var(--gris); font-size:12px; line-height:1.5; margin:10px 0 4px; padding:7px 12px; }
.filter-summary strong { color:var(--texto); }
.data-status { color:var(--gris); font-size:11px; font-style:italic; line-height:1.3; margin:2px 0 6px; }

/* Títulos de sección */
.section-title { display:flex; align-items:baseline; gap:10px; color:#FFFFFF; font-size:18px; font-weight:700; margin:26px 0 10px; padding-left:12px; border-left:4px solid var(--magenta); }
.section-title small { color:var(--gris); font-size:12px; font-weight:400; }

/* Tarjetas KPI: rejilla automática, todas con la misma altura */
.kpi-grid { display:grid; grid-template-columns:repeat(auto-fit, minmax(180px, 1fr)); gap:12px; align-items:stretch; margin-bottom:12px; }
.kpi-grid.cinco { grid-template-columns:repeat(auto-fit, minmax(200px, 1fr)); }
.kpi-grid.una { grid-template-columns:1fr; gap:10px; margin-bottom:10px; }
.kpi-card { background:linear-gradient(180deg, var(--card2) 0%, var(--card) 100%); border:1px solid var(--borde); border-top:3px solid var(--violeta); border-radius:12px; padding:12px 14px; display:flex; flex-direction:column; gap:4px; min-width:0; box-shadow:0 4px 16px rgba(0,0,0,.22); }
.kpi-card.navy { border-top-color:var(--magenta); } .kpi-card.verde { border-top-color:var(--verde); } .kpi-card.cyan { border-top-color:var(--cyan); }
.kpi-card.alerta { border-top-color:var(--alerta); }
.kpi-title { color:var(--gris); font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:.06em; line-height:1.25; }
.kpi-value { color:#FFFFFF; font-size:clamp(18px, 1.7vw, 26px); font-weight:700; line-height:1.15; overflow-wrap:anywhere; font-variant-numeric:tabular-nums; }
.kpi-value.texto { font-size:clamp(15px, 1.25vw, 19px); }
.kpi-value.verde { color:var(--verde); } .kpi-value.alerta { color:var(--alerta); }
.small-note { color:var(--gris); font-size:11.5px; line-height:1.35; margin-top:auto; }
.barra { height:8px; background:var(--suave); border-radius:6px; overflow:hidden; margin:4px 0 2px; }
.barra i { display:block; height:100%; border-radius:6px; background:var(--verde); }
.barra.alerta i { background:var(--alerta); }

/* Panel de presupuesto */
.ppto-ayuda { color:var(--gris); font-size:12px; line-height:1.45; }
.ppto-ayuda b { color:var(--texto); }
.aviso { background:var(--suave); border-radius:8px; color:var(--texto); font-size:12.5px; padding:10px 12px; line-height:1.45; }

/* Botones */
.stButton > button { border-radius:8px; border-color:var(--borde); background:var(--card2); color:var(--texto); font-weight:600; }
.stButton > button[kind="primary"] { background:var(--magenta); color:#fff; border-color:var(--magenta); }
.stButton > button[kind="primary"]:hover { background:#B8166F; border-color:#B8166F; }
.stDataFrame { border:1px solid var(--borde); border-radius:8px; }

/* Tarjetas de gráficos: fondo blanco y textos oscuros para leer bien los datos */
[class*="st-key-graf_"] { background:#FFFFFF; border:1px solid #E2E7EE; border-radius:14px; padding:14px 16px 10px; box-shadow:0 6px 24px rgba(0,0,0,.28); }
[class*="st-key-graf_"] .hd h2 { color:#1C2363 !important; }
[class*="st-key-graf_"] .sub { color:#5B6478 !important; }
[class*="st-key-graf_"] .tag { background:#EEF1F8; color:#1C2363; }
[class*="st-key-graf_"] .sr { color:#2D2D2D; }
[class*="st-key-graf_"] .sr .v { color:#1C2363; }
[class*="st-key-graf_"] .sr .t { background:#EEF1F5; }
[class*="st-key-graf_"] p, [class*="st-key-graf_"] span { color:#2D2D2D; }

/* Encabezados de tarjetas de gráficos y listas */
.hd { display:flex; justify-content:space-between; align-items:center; gap:8px; margin:2px 0 2px; }
.hd h2 { margin:0; padding:0; font-size:1.02rem; font-weight:700; color:#FFFFFF; }
.tag { background:var(--suave); color:var(--texto); font-size:11px; font-weight:600; border-radius:6px; padding:2px 8px; white-space:nowrap; }
.sub { margin:0 0 10px; color:var(--gris); font-size:12px; }
.seg { display:grid; gap:9px; }
.sr { display:grid; grid-template-columns:minmax(100px,170px) 1fr auto; gap:12px; align-items:center; font-size:13px; color:var(--texto); }
.sr .n { overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.sr .t { height:10px; background:var(--suave); border-radius:6px; overflow:hidden; }
.sr .t i { display:block; height:100%; border-radius:6px; }
.sr .v { font-weight:700; color:#FFFFFF; white-space:nowrap; text-align:right; font-variant-numeric:tabular-nums; }
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
    datos = mover_encabezado_al_inicio(hoja.get_all_values())
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

with st.container(border=True):
    st.markdown('<div class="filtros-titulo">Filtros de análisis</div>', unsafe_allow_html=True)
    ciudades_opc = sorted(df_full["Ciudad"].dropna().astype(str).unique()) if "Ciudad" in df_full.columns else []
    vendedores_opc = sorted(df_full["Vendedor"].dropna().astype(str).unique()) if "Vendedor" in df_full.columns else []
    clientes_opc = sorted(df_full["Cliente"].dropna().astype(str).unique()) if "Cliente" in df_full.columns else []
    tipos_venta_opc = sorted(df_full["Tipo de Venta"].dropna().astype(str).unique()) if "Tipo de Venta" in df_full.columns else []
    sel_ciudades, sel_vendedores, sel_clientes, sel_tipo_venta = [], [], [], []

    opciones_filtro = [("Ciudad", ciudades_opc), ("Vendedor", vendedores_opc), ("Cliente", clientes_opc), ("Tipo de venta", tipos_venta_opc)]
    filtros_visibles = [(nombre, opciones) for nombre, opciones in opciones_filtro if opciones]
    # Todos los filtros en una sola línea: periodo, fechas, ciudad, vendedor, cliente y tipo de venta.
    fila_1 = st.columns([1.05, 1.25, 1, 1, 1.3, 1], gap="small")
    destinos = {"Ciudad": fila_1[2], "Vendedor": fila_1[3], "Cliente": fila_1[4], "Tipo de venta": fila_1[5]}
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
                            "Año actual", "Elegir un mes", "Rango personalizado"]
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

        with fila_1[1]:
            if periodo_sel == "Elegir un mes":
                meses_disp = sorted({(d.year, d.month) for d in df_full["Fecha"].dropna().dt.date}, reverse=True)
                etiquetas_mes = [f"{nombres_mes[m]} {a}" for a, m in meses_disp]
                mes_sel = st.selectbox("Mes", etiquetas_mes, index=0, key="mes_sel")
                a, m = meses_disp[etiquetas_mes.index(mes_sel)]
                inicio_p = date(a, m, 1)
                fin_p = min(fin_de_mes(inicio_p), ultimo) if (a, m) == (ultimo.year, ultimo.month) else fin_de_mes(inicio_p)
            elif periodo_sel == "Rango personalizado":
                rango_manual = st.date_input("Desde – hasta", (ultimo.replace(day=1), ultimo),
                                             min_value=f_min, max_value=f_max, format="DD/MM/YYYY", key="rango_manual")
                if isinstance(rango_manual, (tuple, list)) and len(rango_manual) == 2:
                    inicio_p, fin_p = rango_manual
                elif isinstance(rango_manual, (tuple, list)) and len(rango_manual) == 1:
                    inicio_p = fin_p = rango_manual[0]
            # Ajustar al rango de datos disponible
            inicio_p, fin_p = max(inicio_p, f_min), min(fin_p, f_max)
            if inicio_p > fin_p:
                # Sin datos en el periodo elegido: mostrar el último mes con datos.
                inicio_p, fin_p = max(f_min, f_max.replace(day=1)), f_max
            if periodo_sel not in ("Elegir un mes", "Rango personalizado"):
                st.markdown(
                    f'<div class="etiqueta-campo">Fechas</div><div class="campo-fechas">📅 {inicio_p:%d/%m/%Y} '
                    f'<small>→</small> {fin_p:%d/%m/%Y}</div>', unsafe_allow_html=True)
        rango_fechas = (inicio_p, fin_p)
    else:
        rango_fechas = None

    for nombre, opciones in filtros_visibles:
        with destinos[nombre]:
            seleccion = st.multiselect(nombre, opciones, placeholder="Todos")
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

    del_mes = df_full[(df_full["Fecha"].dt.date >= inicio_mes) & (df_full["Fecha"].dt.date <= corte)]
    traslado_mes = es_traslado_serie(del_mes)
    ventas_mes = float(del_mes.loc[~traslado_mes, "Valor Total"].sum())
    traslados_mes = float(del_mes.loc[traslado_mes, "Valor Total"].sum())
    documentos_traslado = del_mes.loc[traslado_mes, "Factura #"].nunique() if "Factura #" in del_mes.columns else 0

    presupuestos = cargar_presupuestos(hoja)
    presupuesto = float(presupuestos.get(clave_mes, 0) or 0)
    habiles_mes = dias_habiles(inicio_mes, fin_mes)
    habiles_transcurridos = dias_habiles(inicio_mes, corte)
    habiles_restantes = max(habiles_mes - habiles_transcurridos, 0)
    ritmo_actual = ventas_mes / habiles_transcurridos if habiles_transcurridos else 0

    st.markdown(
        f'<div class="section-title">Resumen ejecutivo <small>{nombre_mes} · corte {corte:%d/%m/%Y} · '
        f'{habiles_transcurridos} de {habiles_mes} días hábiles</small></div>',
        unsafe_allow_html=True,
    )

    with st.expander(f"Presupuesto de {nombre_mes}: " + (cop(presupuesto) if presupuesto else "sin registrar"),
                     expanded=not presupuesto):
        c_txt, c_val, c_btn = st.columns([2.2, 1.3, 0.9])
        with c_txt:
            st.markdown(
                '<div class="ppto-ayuda">Escribe el <b>presupuesto de ventas sin IVA</b> asignado al mes. '
                'Se guarda en la pestaña <b>Presupuesto</b> del Google Sheets. El mes es el de la '
                '<b>fecha final</b> del filtro; para registrar otro mes, cambia esa fecha.</div>',
                unsafe_allow_html=True,
            )
        with c_val:
            texto_presupuesto = st.text_input(
                f"Presupuesto {clave_mes}", value=fnum(presupuesto) if presupuesto else "",
                placeholder="Ej: 373.580.000", key=f"ppto_{clave_mes}",
            )
        with c_btn:
            if st.button("Guardar", type="primary", use_container_width=True, key=f"guardar_ppto_{clave_mes}"):
                valor_presupuesto = convertir_numero(texto_presupuesto)
                if valor_presupuesto <= 0:
                    st.error("Escribe un valor mayor que cero.")
                else:
                    try:
                        guardar_presupuesto(hoja, clave_mes, valor_presupuesto)
                        cargar_presupuestos.clear()
                        st.session_state["mensaje_carga"] = f"Presupuesto de {nombre_mes} guardado: {cop(valor_presupuesto)}."
                        st.rerun()
                    except Exception as error:
                        st.error(f"No fue posible guardar el presupuesto: {error}")

    nota_ventas = f"Sin IVA y sin traslados · {inicio_mes:%d/%m} al {corte:%d/%m/%Y}"
    nota_traslados = f"{fnum(documentos_traslado)} documentos TR · no suman al cumplimiento"
    if presupuesto:
        cumplimiento = ventas_mes / presupuesto * 100
        meta_al_dia = presupuesto * habiles_transcurridos / habiles_mes if habiles_mes else 0
        cumplimiento_al_dia = ventas_mes / meta_al_dia * 100 if meta_al_dia else 0
        brecha = presupuesto - ventas_mes
        if brecha > 0:
            ritmo_requerido = brecha / habiles_restantes if habiles_restantes else brecha
            atrasado = ritmo_requerido > ritmo_actual
            tarjetas = [
                kpi_html("Ventas acumuladas", cop(ventas_mes), "navy", nota_ventas),
                kpi_html("Cumplimiento", f"{fnum(cumplimiento, 1)}%", "verde",
                         f"Al día: {fnum(cumplimiento_al_dia, 1)}% (meta al día {cop(meta_al_dia)})",
                         barra=cumplimiento, barra_alerta=cumplimiento_al_dia < 100),
                kpi_html("Brecha presupuestal", cop(brecha), "cyan",
                         f"Presupuesto {cop(presupuesto)} menos ventas"),
                kpi_html("Ritmo requerido", f"{cop(ritmo_requerido)}/día", "alerta" if atrasado else "verde",
                         (f"{habiles_restantes} días hábiles restantes · ritmo actual {cop(ritmo_actual)}/día"
                          if habiles_restantes else "No quedan días hábiles en el mes"),
                         clase_valor="alerta" if atrasado else "verde"),
                kpi_html("Traslados a Bellatela", cop(traslados_mes), "navy", nota_traslados),
            ]
        else:
            tarjetas = [
                kpi_html("Ventas acumuladas", cop(ventas_mes), "navy", nota_ventas),
                kpi_html("Cumplimiento", f"{fnum(cumplimiento, 1)}%", "verde",
                         f"Al día: {fnum(cumplimiento_al_dia, 1)}%", clase_valor="verde", barra=100),
                kpi_html("Brecha presupuestal", "Meta cumplida", "verde",
                         f"Excedente de {cop(-brecha)} sobre {cop(presupuesto)}", clase_valor="verde texto"),
                kpi_html("Ritmo requerido", "$0/día", "verde", f"Ritmo actual {cop(ritmo_actual)}/día"),
                kpi_html("Traslados a Bellatela", cop(traslados_mes), "navy", nota_traslados),
            ]
    else:
        sin_dato = "Registra el presupuesto del mes"
        tarjetas = [
            kpi_html("Ventas acumuladas", cop(ventas_mes), "navy", nota_ventas),
            kpi_html("Cumplimiento", "— %", "verde", sin_dato),
            kpi_html("Brecha presupuestal", "— $", "cyan", sin_dato),
            kpi_html("Ritmo requerido", "— $/día", "verde", sin_dato),
            kpi_html("Traslados a Bellatela", cop(traslados_mes), "navy", nota_traslados),
        ]
    st.markdown(rejilla_kpi(tarjetas, "cinco"), unsafe_allow_html=True)

    # --- Tendencia del mes: acumulado real, ruta del presupuesto y proyección ---
    dias_mes = [inicio_mes + timedelta(days=n) for n in range((fin_mes - inicio_mes).days + 1)]
    diario = (del_mes.loc[~traslado_mes].groupby(del_mes.loc[~traslado_mes, "Fecha"].dt.date)["Valor Total"].sum())
    acumulado_real, total_corrido = [], 0.0
    for dia in dias_mes:
        if dia > corte:
            break
        total_corrido += float(diario.get(dia, 0))
        acumulado_real.append(total_corrido)
    proyeccion_cierre = ventas_mes + ritmo_actual * habiles_restantes

    c_graf, c_ref = st.columns([2.1, 1])
    with c_graf:
        with st.container(key="graf_tendencia"):
            st.markdown('<div class="hd"><h2>Tendencia de ventas y proyección de cierre</h2>'
                        f'<span class="tag">{nombre_mes}</span></div>'
                        '<p class="sub">Ventas acumuladas sin traslados frente a la ruta del presupuesto por día hábil</p>',
                        unsafe_allow_html=True)
            figura = go.Figure()
            if presupuesto and habiles_mes:
                ruta = [presupuesto * dias_habiles(inicio_mes, d) / habiles_mes for d in dias_mes]
                figura.add_scatter(x=dias_mes, y=ruta, name="Ruta del presupuesto", mode="lines",
                                   line=dict(color=CYAN, width=2, dash="dot"),
                                   hovertemplate="%{x|%d/%m}<br>Meta acumulada $%{y:,.0f}<extra></extra>")
            figura.add_scatter(x=dias_mes[:len(acumulado_real)], y=acumulado_real, name="Ventas acumuladas",
                               mode="lines+markers", line=dict(color=NAVY, width=3), marker=dict(size=5),
                               hovertemplate="%{x|%d/%m}<br>Vendido $%{y:,.0f}<extra></extra>")
            if habiles_transcurridos and corte < fin_mes:
                dias_futuros = [d for d in dias_mes if d >= corte]
                valores_proyeccion = [ventas_mes + ritmo_actual * dias_habiles(corte + timedelta(days=1), d)
                                      for d in dias_futuros]
                figura.add_scatter(x=dias_futuros, y=valores_proyeccion, name="Proyección al ritmo actual",
                                   mode="lines", line=dict(color=VERDE, width=2, dash="dash"),
                                   hovertemplate="%{x|%d/%m}<br>Proyección $%{y:,.0f}<extra></extra>")
            if presupuesto:
                figura.add_hline(y=presupuesto, line=dict(color=ALERTA, width=1), opacity=0.6,
                                 annotation_text=f"Presupuesto {cop(presupuesto)}", annotation_position="top left",
                                 annotation_font=dict(size=11, color=ALERTA))
            figura.update_layout(
                height=340, margin=dict(l=8, r=8, t=10, b=8), separators=",.",
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(size=12, color=TXT), hoverlabel=dict(bgcolor=NAVY, font_color="#fff"),
                legend=dict(orientation="h", y=-0.15, x=0.5, xanchor="center"),
                xaxis=dict(showgrid=False, tickformat="%d/%m"),
                yaxis=dict(gridcolor=GRID, tickprefix="$", tickformat="~s", rangemode="tozero"),
            )
            st.plotly_chart(figura, use_container_width=True, config={"displayModeBar": False})
    with c_ref:
        with st.container(border=True):
            st.markdown('<div class="hd"><h2>Referencias para la meta</h2></div>'
                        '<p class="sub">Tres puntos de comparación para leer el resultado</p>',
                        unsafe_allow_html=True)
            referencias = [
                kpi_html("Presupuesto asignado", cop(presupuesto) if presupuesto else "Sin registrar", "navy",
                         "Qué resultado exige la dirección", clase_valor="" if presupuesto else "texto"),
                kpi_html("Ventas históricas comparables", "Pendiente", "cyan",
                         "Se agregará al conectar la base histórica 2025-2026", clase_valor="texto"),
                kpi_html("Proyección de cierre", cop(proyeccion_cierre) if habiles_transcurridos else "Sin datos", "verde",
                         (f"{fnum(proyeccion_cierre / presupuesto * 100, 1)}% del presupuesto · " if presupuesto and habiles_transcurridos else "")
                         + "ritmo actual por día hábil"),
            ]
            st.markdown(rejilla_kpi(referencias, "una"), unsafe_allow_html=True)
            st.markdown('<div class="aviso">La proyección reparte el ritmo actual en los días hábiles que faltan '
                        '(lunes a viernes sin festivos). Es una referencia: todavía no considera la estacionalidad '
                        'ni la forma habitual en que se distribuyen las ventas dentro del mes.</div>',
                        unsafe_allow_html=True)

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
PALETA = [NAVY, CYAN, MAGENTA, VERDE, "#FFC145", "#66D8F2", "#F06BB4", "#7FE0BE", "#B9AEFF", "#FFD98A"]
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
        font=dict(size=12, color=TXT), hoverlabel=dict(bgcolor=NAVY, font_color="#fff"),
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
        textfont=dict(size=11, color=TXT),
        hovertemplate="%{y}<br>$%{x:,.0f}<extra></extra>",
    ))
    # Reserva espacio para que el valor del primer lugar no quede cortado.
    figura.update_xaxes(
        showgrid=True, gridcolor=GRID, zeroline=False,
        tickprefix="$", tickformat="~s", range=[0, maximo * 1.25],
    )
    figura.update_yaxes(showgrid=False)
    figura.update_layout(margin=dict(l=8, r=155, t=4, b=8), uniformtext_minsize=9)
    mostrar(figura)


def anillo(items, colores, alto=215):
    total = sum(v for _, v in items)
    figura = go.Figure(go.Pie(
        labels=[str(n) for n, _ in items], values=[v for _, v in items], hole=0.62, sort=False,
        marker=dict(colors=colores, line=dict(color="#FFFFFF", width=2)), textinfo="percent",
        textfont=dict(color="#FFFFFF", size=12),
        hovertemplate="%{label}<br>$%{value:,.0f} (%{percent})<extra></extra>",
    ))
    figura.add_annotation(text=f"<b>{corto(total)}</b>", x=0.5, y=0.5, showarrow=False, font=dict(size=15, color=TXT))
    mostrar(figura, alto=alto, leyenda=True)


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
st.markdown(f'<div class="section-title">Indicadores comerciales <small>{periodo} · según los filtros</small></div>',
            unsafe_allow_html=True)
indicadores = [
    kpi_html("Ventas a clientes", cop(ventas_clientes), "navy", "Sin IVA y sin traslados"),
    kpi_html("Traslados a Bellatela", cop(ventas_traslados), "cyan", f"Total con traslados: {cop(ventas)}"),
    kpi_html("Facturas realizadas", fnum(facturas), "verde", "Documentos en el periodo"),
    kpi_html("Clientes atendidos", fnum(clientes), "navy", f"En {fnum(df['Ciudad'].nunique())} ciudades"),
    kpi_html("Ticket promedio", cop(ticket), "verde", "Valor promedio por factura"),
    kpi_html("Metros de sublimación", f"{fnum(cantidad_metros_sublimacion, 2)} m", "cyan", "Según actividad facturada"),
    kpi_html("Metros de base textil", f"{fnum(cantidad_metros_base, 2)} m", "navy", "Según actividad facturada"),
    kpi_html("Kilos vendidos", f"{fnum(cantidad_kilos, 2)} kg", "verde", "Según unidad facturada"),
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
                       line=dict(color=MAGENTA, width=3), marker=dict(size=7),
                       hovertemplate="%{x}<br>$%{y:,.0f}<extra></extra>")
    figura.update_layout(
        xaxis=dict(type="category", showgrid=False),
        yaxis=dict(rangemode="tozero", gridcolor=GRID, tickformat="d"),
        yaxis2=dict(overlaying="y", side="right", rangemode="tozero",
                    showgrid=False, tickprefix="$", tickformat="~s"),
    )
    mostrar(figura, alto=430, leyenda=True)
c1, c2 = st.columns(2)
with c1:
    with st.container(key="graf_tipo"):
        items_tipo = serie("Tipo de Venta")
        tarjeta("Ventas por tipo de venta", "Participación sobre el valor vendido", f"{len(items_tipo)} tipos")
        if items_tipo:
            anillo(items_tipo, [CYAN, MAGENTA, VERDE, NAVY, "#FFC145", "#66D8F2", "#F06BB4"], alto=360)
with c2:
    with st.container(key="graf_pago"):
        items_pago = serie("Forma de Pago")
        tarjeta("Ventas por forma de pago", "Participación sobre el valor vendido", f"{len(items_pago)} formas")
        if items_pago:
            anillo(items_pago, [VERDE, CYAN, MAGENTA, NAVY, "#FFC145", "#66D8F2", "#F06BB4"], alto=360)

c1, c2 = st.columns(2)
with c1:
    with st.container(key="graf_ciudades"):
        tarjeta("Top 10 ciudades por ventas", "Valor vendido y participación sobre el total")
        barras_h(df.groupby("Ciudad", as_index=False)["Valor Total"].sum(), "Valor Total", "Ciudad", VERDE)
with c2:
    with st.container(key="graf_articulos"):
        tarjeta("Top 10 artículos más vendidos", "Valor vendido y participación sobre el total")
        barras_h(df.groupby("Descripcion", as_index=False)["Valor Total"].sum(), "Valor Total", "Descripcion", MAGENTA)

c1, c2 = st.columns(2)
with c1:
    with st.container(key="graf_clientes"):
        top_clientes = serie("Cliente")[:10]
        tarjeta("Ranking de facturación por cliente", "Top 10 clientes por valor vendido", f"{fnum(clientes)} clientes · {corto(ventas)}")
        st.markdown(filas(top_clientes), unsafe_allow_html=True)
with c2:
    with st.container(key="graf_vendedores"):
        vendedores = serie("Vendedor")[:10]
        tarjeta("Desempeño por vendedor", "Valor vendido y participación", f"{len(vendedores)} vendedores")
        st.markdown(filas(vendedores), unsafe_allow_html=True)

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


with st.container(border=True):
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
