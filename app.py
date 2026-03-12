import streamlit as st
import pandas as pd
import io
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# 1. CONFIGURACIÓN DE PÁGINA
if 'config_ok' not in st.session_state:
    st.set_page_config(page_title="Unión de Datos - UdeG", page_icon="📊", layout="wide")
    st.session_state.config_ok = True

# --- VARIABLES GLOBALES ---
SHEET_BASE_NOMBRE = "Acredita-Bach-base"

# --- FUNCIONES DE SOPORTE ---
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
        return client.open(nombre_archivo).get_worksheet(0)
    except Exception as e:
        if "200" in str(e):
            return client.open(nombre_archivo).get_worksheet(0)
        st.error(f"Error de conexión: {e}")
        return None

def realizar_cruce(df_base, df_nuevo, id_base, id_nuevo, columnas):
    # Unión de datos (Left Join)
    res = pd.merge(df_base, df_nuevo[[id_nuevo] + columnas], 
                   left_on=id_base, right_on=id_nuevo, how='left')
    # Eliminar la columna ID duplicada si tienen nombres distintos
    if id_base != id_nuevo and id_nuevo in res.columns:
        res = res.drop(columns=[id_nuevo])
    # Limpieza de valores nulos para visualización y guardado
    return res.astype(str).replace(['nan', 'NaN', 'None', '<NA>'], '')

# --- INTERFAZ ---
st.title("📊 Plataforma de Datos UDGPlus")
st.subheader("Unidad de Educación Continua Virtual")
st.markdown("---")

tab1, tab2 = st.tabs(["🔗 Google Sheets Bridge", "💻 Unión Local (Excel/CSV)"])

# --- PESTAÑA 1: GOOGLE DRIVE ---
with tab1:
    st.header("Sincronización con Google Drive")
    st.info(f"Base vinculada: **{SHEET_BASE_NOMBRE}**")
    
    archivo_nuevo_g = st.file_uploader("Subir datos nuevos para añadir a Drive:", type=['xlsx', 'csv'], key="up_g_final")
    
    if archivo_nuevo_g:
        with st.spinner("Conectando con Drive..."):
            sheet = conectar_google(SHEET_BASE_NOMBRE)
            if sheet:
                df_drive = pd.DataFrame(sheet.get_all_records())
                df_subido_g = pd.read_csv(archivo_nuevo_g) if archivo_nuevo_g.name.endswith('.csv') else pd.read_excel(archivo_nuevo_g)
                
                if not df_drive.empty:
                    c1, c2 = st.columns(2)
                    id_d = c1.selectbox("Columna ID en Drive:", df_drive.columns, key="sel_id_d")
                    id_s_g = c2.selectbox("Columna ID en archivo nuevo:", df_subido_g.columns, key="sel_id_sg")
                    
                    cols_g = st.multiselect("Columnas a añadir a la nube:", 
                                           [c for c in df_subido_g.columns if c != id_s_g], key="m_cols_g")
                    
                    if st.button("🚀 Actualizar Google Sheets", key="btn_g_final"):
                        if not cols_g:
                            st.warning("Selecciona al menos una columna.")
                        else:
                            with st.spinner("Actualizando hoja..."):
                                resultado_g = realizar_cruce(df_drive, df_subido_g, id_d, id_s_g, cols_g)
                                
                                # Subida de datos
                                datos_lista = [resultado_g.columns.tolist()] + resultado_g.values.tolist()
                                sheet.clear()
                                sheet.update('A1', datos_lista)
                                
                                st.success("✅ Base en Drive actualizada correctamente.")
                                st.balloons()
                                st.dataframe(resultado_g.head(10))
                else:
                    st.error("La base en Drive no tiene datos.")

# --- PESTAÑA 2: UNIÓN LOCAL ---
with tab2:
    st.header("Cruce de archivos locales")
    st.write("Une dos archivos y descarga el resultado sin afectar a Drive.")
    
    col_a, col_b = st.columns(2)
    f_base_l = col_a.file_uploader("Archivo Base (Destino):", type=['xlsx', 'csv'], key="up_l_base")
    f_nuevo_l = col_b.file_uploader("Archivo con nuevos datos:", type=['xlsx', 'csv'], key="up_l_nuevo")
    
    if f_base_l and f_nuevo_l:
        df_l_base = pd.read_csv(f_base_l) if f_base_l.name.endswith('.csv') else pd.read_excel(f_base_l)
        df_l_nuevo = pd.read_csv(f_nuevo_l) if f_nuevo_l.name.endswith('.csv') else pd.read_excel(f_nuevo_l)
        
        c1, c2 = st.columns(2)
        id_l_b = c1.selectbox("ID en Base:", df_l_base.columns, key="sel_id_lb")
        id_l_n = c2.selectbox("ID en Datos Nuevos:", df_l_nuevo.columns, key="sel_id_ln")
        
        cols_l = st.multiselect("Columnas a añadir:", 
                               [c for c in df_l_nuevo.columns if c != id_l_n], key="m_cols_l")
        
        if st.button("🚀 Procesar Unión Local", key="btn_l_final"):
            if not cols_l:
                st.warning("Selecciona al menos una columna.")
            else:
                resultado_l = realizar_cruce(df_l_base, df_l_nuevo, id_l_b, id_l_n, cols_l)
                
                st.success("Cruce realizado. Previsualización:")
                st.dataframe(resultado_l.head(10))
                
                # Preparar descarga
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    resultado_l.to_excel(writer, index=False)
                
                st.download_button(
                    label="📥 Descargar Resultado en Excel",
                    data=output.getvalue(),
                    file_name="union_local_udg.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

st.sidebar.markdown("---")
st.sidebar.caption("© 2026 UDGPlus - Educación Continua")
st.sidebar.markdown("---")
st.sidebar.caption("UDGPlus - Unidad de Educación Continua")
