import io
import re
from datetime import datetime
from pathlib import Path

import gspread
import pandas as pd
import pdfplumber
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from google.oauth2.service_account import Credentials
from PIL import Image

# -----------------------------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA Y BRANDING
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Magic Print Analytics", page_icon="📊", layout="wide")

LOGO_PATH = Path(__file__).resolve().parent / "assets" / "magic_print_logo.jpg"
LOGO_FALLBACK = "https://images.unsplash.com/photo-1524758631624-e2822e304c36?auto=format&fit=crop&w=400&q=80"

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

    :root {
        --bg: #f3f7fb;
        --panel: rgba(255,255,255,0.9);
        --card: #ffffff;
        --line: #dfeaf5;
        --text: #0f172a;
        --muted: #64748b;
        --blue: #2563eb;
        --blue-soft: #dfeeff;
        --green: #10b981;
        --green-soft: #dffcf3;
        --purple: #8b5cf6;
        --purple-soft: #f1e9ff;
        --orange: #f59e0b;
        --orange-soft: #fff0d8;
        --pink: #ff4fd8;
        --cyan: #2dd4bf;
        --shadow: 0 16px 35px rgba(15, 23, 42, 0.08);
        --radius: 18px;
    }

    html, body, [data-testid="stAppViewContainer"], .main {
        background: linear-gradient(180deg, #eef5ff 0%, #f8fafd 20%, #f5f7fb 100%);
        color: var(--text);
        font-family: 'Inter', sans-serif;
    }

    .app-shell {
        padding-top: 0.5rem;
    }

    .topbar {
        background: linear-gradient(135deg, rgba(15,23,42,0.96) 0%, rgba(37,99,235,0.92) 48%, rgba(139,92,246,0.94) 100%);
        border-radius: 22px;
        padding: 18px 22px;
        box-shadow: var(--shadow);
        border: 1px solid rgba(255,255,255,0.18);
        margin-bottom: 1.3rem;
    }

    .brand-title {
        font-size: clamp(1.6rem, 2vw, 2.4rem);
        font-weight: 800;
        color: #ffffff;
        letter-spacing: -0.04em;
        line-height: 1.1;
        margin: 0;
    }

    .brand-subtitle {
        color: rgba(255,255,255,0.75);
        font-size: 0.9rem;
        font-weight: 500;
        margin-top: 0.3rem;
    }

    .page-tag {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 0.45rem 0.75rem;
        border-radius: 999px;
        background: rgba(255,255,255,0.12);
        border: 1px solid rgba(255,255,255,0.18);
        color: #ffffff;
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }

    .section-title {
        margin: 0.9rem 0 0.9rem 0;
        font-size: 1.15rem;
        font-weight: 800;
        color: var(--text);
        letter-spacing: -0.02em;
    }

    .kpi-card {
        background: rgba(255,255,255,0.9);
        border: 1px solid var(--line);
        border-radius: var(--radius);
        padding: 1rem 1rem 0.8rem 1rem;
        min-height: 132px;
        box-shadow: 0 8px 18px rgba(15,23,42,0.04);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }

    .kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 26px rgba(37, 99, 235, 0.08);
    }

    .kpi-label {
        display: flex;
        align-items: center;
        justify-content: space-between;
        font-size: 0.72rem;
        font-weight: 700;
        color: var(--muted);
        letter-spacing: 0.07em;
        text-transform: uppercase;
        margin-bottom: 0.5rem;
    }

    .kpi-icon {
        width: 28px;
        height: 28px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.9rem;
        font-weight: 700;
        background: var(--blue-soft);
        color: var(--blue);
    }

    .kpi-icon.green { background: var(--green-soft); color: var(--green); }
    .kpi-icon.purple { background: var(--purple-soft); color: var(--purple); }
    .kpi-icon.orange { background: var(--orange-soft); color: var(--orange); }
    .kpi-icon.pink { background: rgba(255, 79, 216, 0.12); color: var(--pink); }

    .kpi-value {
        font-size: clamp(1.5rem, 2vw, 2.1rem);
        line-height: 1.1;
        font-weight: 800;
        color: var(--text);
        letter-spacing: -0.04em;
        margin-bottom: 0.55rem;
    }

    .kpi-trend {
        font-size: 0.75rem;
        color: var(--muted);
        font-weight: 600;
        margin-top: 0.25rem;
    }

    .panel {
        background: rgba(255,255,255,0.82);
        border: 1px solid var(--line);
        border-radius: var(--radius);
        box-shadow: 0 8px 18px rgba(15,23,42,0.04);
        padding: 1rem;
    }

    div[data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(11,18,32,0.98) 0%, rgba(15,23,42,0.98) 100%);
        border-right: 1px solid rgba(255,255,255,0.06);
    }

    div[data-testid="stSidebar"] > div {
        padding: 1rem 0.9rem 1rem 0.9rem;
    }

    [data-testid="stSidebarUserContent"], [data-testid="stSidebarNav"] {
        background: transparent;
    }

    .sidebar-title {
        color: #ffffff;
        font-size: 1rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        margin: 0.5rem 0 0.8rem 0;
    }

    .sidebar-sub {
        color: rgba(255,255,255,0.7);
        font-size: 0.78rem;
        margin-bottom: 0.7rem;
    }

    .stFileUploader label, .stMultiSelect label, .stDateInput label {
        color: rgba(255,255,255,0.9) !important;
        font-weight: 600;
    }

    .stButton > button {
        background: linear-gradient(135deg, #2563eb, #8b5cf6);
        border: none;
        border-radius: 12px;
        color: white;
        font-weight: 700;
        padding: 0.6rem 1rem;
    }

    .stSuccess, .stWarning, .stInfo {
        border-radius: 12px;
        border: none;
    }

    [data-testid="stDataFrame"] {
        border-radius: 16px;
        overflow: hidden;
        border: 1px solid rgba(148,163,184,0.22);
    }

    .metric-box {
        background: rgba(255,255,255,0.8);
        border: 1px solid #e2e8f0;
        border-radius: 14px;
        padding: 0.8rem 0.9rem;
    }

    .metric-box .title {
        font-size: 0.7rem;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: var(--muted);
        font-weight: 700;
    }

    .metric-box .value {
        font-size: 1.4rem;
        font-weight: 800;
        color: var(--text);
        letter-spacing: -0.03em;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)

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


def cargar_logo():
    if LOGO_PATH.exists():
        return Image.open(LOGO_PATH)
    return None


def sparkline(values, color="#2563eb"):
    y = list(values)
    if not y:
        y = [0]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(range(len(y))),
        y=y,
        mode="lines",
        line=dict(color=color, width=2),
        hoverinfo="skip",
        showlegend=False,
    ))
    fig.update_layout(
        width=160,
        height=50,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(visible=False, showgrid=False, zeroline=False),
        yaxis=dict(visible=False, showgrid=False, zeroline=False),
    )
    return fig


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
            texto = (
                texto.replace(".", "").replace(",", ".")
                if texto.rfind(",") > texto.rfind(".")
                else texto.replace(",", "")
            )
        elif "," in texto:
            partes = texto.split(",")
            texto = (
                texto.replace(".", "").replace(",", ".")
                if len(partes[-1]) == 2
                else texto.replace(",", "")
            )
        elif "." in texto and len(texto.split(".")[-1]) != 2:
            texto = texto.replace(".", "")
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
    if hoja is None:
        return pd.DataFrame(columns=COLUMNAS)
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


