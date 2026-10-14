import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import gspread

from google.oauth2.service_account import Credentials


# ===================================================
# CONFIGURACIÓN GENERAL
# ===================================================

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


st.markdown(
    """
    <style>
    .kpi-card {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 18px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
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


# ===================================================
# CARGA Y LIMPIEZA DE GOOGLE SHEETS
# ===================================================

@st.cache_data(ttl=600)
def cargar_y_limpiar_datos():

    # Crear credenciales
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=SCOPES
    )

    # Autorizar conexión
    client = gspread.authorize(credentials)

    # Abrir archivo de Google Sheets
    spreadsheet = client.open("Base_Datos_Ventas")

    # Seleccionar la pestaña exacta
    worksheet = spreadsheet.worksheet("Hoja1")

    # Leer todos los valores
    data = worksheet.get_all_values()

    if not data:
        raise ValueError(
            "La pestaña Hoja1 está vacía."
        )

    if len(data) < 2:
        raise ValueError(
            "La pestaña Hoja1 tiene encabezados, "
            "pero no contiene registros."
        )

    # Primera fila como encabezados
    encabezados = [
        str(columna)
        .replace("\ufeff", "")
        .strip()
        for columna in data[0]
    ]

    # Crear DataFrame
    df = pd.DataFrame(
        data[1:],
        columns=encabezados
    )

    # Limpiar filas completamente vacías
    df = df.replace("", np.nan)
    df = df.dropna(how="all").copy()

    # Normalizar nombres de columnas
    df.columns = (
        df.columns
        .astype(str)
        .str.replace("\ufeff", "", regex=False)
        .str.strip()
    )

    # Normalizar posibles variaciones de nombres
    equivalencias = {
        "Código Articulo": "Codigo Articulo",
        "Código Artículo": "Codigo Articulo",
        "Codigo Artículo": "Codigo Articulo",
        "Descripción": "Descripcion",
        "Precio Unitario ": "Precio Unitario",
        "Cantidad ": "Cantidad",
        "% IVA ": "% IVA"
    }

    df.rename(
        columns=equivalencias,
        inplace=True
    )

    columnas_requeridas = [
        "Factura #",
        "Fecha",
        "Cliente",
        "Ciudad",
        "Vendedor",
        "Codigo Articulo",
        "Descripcion",
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

    # Forma de pago es opcional
    if "Forma de Pago" not in df.columns:
        df["Forma de Pago"] = "No registrada"

    # Limpiar campos de texto
    columnas_texto = [
        "Factura #",
        "Cliente",
        "Ciudad",
        "Vendedor",
        "Codigo Articulo",
        "Descripcion",
        "Forma de Pago"
    ]

    for columna in columnas_texto:
        df[columna] = (
            df[columna]
            .astype(str)
            .str.strip()
        )

    # Convertir fecha
    df["Fecha"] = pd.to_datetime(
        df["Fecha"],
        errors="coerce"
    )

    if df["Fecha"].isna().all():
        raise ValueError(
            "La columna Fecha existe, "
            "pero no contiene fechas válidas."
        )

    # Convertir cantidad
    df["Cantidad"] = (
        df["Cantidad"]
        .astype(str)
        .str.replace(",", "", regex=False)
        .str.replace("$", "", regex=False)
        .str.strip()
    )

    df["Cantidad"] = pd.to_numeric(
        df["Cantidad"],
        errors="coerce"
    ).fillna(0)

    # Convertir precio unitario
    df["Precio Unitario"] = (
        df["Precio Unitario"]
        .astype(str)
        .str.replace(",", "", regex=False)
        .str.replace("$", "", regex=False)
        .str.strip()
    )

    df["Precio Unitario"] = pd.to_numeric(
        df["Precio Unitario"],
        errors="coerce"
    ).fillna(0)

    # Convertir valor total
    df["Valor Total"] = (
        df["Valor Total"]
        .astype(str)
        .str.replace(",", "", regex=False)
        .str.replace("$", "", regex=False)
        .str.strip()
    )

    df["Valor Total"] = pd.to_numeric(
        df["Valor Total"],
        errors="coerce"
    ).fillna(0)

    # Convertir IVA
    df["% IVA"] = (
        df["% IVA"]
        .astype(str)
        .str.replace("%", "", regex=False)
        .str.replace("*", "", regex=False)
        .str.replace(",", ".", regex=False)
        .str.strip()
    )

    df["% IVA"] = pd.to_numeric(
        df["% IVA"],
        errors="coerce"
    ).fillna(0)

    # Clasificar productos y servicios
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

    # Calcular ventas con IVA
    df["Ventas con IVA"] = (
        df["Valor Total"] *
        (1 + df["% IVA"] / 100)
    )

    return df


# ===================================================
# EJECUTAR CARGA
# ===================================================

try:
    df_base = cargar_y_limpiar_datos()

except Exception as error:
    st.error(
        "No fue posible cargar la información de Google Sheets."
    )
    st.exception(error)
    st.stop()


if df_base.empty:
    st.warning(
        "La pestaña Hoja1 no contiene registros."
    )
    st.stop()


# ===================================================
# FILTROS
# ===================================================

st.sidebar.title("Filtros de análisis")

fechas_validas = df_base["Fecha"].dropna()

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
        fecha_inicio = pd.to_datetime(rango_fechas[0])
        fecha_fin = pd.to_datetime(rango_fechas[1])

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


# ===================================================
# KPIs
# ===================================================

facturas_unicas = df_filtrado["Factura #"].nunique()
clientes_unicos = df_filtrado["Cliente"].nunique()
cantidad_vendida = df_filtrado["Cantidad"].sum()

ventas_sin_iva = df_filtrado["Valor Total"].sum()
ventas_con_iva = df_filtrado["Ventas con IVA"].sum()

ticket_promedio = (
    ventas_sin_iva / facturas_unicas
    if facturas_unicas > 0
    else 0
)

precio_promedio_mts = (
    ventas_sin_iva / cantidad_vendida
    if cantidad_vendida > 0
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


# ===================================================
# ENCABEZADO DEL DASHBOARD
# ===================================================

st.title("Resumen Ejecutivo de Ventas")

st.caption(
    "Información tomada de la pestaña Hoja1 "
    "del archivo Base_Datos_Ventas."
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
    "Facturas emitidas",
    f"{facturas_unicas:,.0f}"
)

mostrar_kpi(
    col3,
    "Clientes atendidos",
    f"{clientes_unicos:,.0f}"
)

mostrar_kpi(
    col4,
    "Cantidad MTS",
    f"{cantidad_vendida:,.0f}"
)

mostrar_kpi(
    col5,
    "Ticket promedio",
    f"{ticket_promedio:,.0f}",
    "$"
)

mostrar_kpi(
    col6,
    "Precio promedio MTS",
    f"{precio_promedio_mts:,.0f}",
    "$"
)


# ===================================================
# TENDENCIA DE VENTAS
# ===================================================

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


# ===================================================
# VENTAS POR CIUDAD Y VENDEDOR
# ===================================================

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


# ===================================================
# PRODUCTOS Y SERVICIOS
# ===================================================

col_producto, col_tipo = st.columns(2)

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
            .groupby("Descripcion", as_index=False)["Cantidad"]
            .sum()
            .sort_values("Cantidad")
            .tail(10)
        )

        fig_producto = px.bar(
            datos_producto,
            x="Cantidad",
            y="Descripcion",
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


with col_tipo:

    st.subheader("Productos y servicios por ciudad")

    datos_tipo = (
        df_filtrado
        .groupby(["Ciudad", "Tipo"], as_index=False)["Valor Total"]
        .sum()
    )

    fig_tipo = px.bar(
        datos_tipo,
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

    fig_tipo.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis_title="Ventas sin IVA",
        yaxis_title="",
        legend_title=""
    )

    st.plotly_chart(
        fig_tipo,
        use_container_width=True
    )


# ===================================================
# TABLAS DETALLADAS
# ===================================================

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
        use_container_width=True
    )


with tab_pagos:

    ventas_pago = (
        df_filtrado
        .groupby("Forma de Pago", as_index=False)["Valor Total"]
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
        use_container_width=True
    )


with tab_detalle:

    columnas_mostrar = [
        "Factura #",
        "Fecha",
        "Cliente",
        "Ciudad",
        "Vendedor",
        "Codigo Articulo",
        "Descripcion",
        "Cantidad",
        "Valor Total"
    ]

    st.dataframe(
        df_filtrado[columnas_mostrar].style.format(
            {
                "Cantidad": "{:,.1f}",
                "Valor Total": "${:,.0f}"
            }
        ),
        use_container_width=True
    )
