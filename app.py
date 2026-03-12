import streamlit as st
import pandas as pd
from pypdf import PdfWriter
from PIL import Image
import io
import os
import gspread
import datetime
from oauth2client.service_account import ServiceAccountCredentials

# 1. CONFIGURACIÓN DE PÁGINA
if 'config_ok' not in st.session_state:
    st.set_page_config(page_title="Unión de Datos - UdeG", page_icon="📊", layout="wide")
    st.session_state.config_ok = True

# --- VARIABLES GLOBALES ---
SHEET_BASE_NOMBRE = "Acredita-Bach-base"
ID_CARPETA_RESPALDO = "1iRI4ug3fQEOnA_UeKUaXcM98mEQsaQCg"

# --- FUNCIONES ---
def conectar_google(nombre_archivo):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        if "google_creds" in st.secrets:
            creds_dict = dict(st.secrets["google_creds"])
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        else:
            st.error("❌ No se encontraron los Secrets en Streamlit.")
            return None
        
        client = gspread.authorize(creds)
        # Intentamos abrir el archivo (Debe ser formato Google Sheets nativo)
        return client.open(nombre_archivo).get_worksheet(0)
    except Exception as e:
        if "200" in str(e):
            return client.open(nombre_archivo).get_worksheet(0)
        st.error(f"Error de conexión: {e}")
        return None

def respaldar(sheet_obj):
    try:
        fecha = datetime.datetime.now().strftime("%Y%m%d_%H%M")
        nombre_respaldo = f"Backup_{fecha}_{SHEET_BASE_NOMBRE}"
        
        # Copia el archivo directamente a tu carpeta compartida
        # Esto usa TU espacio de almacenamiento
        sheet_obj.client.copy(
            sheet_obj.spreadsheet.id, 
            title=nombre_respaldo, 
            folder_id=ID_CARPETA_RESPALDO
        )
        return True, nombre_respaldo
    except Exception as e:
        return False, str(e)

# --- INTERFAZ ---
st.title("📊 Plataforma de Datos UDGPlus")
st.markdown("---")

tab1, tab2 = st.tabs(["📑 Unión de Tablas (Drive)", "📂 Unificador de PDFs"])

with tab1:
    st.header("Actualización de Base de Datos")
    st.info(f"🔗 Conectado a: **{SHEET_BASE_NOMBRE}**")
    
    archivo_nuevo = st.file_uploader("Subir archivo con nuevos datos (Excel/CSV):", type=['xlsx', 'csv'], key="up_drive")
    
    if archivo_nuevo:
        with st.spinner("Leyendo base de datos en la nube..."):
            sheet = conectar_google(SHEET_BASE_NOMBRE)
            
            if sheet:
                # Obtener datos actuales
                df_drive = pd.DataFrame(sheet.get_all_records())
                # Leer archivo subido
                df_subido = pd.read_csv(archivo_nuevo) if archivo_nuevo.name.endswith('.csv') else pd.read_excel(archivo_nuevo)
                
                if not df_drive.empty:
                    col1, col2 = st.columns(2)
                    id_drive = col1.selectbox("ID en Drive (Columna común):", df_drive.columns, key="id_d")
                    id_subido = col2.selectbox("ID en archivo subido:", df_subido.columns, key="id_s")
                    
                    columnas_extra = st.multiselect(
                        "Selecciona las columnas que quieres añadir a la base:",
                        [c for c in df_subido.columns if c != id_subido],
                        key="cols_e"
                    )
                    
                    if st.button("🚀 Actualizar Base en Drive", key="btn_actualizar"):
                        if not columnas_extra:
                            st.warning("Selecciona al menos una columna.")
                        else:
                            with st.spinner("Procesando y creando respaldo..."):
                                # 1. Hacer el cruce
                                resultado = pd.merge(df_drive, df_subido[[id_subido] + columnas_extra], 
                                                    left_on=id_drive, right_on=id_subido, how='left')
                                if id_drive != id_subido:
                                    resultado = resultado.drop(columns=[id_subido])
                                
                                # 2. Respaldar en la carpeta nueva
                                exito_r, msg_r = respaldar(sheet)
                                
                                if exito_r:
                                    # 3. Limpiar y subir
                                    resultado = resultado.astype(str).replace(['nan', 'NaN', 'None'], '')
                                    datos_lista = [resultado.columns.tolist()] + resultado.values.tolist()
                                    
                                    sheet.clear()
                                    sheet.update('A1', datos_lista)
                                    
                                    st.success(f"✅ ¡Base actualizada! Respaldo guardado en tu carpeta como: {msg_r}")
                                    st.balloons()
                                    st.dataframe(resultado.head())
                                else:
                                    st.error(f"❌ Error al crear respaldo: {msg_r}. No se modificó la base.")
                else:
                    st.error("La base en Drive está vacía o no tiene encabezados válidos.")

with tab2:
    st.header("Combinar Documentos")
    pdfs = st.file_uploader("Sube tus PDFs o Imágenes:", accept_multiple_files=True, key="up_pdf_unir")
    
    if pdfs and st.button("🪄 Generar PDF Unificado", key="btn_pdf_unir"):
        merger = PdfWriter()
        for p in pdfs:
            if p.type == "application/pdf":
                merger.append(p)
            else:
                img = Image.open(p).convert("RGB")
                img_io = io.BytesIO()
                img.save(img_io, format="PDF")
                merger.append(img_io)
        
        output_pdf = io.BytesIO()
        merger.write(output_pdf)
        st.download_button("📥 Descargar PDF Final", output_pdf.getvalue(), "unificado_udg.pdf")

st.sidebar.markdown("---")
st.sidebar.caption("UDGPlus - Unidad de Educación Continua")