def aplicar_filtro_lista(dataframe, columna, titulo):
    if columna not in dataframe.columns:
        return dataframe
    valores = sorted(dataframe[columna].dropna().astype(str).unique())
    seleccionados = st.sidebar.multiselect(
        titulo, valores, default=[], placeholder=f"Seleccione {titulo.lower()}"
    )
    if seleccionados:
        dataframe = dataframe[dataframe[columna].astype(str).isin(seleccionados)]
    return dataframe


# -----------------------------------------------------------------------------
# ESTADOS DE SESIÓN
# -----------------------------------------------------------------------------
if "registros_pdf" not in st.session_state:
    st.session_state["registros_pdf"] = None
if "mensaje_carga" not in st.session_state:
    st.session_state["mensaje_carga"] = ""
if "uploader_version" not in st.session_state:
    st.session_state["uploader_version"] = 0

# -----------------------------------------------------------------------------
# HEADER / BRANDING
# -----------------------------------------------------------------------------
logo = cargar_logo()

with st.container():
    cols = st.columns([1.1, 2.9, 0.8])
    with cols[0]:
        if logo is not None:
            st.image(logo, width=180)
        else:
            st.markdown(
                """
                <div style="
                    width: 180px; height: 70px; border-radius: 16px;
                    background: linear-gradient(135deg, #1e293b, #7c3aed 55%, #f472b6);
                    display:flex; align-items:center; justify-content:center;
                    color: white; font-size: 1.3rem; font-weight: 900; letter-spacing: 0.1em;
                    box-shadow: 0 18px 30px rgba(15,23,42,0.18);
                ">MP</div>
                """,
                unsafe_allow_html=True,
            )
    with cols[1]:
        st.markdown('<div class="brand-title">Magic Print Analytics</div>', unsafe_allow_html=True)
        st.markdown('<div class="brand-subtitle">Seguimiento inteligente de ventas, facturación y análisis comercial</div>', unsafe_allow_html=True)
    with cols[2]:
        st.markdown('<div class="page-tag">LIVE</div>', unsafe_allow_html=True)

