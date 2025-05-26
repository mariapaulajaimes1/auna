import streamlit as st
import nibabel as nib
import numpy as np
import plotly.graph_objs as go
import tempfile
import os
import random

st.set_page_config(layout="wide")
st.title("Visualizador 3D de Imágenes Médicas con Trayectorias de Agujas")

st.markdown("""
<style>
/* Oculta los círculos de los radio buttons */
div[role="radiogroup"] > div > label > div:first-child {
    display: none !important;
}
/* Opcional: mejora el padding y apariencia */
div[role="radiogroup"] > div > label {
    padding-left: 0.5rem !important;
    font-weight: 500;
}
</style>
""", unsafe_allow_html=True)

# Inicializar estados
if 'lines' not in st.session_state:
    st.session_state['lines'] = []
if 'points' not in st.session_state:
    st.session_state['points'] = []

# Subir archivo y guardar en sesión para persistencia
uploaded_file = st.file_uploader("Sube una imagen en formato .nii o .nii.gz", type=["nii", "nii.gz"])

if uploaded_file is not None:
    st.session_state['uploaded_file'] = uploaded_file

if 'uploaded_file' in st.session_state:
    uploaded_file = st.session_state['uploaded_file']

    # Crear archivo temporal para nibabel
    with tempfile.NamedTemporaryFile(delete=False, suffix='.nii.gz') as tmp_file:
        tmp_file.write(uploaded_file.read())
        tmp_filepath = tmp_file.name

    img = nib.load(tmp_filepath)
    data = img.get_fdata()

    # Limpieza del archivo temporal después de cargar la imagen
    os.remove(tmp_filepath)

    midpoint = [s // 2 for s in data.shape]

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

    st.markdown("---")
    st.subheader("Visualización 3D de Agujas")

    fig = go.Figure()
    for line in st.session_state['lines']:
        x = [line[0][0], line[1][0]]
        y = [line[0][1], line[1][1]]
        z = [line[0][2], line[1][2]]
        fig.add_trace(go.Scatter3d(x=x, y=y, z=z, mode='lines+markers'))

    fig.update_layout(scene=dict(xaxis_title='X', yaxis_title='Y', zaxis_title='Z'), width=800, height=600)
    st.plotly_chart(fig)

    st.markdown("---")
    st.subheader("Gestión de Agujas")

    if len(st.session_state['points']) >= 2:
        st.selectbox("Seleccionar primer punto", st.session_state['points'], key='start_point')
        st.selectbox("Seleccionar segundo punto", st.session_state['points'], key='end_point')

        if st.button("Agregar línea"):
            st.session_state['lines'].append((st.session_state['start_point'], st.session_state['end_point']))

    colx1, colx2 = st.columns(2)
    with colx1:
        x = st.number_input("X", min_value=0, max_value=data.shape[0] - 1, value=midpoint[0])
        y = st.number_input("Y", min_value=0, max_value=data.shape[1] - 1, value=midpoint[1])
        z = st.number_input("Z", min_value=0, max_value=data.shape[2] - 1, value=midpoint[2])
        if st.button("Agregar punto"):
            st.session_state['points'].append((x, y, z))
    with colx2:
        if st.button("Generar agujas aleatorias"):
            for _ in range(3):
                z1 = random.randint(29, 36)
                z2 = random.randint(29, 36)
                punto_a = (32, 32, z1)
                punto_b = (39, 32, z2)
                st.session_state['points'].extend([punto_a, punto_b])
                st.session_state['lines'].append((punto_a, punto_b))
            st.success("Agujas generadas correctamente")

    if st.button("Limpiar todo"):
        st.session_state['points'] = []
        st.session_state['lines'] = []
