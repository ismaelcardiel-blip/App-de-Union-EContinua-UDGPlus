import streamlit as st
import pandas as pd
from pypdf import PdfWriter
from PIL import Image
import io

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Herramienta de Unión Institucional", layout="wide")

# --- ESTILOS E IMAGEN INSTITUCIONAL ---
def mostrar_encabezado():
    col1, col2 = st.columns([1, 4])
    with col1:
        # Reemplazar con 'assets/logo.png' localmente
        st.image("https://via.placeholder.com/150x150?text=Logo+U", width=120)
    with col2:
        st.title("Plataforma de Procesamiento de Documentos")
        st.info("Aviso de Privacidad: Los archivos se procesan en memoria y no se almacenan permanentemente.")

# --- LÓGICA: UNIÓN TABULAR ---
def seccion_tabular():
    st.header("1️⃣ Unión de Archivos Tabulados (Join)")
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        file_1 = st.file_uploader("Cargar Archivo Base (Excel/CSV)", type=['csv', 'xlsx'])
    with col_b:
        file_2 = st.file_uploader("Cargar Archivo a Unir", type=['csv', 'xlsx'])

    if file_1 and file_2:
        # Carga de datos
        df1 = pd.read_csv(file_1) if file_1.name.endswith('.csv') else pd.read_excel(file_1)
        df2 = pd.read_csv(file_2) if file_2.name.endswith('.csv') else pd.read_excel(file_2)

        st.success("Archivos cargados correctamente.")
        
        c1, c2 = st.columns(2)
        key_1 = c1.selectbox("Columna Llave (Base)", df1.columns)
        key_2 = c2.selectbox("Columna Llave (A unir)", df2.columns)
        
        cols_to_add = st.multiselect("Columnas a añadir del segundo archivo", [c for c in df2.columns if c != key_2])
        
        if st.button("Ejecutar Join"):
            # Selección de columnas necesarias + la llave
            df2_subset = df2[[key_2] + cols_to_add]
            
            # Operación similar a QGIS (Left Join)
            resultado = pd.merge(df1, df2_subset, left_on=key_1, right_on=key_2, how='left')
            
            st.subheader("Previsualización del resultado:")
            st.dataframe(resultado.head(10))
            
            # Descarga
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                resultado.to_excel(writer, index=False)
            
            st.download_button(
                label="📥 Descargar Resultado (Excel)",
                data=output.getvalue(),
                file_name="union_tablas.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

# --- LÓGICA: UNIÓN DOCUMENTOS ---
def seccion_documentos():
    st.header("2️⃣ Unión de Documentos (PDF / Imágenes)")
    uploaded_files = st.file_uploader("Carga múltiples archivos", type=['pdf', 'jpg', 'png', 'jpeg'], accept_multiple_files=True)
    
    if uploaded_files:
        nombre_final = st.text_input("Nombre del archivo final", "documento_final.pdf")
        
        if st.button("Combinar Documentos"):
            merger = PdfWriter()
            
            for uploaded_file in uploaded_files:
                if uploaded_file.type == "application/pdf":
                    merger.append(uploaded_file)
                else:
                    # Convertir imagen a PDF
                    image = Image.open(uploaded_file).convert("RGB")
                    img_pdf = io.BytesIO()
                    image.save(img_pdf, format="PDF")
                    merger.append(img_pdf)
            
            output_pdf = io.BytesIO()
            merger.write(output_pdf)
            
            st.success("¡Documentos combinados con éxito!")
            st.download_button(
                label="📥 Descargar PDF Final",
                data=output_pdf.getvalue(),
                file_name=nombre_final,
                mime="application/pdf"
            )

# --- MAIN ---
def main():
    mostrar_encabezado()
    
    opcion = st.radio("¿Qué deseas unir?", ["Archivos Tabulados", "Documentos"], horizontal=True)
    st.divider()

    if opcion == "Archivos Tabulados":
        seccion_tabular()
    else:
        seccion_documentos()

if __name__ == "__main__":
    main()
