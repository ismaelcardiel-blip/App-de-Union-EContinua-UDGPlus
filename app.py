import streamlit as st
import pandas as pd
from pypdf import PdfWriter
from PIL import Image
import io
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- CONFIGURACIÓN DE PÁGINA (SIEMPRE AL PRINCIPIO) ---
st.set_page_config(
    page_title="Unión de Datos y Documentos - UdeG", 
    page_icon="📊",
    layout="wide"
)

# --- FUNCIÓN DE CONEXIÓN A GOOGLE DRIVE ---
def conectar_google_sheets(nombre_archivo):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        # El archivo credentials.json debe estar en la misma carpeta
        creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
        client = gspread.authorize(creds)
        sheet = client.open(nombre_archivo).get_worksheet(0)
        return sheet
    except Exception as e:
        st.error(f"❌ Error de conexión: Asegúrate de que '{nombre_archivo}' esté compartido con el correo del credentials.json")
        st.caption(f"Detalle técnico: {e}")
        return None

# --- ESTILOS E IMAGEN INSTITUCIONAL ---
def mostrar_encabezado():
    col1, col2 = st.columns([1, 5])
    posibles_rutas = ["assets/logo_u.png", "logo_u.png"]
    logo_final = next((r for r in posibles_rutas if os.path.exists(r)), None)

    with col1:
        if logo_final: st.image(logo_final, width=150)
    with col2:
        st.title("Plataforma de Procesamiento de Datos y Documentos")
        st.subheader("Unidad de Educación Continua Virtual y Campus Digital Comunitario UDGPlus")

# --- LÓGICA: UNIÓN TABULAR ---
def seccion_tabular():
    st.header("📑 Unión de Archivos Tabulados")
    
    SHEET_BASE_NOMBRE = "Acredita-Bach-base"
    
    modo = st.radio("Selecciona el modo de operación:", 
                    ["Local (Subir 2 archivos)", "Google Sheets Bridge (Puente directo)"],
                    horizontal=True)

    if modo == "Local (Subir 2 archivos)":
        col_a, col_b = st.columns(2)
        with col_a:
            file_1 = st.file_uploader("1. Archivo Base (Capa destino)", type=['csv', 'xlsx'])
        with col_b:
            file_2 = st.file_uploader("2. Archivo a Unir (Capa origen)", type=['csv', 'xlsx'])

        if file_1 and file_2:
            df1 = pd.read_csv(file_1) if file_1.name.endswith('.csv') else pd.read_excel(file_1)
            df2 = pd.read_csv(file_2) if file_2.name.endswith('.csv') else pd.read_excel(file_2)
            procesar_union(df1, df2, "local")

    else:
        st.info(f"🔗 Conectado automáticamente a la base: **{SHEET_BASE_NOMBRE}**")
        nombre_sheet = st.text_input("Archivo en Google Drive:", value=SHEET_BASE_NOMBRE)
        file_origen = st.file_uploader("Subir archivo con datos nuevos (CSV/XLSX):", type=['csv', 'xlsx'])

        if nombre_sheet and file_origen:
            with st.spinner("Sincronizando con Google Drive..."):
                sheet_google = conectar_google_sheets(nombre_sheet)
                if sheet_google:
                    df_base = pd.DataFrame(sheet_google.get_all_records())
                    df_nuevo = pd.read_csv(file_origen) if file_origen.name.endswith('.csv') else pd.read_excel(file_origen)
                    procesar_union(df_base, df_nuevo, "google", sheet_google)

def procesar_union(df1, df2, tipo_destino, g_sheet_obj=None):
    st.write("---")
    if df1.empty:
        st.error("La base de datos está vacía.")
        return

    c1, c2 = st.columns(2)
    key_1 = c1.selectbox("Columna Identificadora en Base:", df1.columns)
    key_2 = c2.selectbox("Columna Identificadora en Datos Nuevos:", df2.columns)
    
    cols_to_add = st.multiselect("Columnas a añadir a la base:", [c for c in df2.columns if c != key_2])
    
    if st.button("🚀 Ejecutar Actualización" if tipo_destino == "google" else "🚀 Generar Nuevo Archivo"):
        if not cols_to_add:
            st.warning("Selecciona al menos una columna.")
        else:
            df2_subset = df2[[key_2] + cols_to_add]
            resultado = pd.merge(df1, df2_subset, left_on=key_1, right_on=key_2, how='left')
            
            if key_1 != key_2 and key_2 in resultado.columns:
                resultado = resultado.drop(columns=[key_2])

            st.success("¡Cruce completado!")
            st.dataframe(resultado.head(10))

            if tipo_destino == "google":
                with st.spinner("Subiendo cambios a Drive..."):
                    # Convertir todo a string para evitar errores de JSON con fechas/nan
                    resultado = resultado.astype(str).replace('nan', '')
                    datos_actualizados = [resultado.columns.values.tolist()] + resultado.values.tolist()
                    g_sheet_obj.clear()
                    g_sheet_obj.update('A1', datos_actualizados)
                    st.balloons()
                    st.success("✅ Google Sheets actualizado correctamente.")
            else:
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    resultado.to_excel(writer, index=False)
                st.download_button("📥 Descargar Resultado", output.getvalue(), "union_resultado.xlsx")

# --- LÓGICA: UNIÓN DOCUMENTOS ---
def seccion_documentos():
    st.header("📂 Combinar PDF e Imágenes")
    uploaded_files = st.file_uploader("Carga tus archivos", type=['pdf', 'jpg', 'png', 'jpeg'], accept_multiple_files=True)
    if uploaded_files:
        nombre_final = st.text_input("Nombre para el archivo final:", "documento_unificado.pdf")
        if st.button("🪄 Generar PDF"):
            merger = PdfWriter()
            for f in uploaded_files:
                if f.type == "application/pdf":
                    merger.append(f)
                else:
                    img = Image.open(f).convert("RGB")
                    img_pdf = io.BytesIO()
                    img.save(img_pdf, format="PDF")
                    merger.append(img_pdf)
            out = io.BytesIO()
            merger.write(out)
            st.download_button("📥 Descargar PDF", out.getvalue(), nombre_final)

# --- FUNCIÓN PRINCIPAL ---
def main():
    mostrar_encabezado()
    tab_inicio, tab_tablas, tab_docs = st.tabs(["🏠 Inicio", "📑 Unión de Tablas", "📂 Combinar Archivos"])
    
    with tab_inicio:
        st.markdown("""
        ### 🎓 Bienvenido
        Herramienta para gestión de datos de **Educación Continua UDGPlus**.
        
        * **Unión de Tablas:** Conecta con Google Drive o usa archivos locales.
        * **Combinar Archivos:** Une PDFs e imágenes en un solo documento.
        """)
        
    with tab_tablas:
        seccion_tabular()

    with tab_docs:
        seccion_documentos()

    st.sidebar.markdown("---")
    st.sidebar.caption("© 2026 UdeG - Sistema de Procesamiento.")

if __name__ == "__main__":
    main()
