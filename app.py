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


st.set_page_config(page_title="Magic Print Analytics", page_icon="📊", layout="wide")

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

st.markdown("""
<style>
.main-title{font-size:42px;font-weight:700;color:#19324d;margin-bottom:25px}
.section-title{color:#19324d;font-size:25px;font-weight:700;margin:25px 0 15px}
.kpi-card{background:#eef4fb;border:1px solid #c8d8e8;border-radius:14px;padding:18px 12px;min-height:115px;box-shadow:0 2px 6px rgba(30,60,90,.10)}
.kpi-card.green{background:#edf8f2;border-color:#b9dfc9}
.kpi-card.orange{background:#fff7e8;border-color:#f0d59a}
.kpi-card.purple{background:#f3effb;border-color:#d8c9ef}
.kpi-card.blue{background:#edf5ff;border-color:#c3d8f5}
.kpi-title{color:#637384;font-size:14px;margin-bottom:8px}
.kpi-value{color:#19324d;font-size:25px;font-weight:700}
.small-note{color:#667685;font-size:13px}
</style>
""", unsafe_allow_html=True)


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
                     if len(partes[-1]) == 2 else texto.replace(",", ""))
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


if "registros_pdf" not in st.session_state:
    st.session_state["registros_pdf"] = None
if "mensaje_carga" not in st.session_state:
    st.session_state["mensaje_carga"] = ""
if "uploader_version" not in st.session_state:
    st.session_state["uploader_version"] = 0

st.markdown('<div class="main-title">Magic Print Analytics</div>', unsafe_allow_html=True)
if st.session_state["mensaje_carga"]:
    st.success(st.session_state.pop("mensaje_carga"))

hoja = conectar_hoja()
if hoja is None:
    st.stop()

with st.sidebar:
    st.header("Cargar facturas PDF")
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
                st.error(
                    "El PDF no corresponde a una factura válida: "
                    "no se encontraron productos o servicios. "
                    "Revisa el archivo e intenta nuevamente."
                )

registros_pdf = st.session_state["registros_pdf"]
if registros_pdf:
    st.markdown('<div class="section-title">Vista previa del PDF</div>', unsafe_allow_html=True)
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

df = cargar_datos()
if df.empty:
    st.info("Google Sheets está conectado, pero todavía no contiene registros.")
    st.stop()

st.sidebar.markdown("---")
st.sidebar.header("Filtros de análisis")
st.sidebar.caption("Puedes seleccionar uno o varios valores en cada lista.")

if "Fecha" in df.columns and not df["Fecha"].dropna().empty:
    fecha_min = df["Fecha"].min().date()
    fecha_max = df["Fecha"].max().date()
    rango = st.sidebar.date_input("Rango de fechas", (fecha_min, fecha_max), min_value=fecha_min, max_value=fecha_max)
    if isinstance(rango, tuple) and len(rango) == 2:
        df = df[(df["Fecha"].dt.date >= rango[0]) & (df["Fecha"].dt.date <= rango[1])]

for columna, titulo in [("Ciudad", "Ciudad"), ("Vendedor", "Vendedor"), ("Cliente", "Cliente"), ("Unidad", "Unidad"), ("Tipo de Venta", "Tipo de venta")]:
    df = aplicar_filtro_lista(df, columna, titulo)

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

st.markdown('<div class="section-title">Indicadores comerciales</div>', unsafe_allow_html=True)
kpis = [
    ("Ventas sin IVA", f"${ventas:,.0f}", "blue"),
    ("Facturas realizadas", f"{facturas:,.0f}", "green"),
    ("Clientes atendidos", f"{clientes:,.0f}", "purple"),
    ("Cantidad vendida", f"{cantidad:,.0f}", "orange"),
    ("Ticket promedio", f"${ticket:,.0f}", "blue"),
]
cols = st.columns(5)
for col, (titulo, valor, color) in zip(cols, kpis):
    with col:
        st.markdown(f'<div class="kpi-card {color}"><div class="kpi-title">{titulo}</div><div class="kpi-value">{valor}</div></div>', unsafe_allow_html=True)

st.markdown('<div class="section-title">Días destacados</div>', unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1:
    st.markdown(f'<div class="kpi-card green"><div class="kpi-title">Día de mayor venta</div><div class="kpi-value">{dia_mayor}</div><div class="small-note">${valor_mayor:,.0f} vendidos</div></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="kpi-card orange"><div class="kpi-title">Día de menor venta</div><div class="kpi-value">{dia_menor}</div><div class="small-note">${valor_menor:,.0f} vendidos</div></div>', unsafe_allow_html=True)


def mostrar_grafico(figura):
    figura.update_layout(height=390, margin=dict(l=20, r=20, t=60, b=20))
    st.plotly_chart(figura, use_container_width=True)


st.markdown('<div class="section-title">Análisis comercial</div>', unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1:
    with st.container(border=True):
        datos = df.groupby("Fecha", as_index=False)["Valor Total"].sum().sort_values("Fecha")
        mostrar_grafico(px.line(datos, x="Fecha", y="Valor Total", markers=True, title="Evolución de ventas"))
with c2:
    with st.container(border=True):
        datos = df.groupby("Ciudad", as_index=False)["Valor Total"].sum().sort_values("Valor Total", ascending=False)
        mostrar_grafico(px.bar(datos, x="Ciudad", y="Valor Total", color="Ciudad", title="Ventas por ciudad"))

c1, c2 = st.columns(2)
with c1:
    with st.container(border=True):
        datos = df.groupby("Vendedor", as_index=False)["Valor Total"].sum().sort_values("Valor Total", ascending=False)
        mostrar_grafico(px.bar(datos, x="Valor Total", y="Vendedor", orientation="h", color="Vendedor", title="Ventas por vendedor"))
with c2:
    with st.container(border=True):
        datos = df.groupby("Descripcion", as_index=False)["Valor Total"].sum().sort_values("Valor Total", ascending=False).head(15)
        mostrar_grafico(px.bar(datos, x="Valor Total", y="Descripcion", orientation="h", color="Valor Total", title="Productos y servicios más vendidos"))

st.markdown('<div class="section-title">Detalle de facturación</div>', unsafe_allow_html=True)
with st.container(border=True):
    st.dataframe(df, use_container_width=True, hide_index=True)
