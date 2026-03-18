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
        st.error(f"Error de conexión: {e}")
        return None

# --- INTERFAZ ---
st.title("📊 Plataforma de Datos Programa de Educación Continua Virtual ")
st.subheader("UDGPlus")
st.markdown("---")

tab1, tab2 = st.tabs(["🔗 Google Sheets Bridge (Directo)", "💻 Unión Local (Descarga Excel)"])

# --- PESTAÑA 1: GOOGLE DRIVE (Actualización Quirúrgica) ---
with tab1:
    st.header("Sincronización Inteligente con Drive")
    st.info(f"Base vinculada: **{SHEET_BASE_NOMBRE}**")
    st.caption("Esta versión respeta tus fórmulas y formatos originales.")
    
    archivo_nuevo_g = st.file_uploader("Subir datos nuevos:", type=['xlsx', 'csv'], key="up_g_v4")
    
    if archivo_nuevo_g:
        with st.spinner("Conectando con Drive..."):
            sheet = conectar_google(SHEET_BASE_NOMBRE)
            if sheet:
                # 1. Obtener encabezados reales de la fila 1 para mapear posiciones
                encabezados_drive = sheet.row_values(1)
                # 2. Obtener datos actuales
                datos_drive = sheet.get_all_records()
                df_drive = pd.DataFrame(datos_drive)
                
                # Leer archivo subido
                df_subido_g = pd.read_csv(archivo_nuevo_g) if archivo_nuevo_g.name.endswith('.csv') else pd.read_excel(archivo_nuevo_g)
                
                if not df_drive.empty:
                    c1, c2 = st.columns(2)
                    id_d = c1.selectbox("Columna ID en Drive (Común):", df_drive.columns, key="id_d_v4")
                    id_s_g = c2.selectbox("Columna ID en archivo nuevo:", df_subido_g.columns, key="id_s_v4")
                    
                    cols_g = st.multiselect("Selecciona columnas para ACTUALIZAR en Drive:", 
                                           [c for c in df_subido_g.columns if c != id_s_g], key="cols_g_v4")
                    
                    if st.button("🚀 Aplicar Cambios en Drive", key="btn_g_v4"):
                        if not cols_g:
                            st.warning("Selecciona al menos una columna.")
                        else:
                            with st.spinner("Actualizando columnas específicas..."):
                                # Preparamos un mapeo rápido del archivo nuevo {ID: {col1: val, col2: val}}
                                df_subido_g[id_s_g] = df_subido_g[id_s_g].astype(str)
                                data_map = df_subido_g.set_index(id_s_g)[cols_g].to_dict('index')
                                
                                # Lista de IDs en el orden actual de Drive
                                ids_en_drive = df_drive[id_d].astype(str).tolist()

                                # Por cada columna que el usuario quiere actualizar
                                for col_nombre in cols_g:
                                    if col_nombre in encabezados_drive:
                                        # A. Encontrar la letra de la columna en Drive
                                        col_idx = encabezados_drive.index(col_nombre) + 1
                                        letra_col = gspread.utils.rowcol_to_a1(1, col_idx).replace('1', '')
                                        
                                        # B. Crear la lista de valores nuevos manteniendo el orden de Drive
                                        nuevos_valores = []
                                        for id_actual in ids_en_drive:
                                            if id_actual in data_map:
                                                valor = data_map[id_actual].get(col_nombre, "")
                                                nuevos_valores.append([valor])
                                            else:
                                                nuevos_valores.append([""]) # Si no hay match, queda vacío o podrías poner un valor x defecto

                                        # C. Definir el rango (desde fila 2 hasta el final)
                                        rango = f"{letra_col}2:{letra_col}{len(nuevos_valores) + 1}"
                                        
                                        # D. Actualizar solo esa columna
                                        # USER_ENTERED hace que Google reconozca números como números y fórmulas como fórmulas
                                        sheet.update(rango, nuevos_valores, value_input_option='USER_ENTERED')
                                
                                st.success(f"✅ Se han actualizado las columnas: {', '.join(cols_g)}. Tus fórmulas y el resto de la tabla permanecen intactos.")
                                st.balloons()
                else:
                    st.error("La base en Drive parece estar vacía.")

# --- PESTAÑA 2: UNIÓN LOCAL ---
with tab2:
    st.header("Cruce de archivos locales")
    st.write("Ideal para uniones rápidas sin tocar la nube.")
    col_a, col_b = st.columns(2)
    f_base_l = col_a.file_uploader("Archivo Base:", type=['xlsx', 'csv'], key="up_l_b_v4")
    f_nuevo_l = col_b.file_uploader("Datos Nuevos:", type=['xlsx', 'csv'], key="up_l_n_v4")
    
    if f_base_l and f_nuevo_l:
        df_l_base = pd.read_csv(f_base_l) if f_base_l.name.endswith('.csv') else pd.read_excel(f_base_l)
        df_l_nuevo = pd.read_csv(f_nuevo_l) if f_nuevo_l.name.endswith('.csv') else pd.read_excel(f_nuevo_l)
        
        c1, c2 = st.columns(2)
        id_l_b = c1.selectbox("ID Base:", df_l_base.columns, key="id_lb_v4")
        id_l_n = c2.selectbox("ID Nuevo:", df_l_nuevo.columns, key="id_ln_v4")
        cols_l = st.multiselect("Columnas a añadir:", [c for c in df_l_nuevo.columns if c != id_l_n], key="cols_l_v4")
        
        if st.button("🚀 Procesar y Descargar", key="btn_l_v4"):
            # Unión clásica
            res_l = pd.merge(df_l_base, df_l_nuevo[[id_l_n] + cols_l], left_on=id_l_b, right_on=id_l_n, how='left')
            if id_l_b != id_l_n: res_l = res_l.drop(columns=[id_l_n])
            
            st.dataframe(res_l.head(10))
            output = io.BytesIO()
            with pd.ExcelWriter(output) as writer: res_l.to_excel(writer, index=False)
            st.download_button("📥 Descargar Resultado", output.getvalue(), "cruce_local.xlsx")

st.sidebar.markdown("---")
st.sidebar.caption("UDGPlus - Unidad de Educación Continua")