st.markdown('<div class="topbar" style="margin-top: 1rem;"></div>', unsafe_allow_html=True)

if st.session_state["mensaje_carga"]:
    st.success(st.session_state.pop("mensaje_carga"))

hoja = conectar_hoja()
if hoja is None:
    st.stop()

# -----------------------------------------------------------------------------
# SIDEBAR / PANEL DE CARGA Y FILTROS
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown('<div class="sidebar-title">Cargar facturas</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-sub">Sube un PDF para agregar registros y actualizar la base.</div>', unsafe_allow_html=True)
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
            except Exception:
                st.error(
                    "El PDF no corresponde a una factura válida. Revisa el archivo e intenta nuevamente."
                )

    st.markdown("---")
    st.markdown('<div class="sidebar-title">Filtros</div>', unsafe_allow_html=True)
    st.caption("Aplica segmentación de análisis por ciudad, vendedor, cliente y tipo de venta.")

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

        if st.button(
            "No cargar este archivo",
            key="cancelar_archivo_repetido",
            use_container_width=True,
            help="Limpia la vista previa y permite seleccionar otro PDF."
        ):
            st.session_state["registros_pdf"] = None
            st.session_state["uploader_version"] += 1
            st.rerun()

        st.info("Las nuevas se pueden cargar sin modificar las repetidas. Para actualizar las repetidas, confirma el reemplazo.")
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
                    st.error(f"No fue posible cargar las facturas: {error}")
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
                    st.error(f"No fue posible reemplazar las facturas: {error}")
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
                st.error(f"No fue posible cargar las facturas: {error}")

# -----------------------------------------------------------------------------
# CARGA DE DATOS Y FILTROS
# -----------------------------------------------------------------------------
df = cargar_datos()
if df.empty:
    st.info("Google Sheets está conectado, pero todavía no contiene registros.")
    st.stop()

st.sidebar.markdown("---")
with st.sidebar:
    if "Fecha" in df.columns and not df["Fecha"].dropna().empty:
        fecha_min = df["Fecha"].min().date()
        fecha_max = df["Fecha"].max().date()
        rango = st.date_input("Rango de fechas", (fecha_min, fecha_max), min_value=fecha_min, max_value=fecha_max)
        if isinstance(rango, tuple) and len(rango) == 2:
            df = df[(df["Fecha"].dt.date >= rango[0]) & (df["Fecha"].dt.date <= rango[1])]

    for columna, titulo in [
        ("Ciudad", "Ciudad"),
        ("Vendedor", "Vendedor"),
        ("Cliente", "Cliente"),
        ("Unidad", "Unidad"),
        ("Tipo de Venta", "Tipo de venta")
    ]:
        df = aplicar_filtro_lista(df, columna, titulo)

# -----------------------------------------------------------------------------
# KPI CARDS Y CÁLCULOS
# -----------------------------------------------------------------------------
ventas = df["Valor Total"].sum()
facturas = df["Factura #"].nunique()
clientes = df["Cliente"].nunique()
cantidad = df["Cantidad"].sum()
ticket = ventas / facturas if facturas else 0
ventas_dia = df.groupby("Fecha", as_index=False)["Valor Total"].sum().dropna()

if ventas_dia.empty:
    dia_mayor, valor_mayor, dia_menor, valor_menor = "Sin datos", 0, "Sin datos", 0
else:
    mayor = ventas_dia.loc[ventas_dia["Valor Total"].idxmax()]
    menor = ventas_dia.loc[ventas_dia["Valor Total"].idxmin()]
    dia_mayor, valor_mayor = mayor["Fecha"].strftime("%d/%m/%Y"), mayor["Valor Total"]
    dia_menor, valor_menor = menor["Fecha"].strftime("%d/%m/%Y"), menor["Valor Total"]

forma_pago = df["Forma de Pago"].fillna("No registrado")
tipo_venta = df["Tipo de Venta"].fillna("Sin clasificación")

kpi_data = [
    ("Ventas sin IVA", ventas, "blue", "💰"),
    ("Facturas realizadas", facturas, "green", "🧾"),
    ("Clientes atendidos", clientes, "purple", "👥"),
    ("Cantidad vendida", cantidad, "orange", "📦"),
    ("Ticket promedio", ticket, "pink", "📈"),
]

