import streamlit as st
import nibabel as nib
import numpy as np
import plotly.graph_objs as go
import tempfile
import os
import random

st.set_page_config(layout="wide")

# --- PARTE INTRODUCTORIA ---
st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/3/38/Streamlit_logo.svg/256px-Streamlit_logo.svg.png", width=100)
st.title("Visualizador 3D de Imágenes Médicas con Trayectorias de Agujas")
st.markdown("**Integrantes:** Juan Pérez, María López, Ana Gómez")
st.markdown("---")

# --- Lógica carga archivo ---
if 'uploaded_file' not in st.session_state:
    st.session_state['uploaded_file'] = None

uploaded_file = st.file_uploader("Sube una imagen en formato .nii o .nii.gz", type=["nii", "nii.gz"])

if uploaded_file is not None:
    st.session_state['uploaded_file'] = uploaded_file

if st.session_state['uploaded_file'] is not None:
    uploaded_file = st.session_state['uploaded_file']

    # Guardar en archivo temporal
    with tempfile.NamedTemporaryFile(delete=False, suffix='.nii.gz') as tmp_file:
        tmp_file.write(uploaded_file.read())
        tmp_filepath = tmp_file.name

    # Cargar imagen con nibabel
    img = nib.load(tmp_filepath)
    data = img.get_fdata()

    # Eliminar archivo temporal
    os.remove(tmp_filepath)

    midpoint = [s // 2 for s in data.shape]

    # Mostrar cortes
    col1, col2, col3 = st.columns(3)

    with col1:
        axial_index = st.slider("Corte Axial", 0, data.shape[2] - 1, midpoint[2])
        st.image(data[:, :, axial_index], caption=f"Corte Axial - Índice {axial_index}", use_column_width=True)

    with col2:
        coronal_index = st.slider("Corte Coronal", 0, data.shape[1] - 1, midpoint[1])
        st.image(data[:, coronal_index, :], caption=f"Corte Coronal - Índice {coronal_index}", use_column_width=True)

    with col3:
        sagittal_index = st.slider("Corte Sagital", 0, data.shape[0] - 1, midpoint[0])
        st.image(data[sagittal_index, :, :], caption=f"Corte Sagital - Índice {sagittal_index}", use_column_width=True)

    # Aquí continúa el resto de tu código para agujas, etc.
else:
    st.info("Por favor, sube un archivo NIfTI (.nii o .nii.gz) para visualizar.")
