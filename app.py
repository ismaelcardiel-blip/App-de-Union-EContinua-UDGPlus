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

def realizar_cruce_inteligente(df_base, df_nuevo, id_base, id_nuevo, columnas_a_cruzar):
    """
    Une los datos y, si la columna ya existe en la base, 
    llena los huecos en lugar de crear una columna duplicada.
    """
    # 1. Aseguramos que los IDs sean strings para evitar fallos de coincidencia
    df_base[id_base] = df_base[id_base].astype(str)
    df_nuevo[id_nuevo] = df_nuevo[id_nuevo].astype(str)

    # 2. Hacemos el merge temporal
    temp_merge = pd.merge(df_base, df_nuevo[[id_nuevo] + columnas_a_cruzar], 
                          left_on=id_base, right_on=id_nuevo, how='left', suffixes=('', '_NUEVO'))

    # 3. Lógica de "rellenado": Si la columna ya existía, pasamos los datos del merge a la original
    for col in columnas_a_cruzar:
        col_nueva = f"{col}_NUEVO"
        if col_nueva in temp_merge.columns:
            # Rellenamos los vacíos de la columna original con los datos de la columna nueva
            # Si la columna original no existía, esto simplemente la crea correctamente
            if col in df_base.columns:
                # Convertimos a string y reemplazamos vacíos reales
                temp_merge[col] = temp_merge[col].astype(str).replace(['nan', 'NaN', 'None', '', '<NA>'], pd.NA)
                temp_merge[col] = temp_merge[col].fillna(temp_merge[col_nueva])
                temp_merge = temp_merge.drop(columns=[col_nueva])
    
    # Limpiamos columna de ID duplicada si existe
    if id_base != id_nuevo and id_nuevo in temp_merge.columns:
        temp_merge = temp_merge.drop(columns=[id_nuevo])

    return temp_merge.astype(str).replace(['nan', 'NaN', 'None', '<NA>'], '')

# --- INTERFAZ ---
st.title("📊 Plataforma de Datos UDGPlus")
st.subheader("Unidad de Educación Continua Virtual")
st.markdown("---")

tab1, tab2 = st.tabs(["🔗 Google Sheets Bridge", "💻 Unión Local (Excel/CSV)"])

# --- PESTAÑA 1: GOOGLE DRIVE ---
with tab1:
    st.header("Sincronización con Google Drive")
    st.info(f"Base vinculada: **{SHEET_BASE_NOMBRE}**")
    
    archivo_nuevo_g = st.file_uploader("Subir datos nuevos:", type=['xlsx', 'csv'], key="up_g_v3")
    
    if archivo_nuevo_g:
        with st.spinner("Conectando con Drive..."):
            sheet = conectar_google(SHEET_BASE_NOMBRE)
            if sheet:
                df_drive = pd.DataFrame(sheet.get_all_records())
                df_subido_g = pd.read_csv(archivo_nuevo_g) if archivo_nuevo_g.name.endswith('.csv') else pd.read_excel(archivo_nuevo_g)
                
                if not df_drive.empty:
                    c1, c2 = st.columns(2)
                    id_d = c1.selectbox("Columna ID en Drive:", df_drive.columns, key="id_d_v3")
                    id_s_g = c2.selectbox("Columna ID en archivo nuevo:", df_subido_g.columns, key="id_s_v3")
                    
                    cols_g = st.multiselect("Columnas a actualizar/añadir:", 
                                           [c for c in df_subido_g.columns if c != id_s_g], key="cols_g_v3")
                    
                    if st.button("🚀 Actualizar Google Sheets", key="btn_g_v3"):
                        if not cols_g:
                            st.warning("Selecciona columnas.")
                        else:
                            with st.spinner("Actualizando datos..."):
                                resultado_g = realizar_cruce_inteligente(df_drive, df_subido_g, id_d, id_s_g, cols_g)
                                
                                datos_lista = [resultado_g.columns.tolist()] + resultado_g.values.tolist()
                                sheet.clear()
                                sheet.update('A1', datos_lista)
                                
                                st.success("✅ Base en Drive actualizada (datos insertados en sus columnas correspondientes).")
                                st.balloons()
                                st.dataframe(resultado_g.head(10))

# --- PESTAÑA 2: UNIÓN LOCAL ---
with tab2:
    st.header("Cruce de archivos locales")
    col_a, col_b = st.columns(2)
    f_base_l = col_a.file_uploader("Archivo Base:", type=['xlsx', 'csv'], key="up_l_b_v3")
    f_nuevo_l = col_b.file_uploader("Datos Nuevos:", type=['xlsx', 'csv'], key="up_l_n_v3")
    
    if f_base_l and f_nuevo_l:
        df_l_base = pd.read_csv(f_base_l) if f_base_l.name.endswith('.csv') else pd.read_excel(f_base_l)
        df_l_nuevo = pd.read_csv(f_nuevo_l) if f_nuevo_l.name.endswith('.csv') else pd.read_excel(f_nuevo_l)
        
        c1, c2 = st.columns(2)
        id_l_b = c1.selectbox("ID Base:", df_l_base.columns, key="id_lb_v3")
        id_l_n = c2.selectbox("ID Nuevo:", df_l_nuevo.columns, key="id_ln_v3")
        cols_l = st.multiselect("Columnas a cruzar:", [c for c in df_l_nuevo.columns if c != id_l_n], key="cols_l_v3")
        
        if st.button("🚀 Procesar Unión Local", key="btn_l_v3"):
            resultado_l = realizar_cruce_inteligente(df_l_base, df_l_nuevo, id_l_b, id_l_n, cols_l)
            st.dataframe(resultado_l.head(10))
            
            output = io.BytesIO()
            with pd.ExcelWriter(output) as writer: resultado_l.to_excel(writer, index=False)
            st.download_button("📥 Descargar Excel", output.getvalue(), "resultado_udg.xlsx")
st.sidebar.markdown("---")
st.sidebar.caption("UDGPlus - Unidad de Educación Continua")
