import streamlit as st
import pandas as pd
from pypdf import PdfWriter
from PIL import Image
import io
import os

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Unión de Datos y Documentos - UdeG", 
    page_icon="📊",
    layout="wide"
)

# --- ESTILOS E IMAGEN INSTITUCIONAL ---
def mostrar_encabezado():
    col1, col2 = st.columns([1, 5])
    
    # Esta lista busca el logo en diferentes lugares posibles
    posibles_rutas = ["assets/logo_u.png", "logo_u.png", "logo_u.png.png"]
    logo_final = None
    
    for ruta in posibles_rutas:
        if os.path.exists(ruta):
            logo_final = ruta
            break

    with col1:
        if logo_final:
            st.image(logo_final, width=150)
        else:
            st.warning("Logo no encontrado")
            
    with col2:
        st.title("Plataforma de Procesamiento de Datos y Documentos")
        st.subheader("Unidad de Educación Continua Virtual y Campus Digital Comunitario UDGPlus")

    # Aviso de Privacidad Integrado
    with st.expander("⚖️ Aviso de Privacidad (UdeG)"):
        st.caption("""
        La Universidad de Guadalajara (en adelante UdeG), con domicilio en Avenida Juárez 976, colonia Centro, 
        código postal 44100, en Guadalajara, Jalisco, hace de su conocimiento que se considerará como información 
        confidencial aquella que se encuentre contemplada en la normativa vigente. Los datos proporcionados serán única 
        y exclusivamente utilizados para los fines que fueron proporcionados.
        
        Esta aplicación procesa los archivos temporalmente en memoria RAM y NO almacena copias en el servidor.
        Consulte el aviso integral en: http://www.transparencia.udg.mx/aviso-confidencialidad-integral
        """)

# --- LÓGICA: UNIÓN TABULAR ---
def seccion_tabular():
    st.header("1️⃣ Unión de Archivos Tabulados")
    st.write("Carga dos archivos para realizar una unión basada en un campo común (Atribute Join).")
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        file_1 = st.file_uploader("Archivo Base (Capa destino)", type=['csv', 'xlsx'])
    with col_b:
        file_2 = st.file_uploader("Archivo a Unir (Capa origen)", type=['csv', 'xlsx'])

    if file_1 and file_2:
        # Carga de datos con detección de formato
        df1 = pd.read_csv(file_1) if file_1.name.endswith('.csv') else pd.read_excel(file_1)
        df2 = pd.read_csv(file_2) if file_2.name.endswith('.csv') else pd.read_excel(file_2)

        st.info(f"Registros detectados: Base ({len(df1)}) | A unir ({len(df2)})")
        
        c1, c2 = st.columns(2)
        key_1 = c1.selectbox("Campo Llave en Base:", df1.columns)
        key_2 = c2.selectbox("Campo Llave en Unión:", df2.columns)
        
        # Selección de columnas (excluyendo la llave para no duplicar)
        available_cols = [c for c in df2.columns if c != key_2]
        cols_to_add = st.multiselect("Selecciona las columnas que deseas agregar:", available_cols)
        
        if st.button("Ejecutar Unión de Atributos"):
            if not cols_to_add:
                st.warning("Por favor selecciona al menos una columna para añadir.")
            else:
                # Lógica de Join
                df2_subset = df2[[key_2] + cols_to_add]
                resultado = pd.merge(df1, df2_subset, left_on=key_1, right_on=key_2, how='left')
                
                st.success("¡Unión completada!")
                st.subheader("Previsualización (primeros 10 registros):")
                st.dataframe(resultado.head(10))
                
                # Preparar descarga
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    resultado.to_excel(writer, index=False)
                
                st.download_button(
                    label="📥 Descargar Resultado en Excel",
                    data=output.getvalue(),
                    file_name="union_resultado_udg.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

# --- LÓGICA: UNIÓN DOCUMENTOS ---
def seccion_documentos():
    st.header("2️⃣ Combinar PDF e Imágenes")
    st.write("Los archivos se combinarán en el orden exacto en que los selecciones.")
    
    uploaded_files = st.file_uploader(
        "Carga archivos (PDF, JPG, PNG)", 
        type=['pdf', 'jpg', 'png', 'jpeg'], 
        accept_multiple_files=True
    )
    
    if uploaded_files:
        nombre_final = st.text_input("Nombre del PDF final:", "documento_unificado_udg.pdf")
        
        if st.button("Generar PDF Combinado"):
            merger = PdfWriter()
            
            with st.spinner("Procesando archivos..."):
                for uploaded_file in uploaded_files:
                    if uploaded_file.type == "application/pdf":
                        merger.append(uploaded_file)
                    else:
                        # Procesamiento de imagen
                        image = Image.open(uploaded_file).convert("RGB")
                        img_pdf = io.BytesIO()
                        image.save(img_pdf, format="PDF")
                        merger.append(img_pdf)
                
                output_pdf = io.BytesIO()
                merger.write(output_pdf)
                
                st.success("¡Documento generado con éxito!")
                st.download_button(
                    label="📥 Descargar PDF Final",
                    data=output_pdf.getvalue(),
                    file_name=nombre_final,
                    mime="application/pdf"
                )

# --- FUNCIÓN PRINCIPAL ---
def main():
    mostrar_encabezado()
    
    st.divider()
    opcion = st.sidebar.radio(
        "Menú de Herramientas", 
        ["Unir Tablas (Join)", "Combinar Documentos"]
    )

    if opcion == "Unir Tablas (Join)":
        seccion_tabular()
    else:
        seccion_documentos()

    # Footer institucional
    st.sidebar.divider()
    st.sidebar.caption("Herramienta desarrollada para uso institucional. © 2024 UdeG.")

if __name__ == "__main__":
    main()
