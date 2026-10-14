import io
import re

import numpy as np
import pandas as pd
import pdfplumber
import plotly.express as px
import streamlit as st
import gspread

from google.oauth2.service_account import Credentials


# =====================================================
# CONFIGURACIÓN
# =====================================================

st.set_page_config(
    page_title="Magic Print Analytics",
    page_icon="📊",
    layout="wide"
)

COLOR_PRINCIPAL = "#2563EB"
COLOR_SECUNDARIO = "#38BDF8"
COLOR_TERCIARIO = "#10B981"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

NOMBRE_ARCHIVO = "Base_Datos_Ventas"
NOMBRE_PESTANA = "Hoja1"

COLUMNAS_GOOGLE_SHEETS = [
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


st.markdown(
    """
    <style>
    .kpi-card {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 18px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border-left: 5px solid #2563EB;
        margin-bottom: 20px;
    }

    .kpi-title {
        color: #64748B;
        font-size: 13px;
        font-weight: 600;
        text-transform: uppercase;
        margin-bottom: 5px;
    }

    .kpi-value {
        color: #0F172A;
        font-size: 25px;
        font-weight: bold;
    }

    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# =====================================================
# CONEXIÓN CON GOOGLE SHEETS
# =====================================================

@st.cache_resource
def conectar_hoja():
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=SCOPES
    )

    client = gspread.authorize(credentials)

    spreadsheet = client.open(NOMBRE_ARCHIVO)

    worksheet = spreadsheet.worksheet(NOMBRE_PESTANA)

    return worksheet


# =====================================================
# FUNCIONES DE CONVERSIÓN
# =====================================================

MESES_PDF = {
    "ENE": "01",
    "FEB": "02",
    "MAR": "03",
    "ABR": "04",
    "MAY": "05",
    "JUN": "06",
    "JUL": "07",
    "AGO": "08",
    "SEP": "09",
    "OCT": "10",
    "NOV": "11",
    "DIC": "12"
}


def convertir_numero(valor):
    if valor is None:
        return 0

    texto = str(valor).strip()
    texto = texto.replace("−", "-")
    texto = texto.replace(",", "")

    try:
        return float(texto)
    except ValueError:
        return 0


def convertir_fecha_pdf(fecha_pdf):
    if not fecha_pdf:
        return ""

    fecha_limpia = (
        str(fecha_pdf)
        .replace("−", "-")
        .strip()
        .upper()
    )

    partes = fecha_limpia.split("-")

    if len(partes) != 3:
        return ""

    anio = partes[0]
    mes_texto = partes[1]
    dia = partes[2]

    mes = MESES_PDF.get(mes_texto)

    if not mes:
        return ""

    return f"{anio}-{mes}-{dia}"


def limpiar_nit(nit):
    if not nit:
        return ""

    nit = (
        str(nit)
        .replace("−", "-")
        .strip()
    )

    if "-" in nit:
        nit = nit.split("-")[0]

    return nit.strip()


# =====================================================
# EXTRACCIÓN DEL PDF
# =====================================================

def extraer_datos_pdf(archivo_pdf):

    registros = []

    contenido_pdf = archivo_pdf.getvalue()

    patron_factura = re.compile(
        r"Numero\s*:\s*(FM[-−]\d+)",
        re.IGNORECASE
    )

    patron_fecha = re.compile(
        r"Fecha\s*:\s*(\d{4}[-−][A-Z]{3}[-−]\d{2})",
        re.IGNORECASE
    )

    patron_cliente = re.compile(
        r"Cliente\s*:\s*([^|\n]+)",
        re.IGNORECASE
    )

    patron_nit = re.compile(
        r"Nit o C\.C\.\s*:\s*([0-9−-]+)",
        re.IGNORECASE
    )

    patron_ciudad = re.compile(
        r"Ciudad\s*:\s*([^|\n]+)",
        re.IGNORECASE
    )

    patron_vendedor = re.compile(
        r"Vendedor:\s*\d+\s*(?:\|?\s*)([^|\n]+)",
        re.IGNORECASE
    )

    patron_pago = re.compile(
        r"\|\s*(CREDITO[^|]+|CONTADO[^|]+)\s*\|",
        re.IGNORECASE
    )

    # Acepta MTS, KLS y otras unidades de hasta cuatro letras.
    patron_item = re.compile(
        r"^(\d{3,10})\s+(.+?)\s+"
        r"(\d+)\s+"
        r"([\d,.]+)\s+"
        r"([A-Z]{2,4})\s+"
        r"([\d,.−-]+)\s+"
        r"([\d,.−-]+)\s+"
        r"([\d,.−-]+)"
        r"(?:\s+([\d,.−-]+)\*)?$",
        re.IGNORECASE
    )

    with pdfplumber.open(io.BytesIO(contenido_pdf)) as pdf:

        for pagina in pdf.pages:

            texto = pagina.extract_text() or ""

            if not texto.strip():
                continue

            factura_match = patron_factura.search(texto)

            if not factura_match:
                continue

            factura = (
                factura_match.group(1)
                .replace("−", "-")
                .strip()
            )

            fecha_match = patron_fecha.search(texto)

            fecha = (
                convertir_fecha_pdf(
                    fecha_match.group(1)
                )
                if fecha_match
                else ""
            )

            cliente_match = patron_cliente.search(texto)

            cliente = (
                cliente_match.group(1).strip()
                if cliente_match
                else ""
            )

            nit_match = patron_nit.search(texto)

            nit = (
                limpiar_nit(nit_match.group(1))
                if nit_match
                else ""
            )

            ciudad_match = patron_ciudad.search(texto)

            ciudad = (
                ciudad_match.group(1)
                .split("+")[0]
                .strip()
                if ciudad_match
                else ""
            )

            vendedor_match = patron_vendedor.search(texto)

            vendedor = (
                vendedor_match.group(1).strip()
                if vendedor_match
                else ""
            )

            pago_match = patron_pago.search(texto)

            forma_pago = (
                pago_match.group(1).strip()
                if pago_match
                else "No registrada"
            )

            for linea in texto.splitlines():

                linea_limpia = (
                    linea
                    .strip()
                    .strip("|")
                    .strip()
                )

                item_match = patron_item.match(
                    linea_limpia
                )

                if not item_match:
                    continue

                codigo = item_match.group(1)
                descripcion = item_match.group(2).strip()

                cantidad = convertir_numero(
                    item_match.group(4)
                )

                unidad = item_match.group(5).upper()

                precio_unitario = convertir_numero(
                    item_match.group(6)
                )

                valor_total = convertir_numero(
                    item_match.group(8)
                )

                iva = (
                    convertir_numero(item_match.group(9))
                    if item_match.group(9)
                    else (
                        19
                        if "*" in linea
                        else 0
                    )
                )

                registros.append([
                    factura,
                    fecha,
                    cliente,
                    nit,
                    ciudad,
                    vendedor,
                    codigo,
                    descripcion,
                    unidad,
                    cantidad,
                    precio_unitario,
                    valor_total,
                    iva,
                    forma_pago
                ])

    return registros


# =====================================================
# CONTROL DE DUPLICADOS
# =====================================================

def normalizar_clave(valor):
    return str(valor).strip().upper()


def obtener_clave_registro(fila):

    factura = normalizar_clave(fila[0])
    codigo = normalizar_clave(fila[6])
    valor = round(convertir_numero(fila[11]), 2)

    return factura, codigo, valor


def filtrar_registros_nuevos(worksheet, registros):

    datos_existentes = worksheet.get_all_values()

    if len(datos_existentes) < 2:
        return registros

    encabezados = [
        str(valor).strip()
        for valor in datos_existentes[0]
    ]

    posiciones = {
        nombre: indice
        for indice, nombre in enumerate(encabezados)
    }

    requeridas = [
        "Factura #",
        "Codigo Articulo",
        "Valor Total"
    ]

    if not all(
        columna in posiciones
        for columna in requeridas
    ):
        return registros

    claves_existentes = set()

    for fila in datos_existentes[1:]:

        if not fila:
            continue

        try:
            factura = fila[posiciones["Factura #"]]
            codigo = fila[posiciones["Codigo Articulo"]]
            valor = fila[posiciones["Valor Total"]]

            clave = (
                normalizar_clave(factura),
                normalizar_clave(codigo),
                round(convertir_numero(valor), 2)
            )

            claves_existentes.add(clave)

        except IndexError:
            continue

    registros_nuevos = []

    for registro in registros:

        clave = obtener_clave_registro(registro)

        if clave not in claves_existentes:
            registros_nuevos.append(registro)

    return registros_nuevos


# =====================================================
# CARGA Y LIMPIEZA DE DATOS
# =====================================================

@st.cache_data(ttl=600)
def cargar_y_limpiar_datos():

    worksheet = conectar_hoja()

    data = worksheet.get_all_values()

    if not data:
        return pd.DataFrame()

    if len(data) < 2:

        encabezados = [
            str(columna)
            .replace("\ufeff", "")
            .strip()
            for columna in data[0]
        ]

        return pd.DataFrame(columns=encabezados)

    encabezados = [
        str(columna)
        .replace("\ufeff", "")
        .strip()
        for columna in data[0]
    ]

    df = pd.DataFrame(
        data[1:],
        columns=encabezados
    )

    df = df.replace("", np.nan)
    df = df.dropna(how="all").copy()

    if df.empty:
        return df

    df.columns = (
        df.columns
        .astype(str)
        .str.replace("\ufeff", "", regex=False)
        .str.strip()
    )

    equivalencias = {
        "Código Articulo": "Codigo Articulo",
        "Código Artículo": "Codigo Articulo",
        "Codigo Artículo": "Codigo Articulo",
        "Descripción": "Descripcion",
        "Precio Unitario ": "Precio Unitario",
        "Cantidad ": "Cantidad",
        "% IVA ": "% IVA",
        "Unidad ": "Unidad"
    }

    df.rename(
        columns=equivalencias,
        inplace=True
    )

    columnas_requeridas = [
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
        "% IVA"
    ]

    columnas_faltantes = [
        columna
        for columna in columnas_requeridas
        if columna not in df.columns
    ]

    if columnas_faltantes:
        raise ValueError(
            f"Columnas faltantes: {columnas_faltantes}. "
            f"Columnas encontradas: {list(df.columns)}"
        )

    if "Forma de Pago" not in df.columns:
        df["Forma de Pago"] = "No registrada"

    columnas_texto = [
        "Factura #",
        "Cliente",
        "Nit",
        "Ciudad",
        "Vendedor",
        "Codigo Articulo",
        "Descripcion",
        "Unidad",
        "Forma de Pago"
    ]

    for columna in columnas_texto:
        df[columna] = (
            df[columna]
            .astype(str)
            .str.strip()
        )

    df["Fecha"] = pd.to_datetime(
        df["Fecha"],
        errors="coerce"
    )

    for columna in [
        "Cantidad",
        "Precio Unitario",
        "Valor Total",
        "% IVA"
    ]:

        df[columna] = (
            df[columna]
            .astype(str)
            .str.replace(",", "", regex=False)
            .str.replace("$", "", regex=False)
            .str.replace("%", "", regex=False)
            .str.replace("*", "", regex=False)
            .str.strip()
        )

        df[columna] = pd.to_numeric(
            df[columna],
            errors="coerce"
        ).fillna(0)

    codigos_servicios = [
        "888912",
        "888923",
        "888916"
    ]

    df["Tipo"] = np.where(
        df["Codigo Articulo"].isin(codigos_servicios),
        "Servicio",
        "Producto"
    )

    df["Ventas con IVA"] = (
        df["Valor Total"] *
        (1 + df["% IVA"] / 100)
    )

    return df


# =====================================================
# BARRA LATERAL Y CARGA DE PDF
# =====================================================

st.sidebar.title("Filtros de análisis")

if st.sidebar.button("Actualizar datos"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("Cargar facturas PDF")

archivo_pdf = st.sidebar.file_uploader(
    "Selecciona un archivo PDF",
    type=["pdf"],
    help="Puedes subir un archivo con cualquier nombre."
)

if archivo_pdf is not None:

    st.sidebar.success(
        f"Archivo seleccionado: {archivo_pdf.name}"
    )

    if st.sidebar.button("Procesar PDF"):

        try:

            registros_pdf = extraer_datos_pdf(
                archivo_pdf
            )

            if not registros_pdf:
                st.error(
                    "No se encontraron líneas de factura "
                    "en el PDF."
                )
                st.stop()

            registros_nuevos = filtrar_registros_nuevos(
                conectar_hoja(),
                registros_pdf
            )

            vista_previa = pd.DataFrame(
                registros_pdf,
                columns=COLUMNAS_GOOGLE_SHEETS
            )

            st.subheader("Vista previa del PDF")

            st.write(
                f"Registros encontrados: "
                f"{len(registros_pdf)}"
            )

            st.dataframe(
                vista_previa,
                use_container_width=True,
                hide_index=True
            )

            if not registros_nuevos:

                st.warning(
                    "Todos los registros del PDF "
                    "ya existen en Google Sheets."
                )

            else:

                if st.button(
                    "Confirmar carga en Google Sheets"
                ):

                    conectar_hoja().append_rows(
                        registros_nuevos,
                        value_input_option="USER_ENTERED"
                    )

                    st.cache_data.clear()

                    st.success(
                        f"Se agregaron "
                        f"{len(registros_nuevos)} registros "
                        "a Google Sheets."
                    )

                    st.info(
                        "Pulsa 'Actualizar datos' "
                        "para ver las nuevas facturas."
                    )

        except Exception as error:

            st.error(
                "No fue posible procesar el PDF."
            )

            st.exception(error)


# =====================================================
# CARGA DEL DASHBOARD
# =====================================================

try:
    df_base = cargar_y_limpiar_datos()

except Exception as error:

    st.error(
        "No fue posible cargar la información "
        "de Google Sheets."
    )

    st.exception(error)
    st.stop()


if df_base.empty:

    st.title("Magic Print Analytics")

    st.info(
        "La conexión con Google Sheets funciona correctamente, "
        "pero Hoja1 todavía no contiene registros."
    )

    st.write(
        "Carga un PDF desde la barra lateral. "
        "Los encabezados deben estar en la fila 1."
    )

    st.stop()


# =====================================================
# FILTROS
# =====================================================

fechas_validas = df_base["Fecha"].dropna()

if fechas_validas.empty:
    st.error(
        "No hay fechas válidas en la columna Fecha."
    )
    st.stop()

fecha_min = fechas_validas.min().date()
fecha_max = fechas_validas.max().date()

rango_fechas = st.sidebar.date_input(
    "Rango de fechas",
    value=(fecha_min, fecha_max),
    min_value=fecha_min,
    max_value=fecha_max
)

df_filtrado = df_base.copy()

if isinstance(rango_fechas, tuple):
    if len(rango_fechas) == 2:

        fecha_inicio = pd.to_datetime(
            rango_fechas[0]
        )

        fecha_fin = pd.to_datetime(
            rango_fechas[1]
        )

        df_filtrado = df_filtrado[
            (df_filtrado["Fecha"] >= fecha_inicio) &
            (df_filtrado["Fecha"] <= fecha_fin)
        ]


ciudades = st.sidebar.multiselect(
    "Ciudad",
    sorted(df_filtrado["Ciudad"].unique())
)

if ciudades:
    df_filtrado = df_filtrado[
        df_filtrado["Ciudad"].isin(ciudades)
    ]


vendedores = st.sidebar.multiselect(
    "Vendedor",
    sorted(df_filtrado["Vendedor"].unique())
)

if vendedores:
    df_filtrado = df_filtrado[
        df_filtrado["Vendedor"].isin(vendedores)
    ]


clientes = st.sidebar.multiselect(
    "Cliente",
    sorted(df_filtrado["Cliente"].unique())
)

if clientes:
    df_filtrado = df_filtrado[
        df_filtrado["Cliente"].isin(clientes)
    ]


unidades = st.sidebar.multiselect(
    "Unidad",
    sorted(df_filtrado["Unidad"].unique())
)

if unidades:
    df_filtrado = df_filtrado[
        df_filtrado["Unidad"].isin(unidades)
    ]


tipos = st.sidebar.multiselect(
    "Tipo",
    sorted(df_filtrado["Tipo"].unique())
)

if tipos:
    df_filtrado = df_filtrado[
        df_filtrado["Tipo"].isin(tipos)
    ]


if df_filtrado.empty:
    st.warning(
        "No existen registros para los filtros seleccionados."
    )
    st.stop()


# =====================================================
# KPIs
# =====================================================

facturas_unicas = df_filtrado["Factura #"].nunique()
clientes_unicos = df_filtrado["Cliente"].nunique()

ventas_sin_iva = df_filtrado["Valor Total"].sum()
ventas_con_iva = df_filtrado["Ventas con IVA"].sum()

cantidad_mts = df_filtrado.loc[
    df_filtrado["Unidad"] == "MTS",
    "Cantidad"
].sum()

cantidad_kls = df_filtrado.loc[
    df_filtrado["Unidad"] == "KLS",
    "Cantidad"
].sum()

ticket_promedio = (
    ventas_sin_iva / facturas_unicas
    if facturas_unicas > 0
    else 0
)


def mostrar_kpi(
    columna,
    titulo,
    valor,
    prefijo=""
):
    columna.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">{titulo}</div>
            <div class="kpi-value">
                {prefijo}{valor}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


# =====================================================
# ENCABEZADO
# =====================================================

st.title("Magic Print Analytics")

st.caption(
    "Fuente: Base_Datos_Ventas / Hoja1"
)

st.markdown("---")

col1, col2, col3, col4, col5, col6 = st.columns(6)

mostrar_kpi(
    col1,
    "Ventas sin IVA",
    f"{ventas_sin_iva:,.0f}",
    "$"
)

mostrar_kpi(
    col2,
    "Facturas",
    f"{facturas_unicas:,.0f}"
)

mostrar_kpi(
    col3,
    "Clientes",
    f"{clientes_unicos:,.0f}"
)

mostrar_kpi(
    col4,
    "Cantidad MTS",
    f"{cantidad_mts:,.2f}"
)

mostrar_kpi(
    col5,
    "Cantidad KLS",
    f"{cantidad_kls:,.2f}"
)

mostrar_kpi(
    col6,
    "Ticket promedio",
    f"{ticket_promedio:,.0f}",
    "$"
)


# =====================================================
# TENDENCIA
# =====================================================

st.subheader("Tendencia de ventas")

ventas_diarias = (
    df_filtrado
    .groupby("Fecha", as_index=False)["Valor Total"]
    .sum()
    .sort_values("Fecha")
)

fig_tendencia = px.line(
    ventas_diarias,
    x="Fecha",
    y="Valor Total",
    markers=True,
    color_discrete_sequence=[COLOR_PRINCIPAL]
)

fig_tendencia.update_layout(
    plot_bgcolor="rgba(0,0,0,0)",
    xaxis_title="Fecha",
    yaxis_title="Ventas sin IVA"
)

st.plotly_chart(
    fig_tendencia,
    use_container_width=True
)


# =====================================================
# CIUDAD Y VENDEDOR
# =====================================================

col_ciudad, col_vendedor = st.columns(2)

with col_ciudad:

    st.subheader("Ventas por ciudad")

    ventas_ciudad = (
        df_filtrado
        .groupby("Ciudad", as_index=False)["Valor Total"]
        .sum()
        .sort_values("Valor Total")
    )

    fig_ciudad = px.bar(
        ventas_ciudad,
        x="Valor Total",
        y="Ciudad",
        orientation="h",
        text_auto=".2s",
        color_discrete_sequence=[COLOR_PRINCIPAL]
    )

    fig_ciudad.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis_title="Ventas sin IVA",
        yaxis_title=""
    )

    st.plotly_chart(
        fig_ciudad,
        use_container_width=True
    )


with col_vendedor:

    st.subheader("Ventas por vendedor")

    ventas_vendedor = (
        df_filtrado
        .groupby("Vendedor")
        .agg(
            Ventas=("Valor Total", "sum"),
            Facturas=("Factura #", "nunique")
        )
        .reset_index()
        .sort_values("Ventas")
    )

    ventas_vendedor["Ticket promedio"] = (
        ventas_vendedor["Ventas"] /
        ventas_vendedor["Facturas"]
    )

    fig_vendedor = px.bar(
        ventas_vendedor,
        x="Ventas",
        y="Vendedor",
        orientation="h",
        text_auto=".2s",
        hover_data=[
            "Facturas",
            "Ticket promedio"
        ],
        color_discrete_sequence=[COLOR_SECUNDARIO]
    )

    fig_vendedor.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis_title="Ventas sin IVA",
        yaxis_title=""
    )

    st.plotly_chart(
        fig_vendedor,
        use_container_width=True
    )


# =====================================================
# PRODUCTOS Y SERVICIOS
# =====================================================

col_producto, col_composicion = st.columns(2)

with col_producto:

    st.subheader("Ranking de productos y servicios")

    metrica = st.radio(
        "Métrica",
        [
            "Ventas",
            "Cantidad vendida",
            "Frecuencia de líneas"
        ],
        horizontal=True
    )

    if metrica == "Ventas":

        datos_producto = (
            df_filtrado
            .groupby("Descripcion", as_index=False)["Valor Total"]
            .sum()
            .sort_values("Valor Total")
            .tail(10)
        )

        fig_producto = px.bar(
            datos_producto,
            x="Valor Total",
            y="Descripcion",
            orientation="h",
            text_auto=".2s",
            color_discrete_sequence=[COLOR_PRINCIPAL]
        )

        fig_producto.update_layout(
            xaxis_title="Ventas sin IVA",
            yaxis_title=""
        )

    elif metrica == "Cantidad vendida":

        datos_producto = (
            df_filtrado
            .groupby(
                ["Descripcion", "Unidad"],
                as_index=False
            )["Cantidad"]
            .sum()
            .sort_values("Cantidad")
            .tail(10)
        )

        datos_producto["Etiqueta"] = (
            datos_producto["Descripcion"] +
            " (" +
            datos_producto["Unidad"] +
            ")"
        )

        fig_producto = px.bar(
            datos_producto,
            x="Cantidad",
            y="Etiqueta",
            orientation="h",
            text_auto=".2s",
            color_discrete_sequence=[COLOR_PRINCIPAL]
        )

        fig_producto.update_layout(
            xaxis_title="Cantidad vendida",
            yaxis_title=""
        )

    else:

        datos_producto = (
            df_filtrado
            .groupby("Descripcion")
            .size()
            .reset_index(name="Frecuencia")
            .sort_values("Frecuencia")
            .tail(10)
        )

        fig_producto = px.bar(
            datos_producto,
            x="Frecuencia",
            y="Descripcion",
            orientation="h",
            text_auto=".2s",
            color_discrete_sequence=[COLOR_PRINCIPAL]
        )

        fig_producto.update_layout(
            xaxis_title="Número de líneas",
            yaxis_title=""
        )

    fig_producto.update_layout(
        plot_bgcolor="rgba(0,0,0,0)"
    )

    st.plotly_chart(
        fig_producto,
        use_container_width=True
    )


with col_composicion:

    st.subheader("Productos y servicios por ciudad")

    datos_composicion = (
        df_filtrado
        .groupby(
            ["Ciudad", "Tipo"],
            as_index=False
        )["Valor Total"]
        .sum()
    )

    fig_composicion = px.bar(
        datos_composicion,
        x="Valor Total",
        y="Ciudad",
        color="Tipo",
        orientation="h",
        barmode="stack",
        color_discrete_map={
            "Producto": COLOR_PRINCIPAL,
            "Servicio": COLOR_TERCIARIO
        }
    )

    fig_composicion.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis_title="Ventas sin IVA",
        yaxis_title="",
        legend_title=""
    )

    st.plotly_chart(
        fig_composicion,
        use_container_width=True
    )


# =====================================================
# TABLAS DETALLADAS
# =====================================================

st.subheader("Análisis detallado")

tab_clientes, tab_pagos, tab_detalle = st.tabs(
    [
        "Ventas por cliente",
        "Forma de pago",
        "Detalle de facturas"
    ]
)


with tab_clientes:

    ventas_cliente = (
        df_filtrado
        .groupby(["Cliente", "Ciudad"])
        .agg(
            Ventas=("Valor Total", "sum"),
            Facturas=("Factura #", "nunique")
        )
        .reset_index()
        .sort_values("Ventas", ascending=False)
    )

    ventas_cliente["Ticket promedio"] = (
        ventas_cliente["Ventas"] /
        ventas_cliente["Facturas"]
    )

    st.dataframe(
        ventas_cliente.style.format(
            {
                "Ventas": "${:,.0f}",
                "Ticket promedio": "${:,.0f}"
            }
        ),
        use_container_width=True,
        hide_index=True
    )


with tab_pagos:

    ventas_pago = (
        df_filtrado
        .groupby(
            "Forma de Pago",
            as_index=False
        )["Valor Total"]
        .sum()
        .sort_values("Valor Total", ascending=False)
    )

    total_pago = ventas_pago["Valor Total"].sum()

    if total_pago > 0:
        ventas_pago["Participación %"] = (
            ventas_pago["Valor Total"] /
            total_pago
        ) * 100
    else:
        ventas_pago["Participación %"] = 0

    st.dataframe(
        ventas_pago.style.format(
            {
                "Valor Total": "${:,.0f}",
                "Participación %": "{:.1f}%"
            }
        ),
        use_container_width=True,
        hide_index=True
    )


with tab_detalle:

    columnas_mostrar = [
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
        "Valor Total"
    ]

    st.dataframe(
        df_filtrado[columnas_mostrar].style.format(
            {
                "Cantidad": "{:,.2f}",
                "Precio Unitario": "${:,.0f}",
                "Valor Total": "${:,.0f}"
            }
        ),
        use_container_width=True,
        hide_index=True
    )