st.markdown('<div class="section-title">📊 Indicadores comerciales</div>', unsafe_allow_html=True)
cols = st.columns(5)
for idx, (titulo, valor, color, icono) in enumerate(kpi_data):
    with cols[idx]:
        with st.container():
            valores_spark = (
                df.groupby("Fecha", as_index=False)["Valor Total"].sum().sort_values("Fecha")["Valor Total"].tail(12).tolist()
                if "Fecha" in df.columns and not df.empty else [0]
            )
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-label">
                        <span>{titulo}</span>
                        <span class="kpi-icon {color}">{icono}</span>
                    </div>
                    <div class="kpi-value">{f'$ {valor:,.0f}' if 'Ventas' in titulo or 'Ticket' in titulo else f'{valor:,.0f}'}</div>
                    <div class="kpi-trend">{titulo}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.plotly_chart(sparkline(valores_spark, color={"blue": "#2563eb", "green": "#10b981", "purple": "#8b5cf6", "orange": "#f59e0b", "pink": "#ff4fd8"}[color]), use_container_width=True, config={"displayModeBar": False})

# -----------------------------------------------------------------------------
# DESTACADOS
# -----------------------------------------------------------------------------
st.markdown('<div class="section-title">⭐ Días destacados</div>', unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1:
    st.markdown(
        f"""
        <div class="metric-box">
            <div class="title">Día de mayor venta</div>
            <div class="value">{dia_mayor}</div>
            <div class="small-note">${valor_mayor:,.0f} vendidos</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with c2:
    st.markdown(
        f"""
        <div class="metric-box">
            <div class="title">Día de menor venta</div>
            <div class="value">{dia_menor}</div>
            <div class="small-note">${valor_menor:,.0f} vendidos</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def mostrar_grafico(figura):
    figura.update_layout(
        height=360,
        margin=dict(l=20, r=20, t=35, b=15),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", size=11, color="#334155"),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0)
    )
    st.plotly_chart(figura, use_container_width=True, config={"displayModeBar": False})

# -----------------------------------------------------------------------------
# BLOQUE DE GRÁFICOS
# -----------------------------------------------------------------------------
st.markdown('<div class="section-title">📈 Análisis comercial</div>', unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1:
    with st.container():
        datos = df.groupby("Fecha", as_index=False)["Valor Total"].sum().sort_values("Fecha")
        mostrar_grafico(px.line(datos, x="Fecha", y="Valor Total", markers=True, line_shape="spline", title="Evolución diaria de ventas"))
with c2:
    with st.container():
        datos = df.groupby("Ciudad", as_index=False)["Valor Total"].sum().sort_values("Valor Total", ascending=False)
        mostrar_grafico(px.bar(datos, x="Ciudad", y="Valor Total", color="Ciudad", title="Ventas por ciudad"))

c1, c2 = st.columns(2)
with c1:
    with st.container():
        datos = df.groupby("Vendedor", as_index=False)["Valor Total"].sum().sort_values("Valor Total", ascending=False)
        mostrar_grafico(px.bar(datos, x="Valor Total", y="Vendedor", orientation="h", color="Vendedor", title="Desempeño por vendedor"))
with c2:
    with st.container():
        datos = df.groupby("Tipo de Venta", as_index=False)["Valor Total"].sum().sort_values("Valor Total", ascending=False)
        mostrar_grafico(px.pie(datos, values="Valor Total", names="Tipo de Venta", title="Participación por tipo de venta", hole=0.45))

# -----------------------------------------------------------------------------
# TABLA DETALLADA
# -----------------------------------------------------------------------------
st.markdown('<div class="section-title">📋 Detalle de facturación</div>', unsafe_allow_html=True)
with st.container():
    st.dataframe(df, use_container_width=True, hide_index=True)

# -----------------------------------------------------------------------------
# RESUMEN DE FORMA DE PAGO / TIPO DE VENTA
# -----------------------------------------------------------------------------
forma = df.groupby("Forma de Pago", dropna=False)["Valor Total"].sum().reset_index().sort_values("Valor Total", ascending=False)
tipo = df.groupby("Tipo de Venta", dropna=False)["Valor Total"].sum().reset_index().sort_values("Valor Total", ascending=False)

if not forma.empty or not tipo.empty:
    st.markdown('<div class="section-title">💡 Resumen comercial</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if not forma.empty:
            with st.container():
                st.subheader("Forma de pago")
                mostrar_grafico(px.bar(forma, x="Forma de Pago", y="Valor Total", color="Forma de Pago", title="Ventas por forma de pago"))
    with c2:
        if not tipo.empty:
            with st.container():
                st.subheader("Tipo de venta")
                mostrar_grafico(px.bar(tipo, x="Tipo de Venta", y="Valor Total", color="Tipo de Venta", title="Ventas por tipo de venta"))


# # final newline
