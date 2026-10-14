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
# ESTILOS
# ============================================================

st.markdown(
    """
    <style>
        .main-title {
            font-size: 42px;
            font-weight: 700;
            color: #19324d;
        }

        .metric-card {
            background-color: #f5f7fa;
            padding: 18px;
            border-radius: 12px;
            text-align: center;
            border: 1px solid #e1e5ea;
        }

        .metric-title {
            color: #687684;
            font-size: 14px;
        }

        .metric-value {
            color: #19324d;
            font-size: 25px;
            font-weight: 700;
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
        hoja = archivo.worksheet(NOMBRE_PESTANA)

        return hoja

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
    valor = limpiar_texto(valor)
    valor = re.sub(r"[^0-9]", "", valor)
    return valor


def convertir_numero(valor):
    if valor is None:
        return 0.0

    texto = limpiar_texto(valor)
    texto = texto.replace("$", "")
    texto = texto.replace(" ", "")

    if texto == "":
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

    partes = re.split(r"-", fecha)

    if len(partes) != 3:
        return ""

    anio = partes[0]
    mes = partes[1].upper()
    dia = partes[2].zfill(2)

    mes_numero = MESES_PDF.get(mes, mes)

    try:
        fecha_final = datetime.strptime(
            f"{anio}-{mes_numero}-{dia}",
            "%Y-%m-%d"
        )

        return fecha_final.strftime("%Y-%m-%d")

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

    texto_paginas = []

    with pdfplumber.open(io.BytesIO(contenido)) as pdf:
        for pagina in pdf.pages:
            texto = pagina.extract_text() or ""
            texto_paginas.append(texto)

    texto_completo = "\n".join(texto_paginas)

    if not texto_completo.strip():
        raise ValueError(
            "No se pudo extraer texto del PDF. "
            "Verifica que el archivo no sea únicamente una imagen escaneada."
        )

    bloques_factura = re.split(
        r"(?=Factura\s*(?:No|N[°º]|#)\s*:?\s*[A-Z0-9-]+)",
        texto_completo,
        flags=re.IGNORECASE
    )

    if len(bloques_factura) == 1:
        bloques_factura = [texto_completo]

    for bloque in bloques_factura:

        factura_match = re.search(
            r"Factura\s*(?:No|N[°º]|#)\s*:?\s*([A-Z0-9-]+)",
            bloque,
            flags=re.IGNORECASE
        )

        if not factura_match:
            factura_match = re.search(
                r"\b(FM-\d+)\b",
                bloque,
                flags=re.IGNORECASE
            )

        if not factura_match:
            continue

        factura = limpiar_texto(factura_match.group(1)).upper()

        fecha_match = re.search(
            r"Fecha\s*:?\s*(\d{4}[-−–][A-Z]{3}[-−–]\d{2})",
            bloque,
            flags=re.IGNORECASE
        )

        fecha = ""
        if fecha_match:
            fecha = convertir_fecha_pdf(fecha_match.group(1))

        cliente_match = re.search(
            r"Cliente\s*:?\s*(.+?)(?=\s+(?:NIT|Nit)\s*:|$)",
            bloque,
            flags=re.IGNORECASE
        )

        cliente = ""
        if cliente_match:
            cliente = limpiar_texto(cliente_match.group(1))

        nit_match = re.search(
            r"NIT\s*:?\s*([0-9.\-]+)",
            bloque,
            flags=re.IGNORECASE
        )

        nit = ""
        if nit_match:
            nit = limpiar_nit(nit_match.group(1))

        ciudad_match = re.search(
            r"Ciudad\s*:?\s*(.+?)(?=\s+(?:Vendedor|Venta|Forma)\s*:|$)",
            bloque,
            flags=re.IGNORECASE
        )

        ciudad = ""
        if ciudad_match:
            ciudad = limpiar_texto(ciudad_match.group(1))

        vendedor_match = re.search(
            r"Vendedor\s*:?\s*(.+?)(?=\s+(?:Forma de Pago|Forma Pago|Pago)\s*:|$)",
            bloque,
            flags=re.IGNORECASE
        )

        vendedor = ""
        if vendedor_match:
            vendedor = limpiar_texto(vendedor_match.group(1))

        pago_match = re.search(
            r"Forma\s+de\s+Pago\s*:?\s*(.+)",
            bloque,
            flags=re.IGNORECASE
        )

        forma_pago = ""
        if pago_match:
            forma_pago = limpiar_texto(pago_match.group(1).split("\n")[0])

        # Busca líneas de productos o servicios.
        patron_linea = re.compile(
            r"(?m)^\s*"
            r"(\d{3,10})\s+"
            r"(.+?)\s+"
            r"(\d+(?:[.,]\d+)?)\s+"
            r"(MTS|KLS|UND|UN|KG|KGM|SERV|UNIDAD)\s+"
            r"([\d.,]+)\s+"
            r"(?:[\d.,]+\s+)?"
            r"([\d.,]+)"
            r"\s*$",
            flags=re.IGNORECASE
        )

        lineas = patron_linea.findall(bloque)

        # Segundo patrón para documentos donde no aparece la unidad.
        if not lineas:
            patron_linea_sin_unidad = re.compile(
                r"(?m)^\s*"
                r"(\d{3,10})\s+"
                r"(.+?)\s+"
                r"(\d+(?:[.,]\d+)?)\s+"
                r"([\d.,]+)\s+"
                r"([\d.,]+)"
                r"\s*$",
                flags=re.IGNORECASE
            )

            lineas_sin_unidad = patron_linea_sin_unidad.findall(bloque)

            for codigo, descripcion, cantidad, precio, total in lineas_sin_unidad:
                lineas.append(
                    (
                        codigo,
                        descripcion,
                        cantidad,
                        "UND",
                        precio,
                        total
                    )
                )

        for linea in lineas:
            codigo = limpiar_texto(linea[0])
            descripcion = limpiar_texto(linea[1])
            cantidad = convertir_numero(linea[2])
            unidad = limpiar_texto(linea[3]).upper()
            precio_unitario = convertir_numero(linea[4])
            valor_total = convertir_numero(linea[5])

            if not codigo or valor_total == 0:
                continue

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
                19,
                forma_pago
            ])

    if not registros:
        raise ValueError(
            "No se encontraron líneas de productos o servicios. "
            "Revisa el formato del PDF."
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
            "facturas_nuevas": set()
        }

    encabezados = [
        limpiar_texto(columna)
        for columna in datos[0]
    ]

    if "Factura #" not in encabezados:
        raise ValueError(
            "No existe la columna 'Factura #' en la fila 1 de Google Sheets."
        )

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

    facturas_nuevas = facturas_pdf - facturas_existentes

    return {
        "facturas_existentes": facturas_existentes,
        "filas_a_borrar": filas_a_borrar,
        "facturas_nuevas": facturas_nuevas
    }


def agregar_facturas_nuevas(hoja, registros_pdf, facturas_existentes):
    registros_nuevos = [
        registro
        for registro in registros_pdf
        if limpiar_texto(registro[0]) not in facturas_existentes
    ]

    if registros_nuevos:
        hoja.append_rows(
            registros_nuevos,
            value_input_option="USER_ENTERED"
        )

    return registros_nuevos


def reemplazar_facturas(hoja, registros_pdf, filas_a_borrar):
    # Se eliminan de abajo hacia arriba para no alterar los números de fila.
    for numero_fila in sorted(filas_a_borrar, reverse=True):
        hoja.delete_rows(numero_fila)

    hoja.append_rows(
        registros_pdf,
        value_input_option="USER_ENTERED"
    )


# ============================================================
# LECTURA DE GOOGLE SHEETS
# ============================================================

@st.cache_data(ttl=30)
def cargar_datos():
    hoja = conectar_hoja()

    if hoja is None:
        return pd.DataFrame()

    datos = hoja.get_all_values()

    if not datos:
        return pd.DataFrame(columns=COLUMNAS)

    encabezados = [
        limpiar_texto(columna)
        for columna in datos[0]
    ]

    if len(datos) == 1:
        return pd.DataFrame(columns=encabezados)

    filas = datos[1:]

    cantidad_columnas = len(encabezados)

    filas_ajustadas = []

    for fila in filas:
        fila = list(fila)

        if len(fila) < cantidad_columnas:
            fila.extend([""] * (cantidad_columnas - len(fila)))

        if len(fila) > cantidad_columnas:
            fila = fila[:cantidad_columnas]

        filas_ajustadas.append(fila)

    df = pd.DataFrame(
        filas_ajustadas,
        columns=encabezados
    )

    for columna in ["Cantidad", "Precio Unitario", "Valor Total", "% IVA"]:
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
        servicios = ["888912", "888916", "888923"]

        df["Tipo"] = np.where(
            df["Codigo Articulo"].isin(servicios),
            "Servicio",
            "Producto"
        )

    if "Valor Total" in df.columns and "% IVA" in df.columns:
        df["Ventas con IVA"] = (
            df["Valor Total"] *
            (1 + df["% IVA"] / 100)
        )

    return df


# ============================================================
# INICIO DE LA APLICACIÓN
# ============================================================

if "registros_pdf" not in st.session_state:
    st.session_state["registros_pdf"] = None

if "mensaje" not in st.session_state:
    st.session_state["mensaje"] = ""


st.markdown(
    '<div class="main-title">Magic Print Analytics</div>',
    unsafe_allow_html=True
)

hoja = conectar_hoja()

if hoja is None:
    st.stop()


# ============================================================
# CARGA DEL PDF
# ============================================================

st.sidebar.header("Cargar facturas PDF")

archivo_pdf = st.sidebar.file_uploader(
    "Selecciona un archivo PDF",
    type=["pdf"]
)

if archivo_pdf is not None:
    st.sidebar.success(
        f"Archivo seleccionado: {archivo_pdf.name}"
    )

    if st.sidebar.button(
        "Procesar PDF",
        type="primary",
        key="procesar_pdf"
    ):
        try:
            with st.spinner("Procesando el PDF..."):
                registros = extraer_datos_pdf(archivo_pdf)

            st.session_state["registros_pdf"] = registros
            st.success(
                f"Se encontraron {len(registros)} líneas de factura."
            )
            st.rerun()

        except Exception as error:
            st.error(f"No fue posible procesar el PDF: {error}")


# ============================================================
# PREVISUALIZACIÓN Y CONFIRMACIÓN DE CARGA
# ============================================================

registros_pdf = st.session_state.get("registros_pdf")

if registros_pdf:

    st.subheader("Vista previa del PDF")

    df_pdf = pd.DataFrame(
        registros_pdf,
        columns=COLUMNAS
    )

    st.write(
        f"Registros encontrados: {len(df_pdf)}"
    )

    st.dataframe(
        df_pdf,
        use_container_width=True,
        hide_index=True
    )

    try:
        informacion = obtener_informacion_duplicados(
            hoja,
            registros_pdf
        )

        facturas_existentes = sorted(
            informacion["facturas_existentes"]
        )

        facturas_nuevas = sorted(
            informacion["facturas_nuevas"]
        )

        if facturas_existentes:
            st.warning(
                "Se encontraron facturas que ya están cargadas en Google Sheets."
            )

            st.write(
                "Facturas repetidas: "
                + ", ".join(facturas_existentes)
            )

            st.write(
                f"Líneas existentes relacionadas: "
                f"{len(informacion['filas_a_borrar'])}"
            )

            st.info(
                "Si eliges cargar únicamente las nuevas, "
                "las facturas repetidas serán ignoradas."
            )

            st.info(
                "Si eliges reemplazar, se eliminarán las líneas "
                "existentes de esas facturas y se cargarán nuevamente."
            )

            confirmar_reemplazo = st.checkbox(
                "Confirmo que deseo reemplazar las facturas repetidas.",
                key="confirmar_reemplazo"
            )

            col1, col2 = st.columns(2)

            with col1:
                if st.button(
                    "Cargar solo facturas nuevas",
                    key="cargar_solo_nuevas"
                ):
                    registros_nuevos = agregar_facturas_nuevas(
                        hoja,
                        registros_pdf,
                        informacion["facturas_existentes"]
                    )

                    if registros_nuevos:
                        st.cache_data.clear()
                        st.session_state["registros_pdf"] = None

                        st.success(
                            f"Se cargaron {len(registros_nuevos)} "
                            "líneas nuevas."
                        )

                        st.rerun()

                    else:
                        st.info(
                            "No hay facturas nuevas para cargar."
                        )

            with col2:
                if st.button(
                    "Reemplazar repetidas y cargar nuevas",
                    type="primary",
                    key="reemplazar_y_cargar"
                ):
                    if not confirmar_reemplazo:
                        st.error(
                            "Debes confirmar el reemplazo "
                            "antes de continuar."
                        )
                    else:
                        reemplazar_facturas(
                            hoja,
                            registros_pdf,
                            informacion["filas_a_borrar"]
                        )

                        st.cache_data.clear()
                        st.session_state["registros_pdf"] = None

                        st.success(
                            "Las facturas repetidas fueron reemplazadas "
                            "y las nuevas fueron cargadas."
                        )

                        st.rerun()

        else:
            st.success(
                "No se encontraron facturas repetidas. "
                "Todas serán cargadas."
            )

            if st.button(
                "Cargar facturas en Google Sheets",
                type="primary",
                key="cargar_facturas_nuevas"
            ):
                hoja.append_rows(
                    registros_pdf,
                    value_input_option="USER_ENTERED"
                )

                st.cache_data.clear()
                st.session_state["registros_pdf"] = None

                st.success(
                    "Las facturas fueron cargadas correctamente."
                )

                st.rerun()

    except Exception as error:
        st.error(
            f"No fue posible validar las facturas existentes: {error}"
        )


# ============================================================
# CARGA DE DATOS PARA EL DASHBOARD
# ============================================================

df_base = cargar_datos()

if df_base.empty:
    st.info(
        "Google Sheets está conectado, pero todavía no contiene registros. "
        "Carga un PDF desde la barra lateral."
    )

    st.stop()


# ============================================================
# FILTROS
# ============================================================

st.sidebar.markdown("---")
st.sidebar.header("Filtros de análisis")

df = df_base.copy()

if "Fecha" in df.columns:
    fechas_validas = df["Fecha"].dropna()

    if not fechas_validas.empty:
        fecha_minima = fechas_validas.min().date()
        fecha_maxima = fechas_validas.max().date()

        rango_fechas = st.sidebar.date_input(
            "Rango de fechas",
            value=(fecha_minima, fecha_maxima),
            min_value=fecha_minima,
            max_value=fecha_maxima
        )

        if isinstance(rango_fechas, tuple) and len(rango_fechas) == 2:
            inicio, fin = rango_fechas

            df = df[
                (df["Fecha"].dt.date >= inicio) &
                (df["Fecha"].dt.date <= fin)
            ]

if "Ciudad" in df.columns:
    ciudades = sorted(
        df["Ciudad"]
        .dropna()
        .astype(str)
        .unique()
    )

    ciudades_seleccionadas = st.sidebar.multiselect(
        "Ciudad",
        ciudades,
        default=ciudades
    )

    df = df[df["Ciudad"].isin(ciudades_seleccionadas)]

if "Vendedor" in df.columns:
    vendedores = sorted(
        df["Vendedor"]
        .dropna()
        .astype(str)
        .unique()
    )

    vendedores_seleccionados = st.sidebar.multiselect(
        "Vendedor",
        vendedores,
        default=vendedores
    )

    df = df[df["Vendedor"].isin(vendedores_seleccionados)]

if "Cliente" in df.columns:
    clientes = sorted(
        df["Cliente"]
        .dropna()
        .astype(str)
        .unique()
    )

    clientes_seleccionados = st.sidebar.multiselect(
        "Cliente",
        clientes
    )

    if clientes_seleccionados:
        df = df[df["Cliente"].isin(clientes_seleccionados)]

if "Unidad" in df.columns:
    unidades = sorted(
        df["Unidad"]
        .dropna()
        .astype(str)
        .unique()
    )

    unidades_seleccionadas = st.sidebar.multiselect(
        "Unidad",
        unidades,
        default=unidades
    )

    df = df[df["Unidad"].isin(unidades_seleccionadas)]

if "Tipo" in df.columns:
    tipos = sorted(df["Tipo"].dropna().unique())

    tipos_seleccionados = st.sidebar.multiselect(
        "Tipo de registro",
        tipos,
        default=tipos
    )

    df = df[df["Tipo"].isin(tipos_seleccionados)]


# ============================================================
# DASHBOARD
# ============================================================

st.subheader("Indicadores comerciales")

ventas = df["Valor Total"].sum() if "Valor Total" in df.columns else 0
facturas = df["Factura #"].nunique() if "Factura #" in df.columns else 0
clientes = df["Cliente"].nunique() if "Cliente" in df.columns else 0
cantidad = df["Cantidad"].sum() if "Cantidad" in df.columns else 0
ticket_promedio = ventas / facturas if facturas else 0

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric(
    "Ventas sin IVA",
    f"${ventas:,.0f}"
)

col2.metric(
    "Facturas",
    f"{facturas:,.0f}"
)

col3.metric(
    "Clientes",
    f"{clientes:,.0f}"
)

col4.metric(
    "Unidades vendidas",
    f"{cantidad:,.0f}"
)

col5.metric(
    "Ticket promedio",
    f"${ticket_promedio:,.0f}"
)


# ============================================================
# GRÁFICOS
# ============================================================

st.subheader("Análisis de ventas")

col1, col2 = st.columns(2)

with col1:
    if "Fecha" in df.columns and "Valor Total" in df.columns:
        ventas_tiempo = (
            df.groupby("Fecha", as_index=False)["Valor Total"]
            .sum()
            .sort_values("Fecha")
        )

        figura = px.line(
            ventas_tiempo,
            x="Fecha",
            y="Valor Total",
            markers=True,
            title="Evolución de ventas"
        )

        figura.update_layout(
            yaxis_title="Ventas",
            xaxis_title="Fecha"
        )

        st.plotly_chart(
            figura,
            use_container_width=True
        )

with col2:
    if "Ciudad" in df.columns and "Valor Total" in df.columns:
        ventas_ciudad = (
            df.groupby("Ciudad", as_index=False)["Valor Total"]
            .sum()
            .sort_values("Valor Total", ascending=False)
        )

        figura = px.bar(
            ventas_ciudad,
            x="Ciudad",
            y="Valor Total",
            color="Ciudad",
            title="Ventas por ciudad"
        )

        figura.update_layout(
            showlegend=False,
            yaxis_title="Ventas",
            xaxis_title="Ciudad"
        )

        st.plotly_chart(
            figura,
            use_container_width=True
        )


col1, col2 = st.columns(2)

with col1:
    if "Vendedor" in df.columns and "Valor Total" in df.columns:
        ventas_vendedor = (
            df.groupby("Vendedor", as_index=False)["Valor Total"]
            .sum()
            .sort_values("Valor Total", ascending=False)
        )

        figura = px.bar(
            ventas_vendedor,
            x="Valor Total",
            y="Vendedor",
            orientation="h",
            color="Vendedor",
            title="Ventas por vendedor"
        )

        figura.update_layout(
            showlegend=False,
            xaxis_title="Ventas",
            yaxis_title="Vendedor"
        )

        st.plotly_chart(
            figura,
            use_container_width=True
        )

with col2:
    if "Descripcion" in df.columns and "Valor Total" in df.columns:
        ventas_producto = (
            df.groupby("Descripcion", as_index=False)["Valor Total"]
            .sum()
            .sort_values("Valor Total", ascending=False)
            .head(15)
        )

        figura = px.bar(
            ventas_producto,
            x="Valor Total",
            y="Descripcion",
            orientation="h",
            color="Valor Total",
            title="Productos y servicios con mayor venta"
        )

        figura.update_layout(
            yaxis_title="Descripción",
            xaxis_title="Ventas"
        )

        st.plotly_chart(
            figura,
            use_container_width=True
        )


# ============================================================
# TABLA DETALLADA
# ============================================================

st.subheader("Detalle de facturación")

st.dataframe(
    df,
    use_container_width=True,
    hide_index=True
)
