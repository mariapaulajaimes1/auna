import os
import io
import zipfile
import tempfile

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
import SimpleITK as sitk
from skimage.transform import resize
import plotly.graph_objects as go
import random

st.set_page_config(layout="wide", page_title="BrachyCervix")

# Logo
col1, col2 = st.columns([5, 15])
with col1:
    st.image("Banner.png", width=500)

# Estilos
st.markdown("""
<style>
    .giant-title { color: #28aec5; text-align: center; font-size: 72px; margin: 30px 0; font-weight: bold; text-transform: uppercase; letter-spacing: 2px; text-shadow: 2px 2px 4px rgba(0,0,0,0.1); }
    .sub-header { color: #c0d711; font-size: 24px; margin-bottom: 15px; font-weight: bold; }
    .stButton>button { background-color: #28aec5; color: white; border: none; border-radius: 4px; padding: 8px 16px; }
    .stButton>button:hover { background-color: #1c94aa; }
</style>
""", unsafe_allow_html=True)

st.sidebar.markdown('<p class="sub-header">Visualizador de imágenes DICOM</p>', unsafe_allow_html=True)
uploaded_file = st.sidebar.file_uploader("Sube un archivo ZIP con tus archivos DICOM", type="zip")

# Funciones
def find_dicom_series(directory):
    series = []
    for root, _, files in os.walk(directory):
        try:
            ids = sitk.ImageSeriesReader.GetGDCMSeriesIDs(root)
            for sid in ids:
                flist = sitk.ImageSeriesReader.GetGDCMSeriesFileNames(root, sid)
                if flist:
                    series.append((sid, root, flist))
        except:
            pass
    return series

def apply_window_level(image, ww, wc):
    img_f = image.astype(float)
    mn = wc - ww / 2.0
    mx = wc + ww / 2.0
    win = np.clip(img_f, mn, mx)
    return (win - mn) / (mx - mn) if mx != mn else np.zeros_like(img_f)

# Extraer ZIP
dirname = None
if uploaded_file:
    temp_dir = tempfile.mkdtemp()
    with zipfile.ZipFile(io.BytesIO(uploaded_file.read()), 'r') as z:
        z.extractall(temp_dir)
    dirname = temp_dir
    st.sidebar.success("Archivos extraídos correctamente.")

# Cargar serie
img = None
original = None
if dirname:
    with st.spinner('Buscando series DICOM...'):
        series = find_dicom_series(dirname)
    if series:
        opts = [f"Serie {i+1}: {s[0][:10]}... ({len(s[2])} ficheros)" for i, s in enumerate(series)]
        sel = st.sidebar.selectbox("Seleccionar serie DICOM:", opts)
        idx = opts.index(sel)
        _, _, files = series[idx]
        reader = sitk.ImageSeriesReader()
        reader.SetFileNames(files)
        vol = reader.Execute()
        img = sitk.GetArrayViewFromImage(vol)
        original = img.copy()
    else:
        st.sidebar.error("No se encontraron DICOM válidos en el ZIP cargado.")

# Visualización
if img is not None:
    n_ax, n_cor, n_sag = img.shape
    mn, mx = float(img.min()), float(img.max())
    default_ww, default_wc = mx - mn, mn + (mx - mn) / 2

    sync = st.sidebar.checkbox('Sincronizar cortes', value=True)
    if sync:
        corte = st.sidebar.radio('Corte (sincronizado)', ('Axial', 'Coronal', 'Sagital'))
        lims = {'Axial': n_ax - 1, 'Coronal': n_cor - 1, 'Sagital': n_sag - 1}
        mids = {'Axial': n_ax // 2, 'Coronal': n_cor // 2, 'Sagital': n_sag // 2}
        idx_slider = st.sidebar.slider('Índice', 0, lims[corte], mids[corte])
        slice_idx = idx_slider
    else:
        corte = st.sidebar.radio('Selecciona el tipo de corte', ('Axial', 'Coronal', 'Sagital'))
        if corte == 'Axial':
            slice_idx = st.sidebar.slider('Índice Axial', 0, n_ax - 1, n_ax // 2)
        elif corte == 'Coronal':
            slice_idx = st.sidebar.slider('Índice Coronal', 0, n_cor - 1, n_cor // 2)
        else:
            slice_idx = st.sidebar.slider('Índice Sagital', 0, n_sag - 1, n_sag // 2)

    # Opciones de imagen
    show_3d = st.sidebar.checkbox('Mostrar visualización 3D', value=True)
    invert = st.sidebar.checkbox('Invertir colores (Negativo)', value=False)
    window_type = st.sidebar.selectbox('Tipo de ventana', ('Default', 'Abdomen', 'Hueso', 'Pulmón'))
    if window_type == 'Default':
        ww, wc = default_ww, default_wc
    elif window_type == 'Abdomen':
        ww, wc = 400, 40
    elif window_type == 'Hueso':
        ww, wc = 2000, 500
    elif window_type == 'Pulmón':
        ww, wc = 1500, -600
    else:
        ww, wc = default_ww, default_wc

    axial = img[slice_idx, :, :] if corte == 'Axial' else img[n_ax // 2, :, :]
    coronal = img[:, slice_idx, :] if corte == 'Coronal' else img[:, n_cor // 2, :]
    sagital = img[:, :, slice_idx] if corte == 'Sagital' else img[:, :, n_sag // 2]
    cortes = [('Axial', axial), ('Coronal', coronal), ('Sagital', sagital)]

    cols = st.columns(3)
    for col, (name, mat) in zip(cols, cortes):
        with col:
            st.markdown(f"{name}")
            fig, ax = plt.subplots()
            ax.axis('off')
            norm = apply_window_level(mat, ww, wc)
            if invert:
                norm = 1 - norm
            ax.imshow(norm, cmap='gray', origin='lower')
            st.pyplot(fig)

    # 3D
    if show_3d:
        resized = resize(original, (64, 64, 64), anti_aliasing=True)

        if 'points' not in st.session_state:
            st.session_state['points'] = []
        if 'lines' not in st.session_state:
            st.session_state['lines'] = []

        # --- BOTÓN PARA GENERAR AGUJAS ALEATORIAS ---
        if st.button("Generar agujas aleatorias predeterminadas"):
            # Vaciar puntos y líneas previas
            st.session_state['points'] = []
            st.session_state['lines'] = []

            # Agregar puntos según tu lógica
            # x1=32, x2=39
            # y1=32, y2=32
            # z1=z2= aleatorio entre 29 y 36
            z_random_1 = random.randint(29, 36)
            z_random_2 = random.randint(29, 36)
            st.session_state['points'].append((32, 32, z_random_1))
            st.session_state['points'].append((39, 32, z_random_2))

        with st.expander("Agregar punto 3D manualmente"):
            x = st.number_input("X", 0.0, 64.0, 32.0)
            y = st.number_input("Y", 0.0, 64.0, 32.0)
            z = st.number_input("Z", 0.0, 64.0, 32.0)
            if st.button("Agregar Punto"):
                st.session_state['points'].append((x, y, z))

        if len(st.session_state['points']) >= 2:
            st.selectbox("Seleccionar primer punto", options=list(range(len(st.session_state['points']))), key='p1')
            st.selectbox("Seleccionar segundo punto", options=list(range(len(st.session_state['points']))), key='p2')
            if st.button("Agregar línea"):
                st.session_state['lines'].append((
                    st.session_state['points'][st.session_state['p1']],
                    st.session_state['points'][st.session_state['p2']]
                ))

        xg, yg, zg = np.mgrid[0:64, 0:64, 0:64]
        fig3d = go.Figure(data=[go.Volume(
            x=xg.flatten(), y=yg.flatten(), z=zg.flatten(),
            value=resized.flatten(),
            opacity=0.1, surface_count=15, colorscale='Gray')
        ])

        for pt in st.session_state['points']:
            fig3d.add_trace(go.Scatter3d(
                x=[pt[0]], y=[pt[1]], z=[pt[2]],
                mode='markers',
                marker=dict(size=5, color='red')
            ))
        for a, b in st.session_state['lines']:
            fig3d.add_trace(go.Scatter3d(
                x=[a[0], b[0]], y=[a[1], b[1]], z=[a[2], b[2]],
                mode='lines',
                line=dict(color='blue')
            ))

        fig3d.update_layout(margin=dict(l=0, r=0, b=0, t=0))
        st.subheader('Vista 3D')
        st.plotly_chart(fig3d, use_container_width=True)

# Footer
st.markdown('<p class="giant-title">BrachyCervix</p>', unsafe_allow_html=True)
st.markdown("""
<hr>
<div style="text-align:center;color:#28aec5;font-size:50px;">
    BrachyCervix -
    Semiautomátización y visor para procesos de braquiterapia enfocados en el Cervix
</div>
<div style="text-align:center;color:#28aec5;font-size:20px;">
    Proyecto asignatura medialab 3
</div>
<div style="text-align:center;color:#28aec5;font-size:20px;">
    Universidad EAFIT 
</div>
<div style="text-align:center;color:#28aec5;font-size:20px;">
    Contacto: javier.trujillo@eafit.edu.co
</div>
<hr>
""", unsafe_allow_html=True)
