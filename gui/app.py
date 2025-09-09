import streamlit as st
from streamlit_ketcher import st_ketcher
import json
import pandas as pd
import requests

st.set_page_config(layout = 'wide')


st.header('Property Prediction')
st.divider(width = 'stretch')

col1, col2, col3 = st.columns([2, 3, 1], gap = 'small')
                                   
with col1:
    with st.container(border = True, 
                      key = 'container_1'):
        uploaded_file = st.file_uploader('Choose a CSV file', type=['csv'])
    
    if uploaded_file is not None:
        with st.container(border = True, 
                            key = 'container_2',
                            horizontal = True,
                            gap = 'small'):
        
            molecules_df = pd.read_csv(uploaded_file)
            
            id_column = st.selectbox(
                label = 'Select ID column',
                options = molecules_df.columns,
                index = None
            )
            smiles_column = st.selectbox(
                label = 'Select SMILES column',
                options = molecules_df.columns,
                index = None
            )

            if smiles_column is not None:
                st.write(f'Found {molecules_df[smiles_column].nunique()} unique SMILES.')
        
        if smiles_column is not None and id_column is not None:
            with st.container(border = True, key = 'container_3'):
                with open('./config/model_configs.json') as f:
                    model_configs = json.load(f)
                model_names = [c['name'] for c in model_configs]
                chosen_models = st.multiselect(
                    "Select models",
                    model_names,
                    default = model_names,
                    key = 'multiselect_models'
                    )

                specs_df = pd.DataFrame(model_configs)[['name', 'algorithm', 'r squared']]
                        
                specs_df = (
                    specs_df.style
                        .applymap(lambda v: 'color: red;' if v < 0.4 else 'color: green;', subset=['r squared'])
                        .format({'r squared':'{:,.2f}'})
                )
                with st.expander('Show models specs'):
                    st.dataframe(specs_df, hide_index = True)
            
            if st.button('Predict', use_container_width = True):
                if not chosen_models:
                    st.error('Select at least one model')
                else:
                    payload_rows_df = molecules_df[[id_column, smiles_column]].rename(columns = {id_column: 'id', smiles_column: 'smiles'})
                    payload = {'config': {'models': chosen_models}, 'data': {'rows': payload_rows_df.to_dict(orient = 'records')}}

                    r = requests.post('http://127.0.0.1:8000/predict', json = payload)

                with col2:
                    # change col names back to original
                    # render and show molecules
                    #st.text(r.json())  
                    st.dataframe(pd.DataFrame(r.json())) 

