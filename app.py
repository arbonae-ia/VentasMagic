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


# ============================================================
# CONFIGURACIÓN
# ============================================================

st.set_page_config(
    page_title="Magic Print Analytics",
    page_icon="📊",
    layout="wide"
)

NOMBRE_ARCHIVO = "Base_Datos_Ventas"
NOMBRE_PESTANA = "Hoja1"

COLUMNAS = [
    "Factura #",
    "Fecha",
    "Cliente",
    "Nit",
    "Ciudad",
    "Vendedor",
    "Codigo Articulo",
    "Descripcion",
    "Unidad",
    "Cantidad",
    "Precio Unitario",
    "Valor Total",
    "% IVA",
    "Forma de Pago"
]

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]


# ============================================================
# DISEÑO VISUAL
# ============================================================

st.markdown(
    """
    <style>
    .main-title {
        font-size: 42px;
        font-weight: 700;
        color: #19324d;
        margin-bottom: 25px;
    }

    .section-title {
        color: #19324d;
        font-size: 25px;
        font-weight: 700;
        margin-top: 25px;
        margin-bottom: 15px;
    }

    .kpi-card {
        background: #eef4fb;
        border: 1px solid #c8d8e8;
        border-radius: 14px;
        padding: 18px 12px;
        min-height: 115px;
        box-shadow: 0 2px 6px rgba(30, 60, 90, 0.10);
    }

    .kpi-card.green {
        background: #edf8f2;
        border-color: #b9dfc9;
    }

    .kpi-card.orange {
        background: #fff7e8;
        border-color: #f0d59a;
    }

    .kpi-card.purple {
        background: #f3effb;
        border-color: #d8c9ef;
    }

    .kpi-card.blue {
        background: #edf5ff;
        border-color: #c3d8f5;
    }

    .kpi-title {
        color: #637384;
        font-size: 14px;
        margin-bottom: 8px;
    }

    .kpi-value {
        color: #19324d;
        font-size: 25px;
        font-weight: 700;
    }

    .chart-card {
        background: white;
        border: 1px solid #d9e1e8;
        border-radius: 14px;
        padding: 12px 18px 4px 18px;
        margin-bottom: 20px;
        box-shadow: 0 2px 7px rgba(30, 60, 90, 0.08);
    }

    .upload-card {
        background: #f5f8fb;
        border: 1px solid #d9e1e8;
        border-radius: 14px;
        padding: 12px;
    }

    .small-note {
        color: #667685;
        font-size: 13px;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# CONEXIÓN CON GOOGLE SHEETS
# ============================================================

@st.cache_resource
def conectar_hoja():
    try:
        credentials = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=SCOPES
        )

        cliente = gspread.authorize(credentials)
        archivo = cliente.open(NOMBRE_ARCHIVO)
        return archivo.worksheet(NOMBRE_PESTANA)

    except Exception as error:
        st.error(f"No fue posible conectar con Google Sheets: {error}")
        return None


# ============================================================
# FUNCIONES DE LIMPIEZA
# ============================================================

MESES_PDF = {
    "JAN": "01",
    "FEB": "02",
    "MAR": "03",
    "APR": "04",
    "MAY": "05",
    "JUN": "06",
    "JUL": "07",
    "AUG": "08",
    "SEP": "09",
    "OCT": "10",
    "NOV": "11",
    "DEC": "12"
}


def limpiar_texto(valor):
    if valor is None:
        return ""

    valor = str(valor)
    valor = valor.replace("\xa0", " ")
    valor = re.sub(r"\s+", " ", valor)

    return valor.strip()


def limpiar_nit(valor):
    return re.sub(r"[^0-9]", "", limpiar_texto(valor))


def convertir_numero(valor):
    if valor is None:
        return 0.0

    texto = limpiar_texto(valor)
    texto = texto.replace("$", "").replace(" ", "")

    if not texto:
        return 0.0

    try:
        if "," in texto and "." in texto:
            if texto.rfind(",") > texto.rfind("."):
                texto = texto.replace(".", "").replace(",", ".")
            else:
                texto = texto.replace(",", "")

        elif "," in texto:
            partes = texto.split(",")

            if len(partes[-1]) == 2:
                texto = texto.replace(".", "").replace(",", ".")
            else:
                texto = texto.replace(",", "")

        elif "." in texto:
            partes = texto.split(".")

            if len(partes[-1]) != 2:
                texto = texto.replace(".", "")

        return float(texto)

    except Exception:
        return 0.0


def convertir_fecha_pdf(fecha):
    fecha = limpiar_texto(fecha)
    fecha = fecha.replace("−", "-").replace("–", "-")

    partes = fecha.split("-")

    if len(partes) != 3:
        return ""

    anio = partes[0]
    mes = partes[1].upper()
    dia = partes[2].zfill(2)

    mes_numero = MESES_PDF.get(mes, mes)

    try:
        return datetime.strptime(
            f"{anio}-{mes_numero}-{dia}",
            "%Y-%m-%d"
        ).strftime("%Y-%m-%d")

    except Exception:
        return fecha


# ============================================================
# EXTRACCIÓN DEL PDF
# ============================================================

def extraer_datos_pdf(archivo_pdf):
    registros = []
    contenido = archivo_pdf.read()

    if not contenido:
        raise ValueError("El archivo PDF está vacío.")

    with pdfplumber.open(io.BytesIO(contenido)) as pdf:

        for pagina in pdf.pages:
            texto = pagina.extract_text() or ""

            if not texto.strip():
                continue

            texto = (
                texto
                .replace("−", "-")
                .replace("–", "-")
                .replace("—", "-")
            )

            factura_match = re.search(
                r"Numero\s*:\s*([A-Z]+-\d+)",
                texto,
                flags=re.IGNORECASE
            )

            if not factura_match:
                factura_match = re.search(
                    r"\b(FM-\d+)\b",
                    texto,
                    flags=re.IGNORECASE
                )

            if not factura_match:
                continue

            factura = factura_match.group(1).upper()

            fecha_match = re.search(
                r"Fecha\s*:\s*(\d{4}-[A-Z]{3}-\d{2})",
                texto,
                flags=re.IGNORECASE
            )

            fecha = (
                convertir_fecha_pdf(fecha_match.group(1))
                if fecha_match else ""
            )

            cliente_match = re.search(
                r"Cliente\s*:\s*(.*?)\s*\|",
                texto,
                flags=re.IGNORECASE
            )

            cliente = (
                limpiar_texto(cliente_match.group(1))
                if cliente_match else ""
            )

            nit_match = re.search(
                r"Nit\s+o\s+C\.C\.\s*:\s*([0-9.\-]+)",
                texto,
                flags=re.IGNORECASE
            )

            nit = (
                limpiar_nit(nit_match.group(1))
                if nit_match else ""
            )

            ciudad_match = re.search(
                r"Ciudad\s*:\s*([A-ZÁÉÍÓÚÑ ]+)",
                texto,
                flags=re.IGNORECASE
            )

            ciudad = (
                limpiar_texto(ciudad_match.group(1))
                if ciudad_match else ""
            )

            vendedor_match = re.search(
                r"Vendedor\s*:\s*(.*?)\s*\|",
                texto,
                flags=re.IGNORECASE
            )

            vendedor = (
                limpiar_texto(vendedor_match.group(1))
                if vendedor_match else ""
            )

            pago_match = re.search(
                r"\|\s*(CREDITO\s+\d+\s+DIAS?|CONTADO)\s*\|",
                texto,
                flags=re.IGNORECASE
            )

            forma_pago = (
                limpiar_texto(pago_match.group(1))
                if pago_match else ""
            )

            patron_linea = re.compile(
                r"^\s*\|?\s*"
                r"(\d{3,10})\s+"
                r"(.+?)\s+"
                r"(\d+(?:[.,]\d+)?)\s+"
                r"(\d+(?:[.,]\d+)?)\s+"
                r"(MTS|KLS|UND|UN|KG|KGM|SERV|UNIDAD)\s+"
                r"([\d.,]+)\s+"
                r"([\d.,]+)\s+"
                r"([\d.,]+)\s+"
                r"([\d.,]+)"
                r"\s*\*?\|?\s*$",
                flags=re.IGNORECASE | re.MULTILINE
            )

            lineas = patron_linea.findall(texto)

            for linea in lineas:
                (
                    codigo,
                    descripcion,
                    piezas,
                    cantidad,
                    unidad,
                    precio_unitario,
                    descuento,
                    valor_total,
                    iva
                ) = linea

                valor_total = convertir_numero(valor_total)

                if not codigo or valor_total == 0:
                    continue

                registros.append([
                    factura,
                    fecha,
                    cliente,
                    nit,
                    ciudad,
                    vendedor,
                    limpiar_texto(codigo),
                    limpiar_texto(descripcion),
                    limpiar_texto(unidad).upper(),
                    convertir_numero(cantidad),
                    convertir_numero(precio_unitario),
                    valor_total,
                    convertir_numero(iva),
                    forma_pago
                ])

    if not registros:
        raise ValueError(
            "No se encontraron líneas de productos o servicios."
        )

    return registros


# ============================================================
# DUPLICADOS Y CARGA
# ============================================================

def obtener_informacion_duplicados(hoja, registros_pdf):
    datos = hoja.get_all_values()

    if len(datos) < 2:
        return {
            "facturas_existentes": set(),
            "filas_a_borrar": [],
            "facturas_nuevas": {
                limpiar_texto(registro[0])
                for registro in registros_pdf
            }
        }

    encabezados = [
        limpiar_texto(columna)
        for columna in datos[0]
    ]

    posicion_factura = encabezados.index("Factura #")

    facturas_pdf = {
        limpiar_texto(registro[0])
        for registro in registros_pdf
    }

    facturas_existentes = set()
    filas_a_borrar = []

    for numero_fila, fila in enumerate(datos[1:], start=2):
        if len(fila) <= posicion_factura:
            continue

        factura = limpiar_texto(fila[posicion_factura])

        if factura in facturas_pdf:
            facturas_existentes.add(factura)
            filas_a_borrar.append(numero_fila)

    return {
        "facturas_existentes": facturas_existentes,
        "filas_a_borrar": filas_a_borrar,
        "facturas_nuevas": facturas_pdf - facturas_existentes
    }


def agregar_facturas_nuevas(hoja, registros_pdf, facturas_existentes):
    registros_nuevos = [
        registro
        for registro in registros_pdf
        if limpiar_texto(registro[0])
        not in facturas_existentes
    ]

    if registros_nuevos:
        hoja.append_rows(
            registros_nuevos,
            value_input_option="USER_ENTERED"
        )

    return registros_nuevos


def reemplazar_facturas(hoja, registros_pdf, filas_a_borrar):
    for numero_fila in sorted(filas_a_borrar, reverse=True):
        hoja.delete_rows(numero_fila)

    hoja.append_rows(
        registros_pdf,
        value_input_option="USER_ENTERED"
    )


# ============================================================
# CARGA DE DATOS EXISTENTES
# ============================================================

@st.cache_data(ttl=30)
def cargar_datos():
    hoja = conectar_hoja()
    datos = hoja.get_all_values()

    if not datos:
        return pd.DataFrame(columns=COLUMNAS)

    encabezados = [
        limpiar_texto(columna)
        for columna in datos[0]
    ]

    if len(datos) == 1:
        return pd.DataFrame(columns=encabezados)

    filas = []

    for fila in datos[1:]:
        fila = list(fila)

        if len(fila) < len(encabezados):
            fila.extend([""] * (len(encabezados) - len(fila)))

        filas.append(fila[:len(encabezados)])

    df = pd.DataFrame(filas, columns=encabezados)

    for columna in [
        "Cantidad",
        "Precio Unitario",
        "Valor Total",
        "% IVA"
    ]:
        if columna in df.columns:
            df[columna] = df[columna].apply(convertir_numero)

    if "Fecha" in df.columns:
        df["Fecha"] = pd.to_datetime(
            df["Fecha"],
            errors="coerce"
        )

    if "Codigo Articulo" in df.columns:
        df["Codigo Articulo"] = (
            df["Codigo Articulo"]
            .astype(str)
            .str.replace(".0", "", regex=False)
            .str.strip()
        )

    if "Tipo" not in df.columns:
        codigos_servicio = ["888912", "888916", "888923"]

        df["Tipo"] = np.where(
            df["Codigo Articulo"].isin(codigos_servicio),
            "Servicio",
            "Producto"
        )

    return df


# ============================================================
# ESTADO DE LA APLICACIÓN
# ============================================================

if "registros_pdf" not in st.session_state:
    st.session_state["registros_pdf"] = None

if "mensaje_carga" not in st.session_state:
    st.session_state["mensaje_carga"] = ""


# ============================================================
# ENCABEZADO
# ============================================================

st.markdown(
    '<div class="main-title">Magic Print Analytics</div>',
    unsafe_allow_html=True
)

if st.session_state["mensaje_carga"]:
    st.success(st.session_state["mensaje_carga"])
    st.session_state["mensaje_carga"] = ""


hoja = conectar_hoja()

if hoja is None:
    st.stop()


# ============================================================
# CARGA DEL PDF
# ============================================================

with st.sidebar:
    st.header("Cargar facturas PDF")

    archivo_pdf = st.file_uploader(
        "Selecciona un archivo PDF",
        type=["pdf"]
    )

    if archivo_pdf:
        st.success(
            f"Archivo seleccionado:\n{archivo_pdf.name}"
        )

        if st.button(
            "Procesar PDF",
            type="primary",
            use_container_width=True
        ):
            try:
                with st.spinner("Procesando el PDF..."):
                    st.session_state["registros_pdf"] = (
                        extraer_datos_pdf(archivo_pdf)
                    )

                st.rerun()

            except Exception as error:
                st.error(
                    f"No fue posible procesar el PDF: {error}"
                )


# ============================================================
# PREVISUALIZACIÓN Y DUPLICADOS
# ============================================================

registros_pdf = st.session_state["registros_pdf"]

if registros_pdf:

    st.markdown(
        '<div class="section-title">Vista previa del PDF</div>',
        unsafe_allow_html=True
    )

    df_pdf = pd.DataFrame(
        registros_pdf,
        columns=COLUMNAS
    )

    st.caption(
        f"Se encontraron {len(df_pdf)} líneas "
        f"correspondientes a "
        f"{df_pdf['Factura #'].nunique()} facturas."
    )

    st.dataframe(
        df_pdf,
        use_container_width=True,
        hide_index=True
    )

    informacion = obtener_informacion_duplicados(
        hoja,
        registros_pdf
    )

    repetidas = sorted(
        informacion["facturas_existentes"]
    )

    nuevas = sorted(
        informacion["facturas_nuevas"]
    )

    if repetidas:

        st.warning(
            f"El PDF contiene {len(repetidas)} facturas "
            "que ya existen en Google Sheets."
        )

        col1, col2, col3 = st.columns(3)

        col1.metric("Facturas repetidas", len(repetidas))
        col2.metric(
            "Líneas repetidas",
            len(informacion["filas_a_borrar"])
        )
        col3.metric("Facturas nuevas", len(nuevas))

        with st.expander("Ver facturas repetidas"):
            st.write(", ".join(repetidas))

        if nuevas:
            st.info(
                "Puedes cargar únicamente las facturas nuevas. "
                "Las repetidas no serán modificadas."
            )
        else:
            st.info(
                "Todas las facturas del PDF ya están cargadas. "
                "El botón de cargar nuevas está desactivado."
            )

        st.markdown("### Selecciona una acción")

        confirmar = st.checkbox(
            "Confirmo que deseo reemplazar las facturas repetidas.",
            key="confirmar_reemplazo"
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.button(
                "Cargar solo facturas nuevas",
                disabled=(len(nuevas) == 0),
                use_container_width=True,
                help="Carga únicamente facturas que no existen."
            ):
                try:
                    with st.spinner("Cargando facturas nuevas..."):
                        registros_nuevos = agregar_facturas_nuevas(
                            hoja,
                            registros_pdf,
                            informacion["facturas_existentes"]
                        )

                    st.cache_data.clear()
                    st.session_state["registros_pdf"] = None
                    st.session_state["mensaje_carga"] = (
                        f"Se cargaron {len(nuevas)} "
                        "facturas nuevas correctamente."
                    )

                    st.rerun()

                except Exception as error:
                    st.error(
                        f"No fue posible cargar las facturas: {error}"
                    )

        with col2:
            if st.button(
                "Reemplazar facturas repetidas",
                type="primary",
                disabled=(not confirmar),
                use_container_width=True,
                help=(
                    "Elimina las líneas repetidas y "
                    "carga nuevamente la información del PDF."
                )
            ):
                try:
                    with st.spinner(
                        "Reemplazando facturas repetidas..."
                    ):
                        reemplazar_facturas(
                            hoja,
                            registros_pdf,
                            informacion["filas_a_borrar"]
                        )

                    st.cache_data.clear()
                    st.session_state["registros_pdf"] = None
                    st.session_state["mensaje_carga"] = (
                        f"Se reemplazaron {len(repetidas)} "
                        "facturas correctamente."
                    )

                    st.rerun()

                except Exception as error:
                    st.error(
                        f"No fue posible reemplazar las facturas: {error}"
                    )

    else:

        st.success(
            "No se encontraron facturas repetidas. "
            "Todas son nuevas."
        )

        if st.button(
            "Cargar facturas en Google Sheets",
            type="primary",
            use_container_width=True
        ):
            try:
                with st.spinner("Cargando facturas..."):
                    hoja.append_rows(
                        registros_pdf,
                        value_input_option="USER_ENTERED"
                    )

                st.cache_data.clear()
                st.session_state["registros_pdf"] = None
                st.session_state["mensaje_carga"] = (
                    "Las facturas fueron cargadas correctamente."
                )

                st.rerun()

            except Exception as error:
                st.error(
                    f"No fue posible cargar las facturas: {error}"
                )


# ============================================================
# DASHBOARD
# ============================================================

df_base = cargar_datos()

if df_base.empty:
    st.info(
        "Google Sheets está conectado, pero todavía no contiene "
        "registros para mostrar."
    )

    st.stop()

st.sidebar.markdown("---")
st.sidebar.header("Filtros de análisis")
st.sidebar.caption(
    "Puedes seleccionar uno o varios valores en cada lista."
)

df = df_base.copy()


# ============================================================
# FILTROS EN LISTAS
# ============================================================

if "Fecha" in df.columns:
    fechas = df["Fecha"].dropna()

    if not fechas.empty:
        fecha_inicio = fechas.min().date()
        fecha_fin = fechas.max().date()

        rango = st.sidebar.date_input(
            "Rango de fechas",
            value=(fecha_inicio, fecha_fin),
            min_value=fecha_inicio,
            max_value=fecha_fin
        )

        if isinstance(rango, tuple) and len(rango) == 2:
            df = df[
                (df["Fecha"].dt.date >= rango[0]) &
                (df["Fecha"].dt.date <= rango[1])
            ]


def aplicar_filtro_lista(dataframe, columna, titulo):
    if columna not in dataframe.columns:
        return dataframe

    valores = sorted(
        dataframe[columna]
        .dropna()
        .astype(str)
        .unique()
    )

    seleccionados = st.sidebar.multiselect(
        titulo,
        options=valores,
        default=[],
        placeholder=f"Seleccione {titulo.lower()}"
    )

    if seleccionados:
        dataframe = dataframe[
            dataframe[columna].astype(str).isin(seleccionados)
        ]

    return dataframe


df = aplicar_filtro_lista(df, "Ciudad", "Ciudad")
df = aplicar_filtro_lista(df, "Vendedor", "Vendedor")
df = aplicar_filtro_lista(df, "Cliente", "Cliente")
df = aplicar_filtro_lista(df, "Unidad", "Unidad")
df = aplicar_filtro_lista(df, "Tipo", "Tipo de registro")


# ============================================================
# KPI
# ============================================================

ventas = df["Valor Total"].sum()
facturas = df["Factura #"].nunique()
clientes = df["Cliente"].nunique()
cantidad = df["Cantidad"].sum()
ticket = ventas / facturas if facturas else 0

st.markdown(
    '<div class="section-title">Indicadores comerciales</div>',
    unsafe_allow_html=True
)

k1, k2, k3, k4, k5 = st.columns(5)

with k1:
    st.markdown(
        f"""
        <div class="kpi-card blue">
            <div class="kpi-title">Ventas sin IVA</div>
            <div class="kpi-value">${ventas:,.0f}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with k2:
    st.markdown(
        f"""
        <div class="kpi-card green">
            <div class="kpi-title">Facturas realizadas</div>
            <div class="kpi-value">{facturas:,.0f}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with k3:
    st.markdown(
        f"""
        <div class="kpi-card purple">
            <div class="kpi-title">Clientes atendidos</div>
            <div class="kpi-value">{clientes:,.0f}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with k4:
    st.markdown(
        f"""
        <div class="kpi-card orange">
            <div class="kpi-title">Cantidad vendida</div>
            <div class="kpi-value">{cantidad:,.0f}</div>
        </div>
        """,
        unsafe_allow_html=True
    )

with k5:
    st.markdown(
        f"""
        <div class="kpi-card blue">
            <div class="kpi-title">Ticket promedio</div>
            <div class="kpi-value">${ticket:,.0f}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# GRÁFICOS
# ============================================================

st.markdown(
    '<div class="section-title">Análisis comercial</div>',
    unsafe_allow_html=True
)

col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        if "Fecha" in df.columns:
            datos = (
                df.groupby("Fecha", as_index=False)["Valor Total"]
                .sum()
                .sort_values("Fecha")
            )

            figura = px.line(
                datos,
                x="Fecha",
                y="Valor Total",
                markers=True,
                title="Evolución de ventas"
            )

            figura.update_layout(
                height=390,
                margin=dict(l=20, r=20, t=60, b=20),
                showlegend=False,
                xaxis_title="Fecha",
                yaxis_title="Ventas"
            )

            st.plotly_chart(
                figura,
                use_container_width=True
            )

with col2:
    with st.container(border=True):
        datos = (
            df.groupby("Ciudad", as_index=False)["Valor Total"]
            .sum()
            .sort_values("Valor Total", ascending=False)
        )

        figura = px.bar(
            datos,
            x="Ciudad",
            y="Valor Total",
            color="Ciudad",
            title="Ventas por ciudad"
        )

        figura.update_layout(
            height=390,
            margin=dict(l=20, r=20, t=60, b=20),
            showlegend=False,
            xaxis_title="Ciudad",
            yaxis_title="Ventas"
        )

        st.plotly_chart(
            figura,
            use_container_width=True
        )


col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        datos = (
            df.groupby("Vendedor", as_index=False)["Valor Total"]
            .sum()
            .sort_values("Valor Total", ascending=False)
        )

        figura = px.bar(
            datos,
            x="Valor Total",
            y="Vendedor",
            orientation="h",
            color="Vendedor",
            title="Ventas por vendedor"
        )

        figura.update_layout(
            height=430,
            margin=dict(l=20, r=20, t=60, b=20),
            showlegend=False,
            xaxis_title="Ventas",
            yaxis_title="Vendedor"
        )

        st.plotly_chart(
            figura,
            use_container_width=True
        )

with col2:
    with st.container(border=True):
        datos = (
            df.groupby("Descripcion", as_index=False)["Valor Total"]
            .sum()
            .sort_values("Valor Total", ascending=False)
            .head(15)
        )

        figura = px.bar(
            datos,
            x="Valor Total",
            y="Descripcion",
            orientation="h",
            color="Valor Total",
            title="Productos y servicios más vendidos"
        )

        figura.update_layout(
            height=430,
            margin=dict(l=20, r=20, t=60, b=20),
            showlegend=False,
            xaxis_title="Ventas",
            yaxis_title="Descripción"
        )

        st.plotly_chart(
            figura,
            use_container_width=True
        )


# ============================================================
# DETALLE
# ============================================================

st.markdown(
    '<div class="section-title">Detalle de facturación</div>',
    unsafe_allow_html=True
)

with st.container(border=True):
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )
