import streamlit as st
import sys
import os
import copy
from PIL import Image

# not necessary if we install it with pip install
sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))
from fairiskdata import FAIRiskDataset
from docs.streamlit.timeseries_streamlit import render_timeseries
from docs.streamlit.params_streamlit import render_params

st.set_page_config(page_title='fairiskdata', layout="wide")

st.sidebar.markdown("<h1 style='text-align: center;'>FAIRisk</h1>", unsafe_allow_html=True)
resources_dir = f'{os.path.dirname(__file__)}/resources'
logo_col1, logo_col2 = st.sidebar.beta_columns(2)
with logo_col1:
  st.image(Image.open(f'{resources_dir}/fhp_t_s.png'), width=100)
with logo_col2:
  st.image(Image.open(f'{resources_dir}/eosc_logo.png'), width=100)

st.sidebar.subheader('Navigation')
page = st.sidebar.radio('', ['Parameters', 'Timeseries'])

@st.cache(allow_output_mutation=True)
def load_data():
    return FAIRiskDataset.load()

dataset = load_data()
dataset = copy.deepcopy(dataset)

if page == 'Parameters':
    render_params(dataset)
else:
    render_timeseries(dataset)
