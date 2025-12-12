import json
import requests
import pandas as pd
import streamlit as st
from utils import smiles_to_svg, svg_to_datauri

# init session state for prediction result and error
if 'results_df' not in st.session_state:
    st.session_state.results_df = None

if 'request_error' not in st.session_state:
    st.session_state.request_error = None

st.set_page_config(layout = 'wide')
st.header('Property Prediction')
st.divider(width = 'stretch')

with st.container(border = False, key = 'layout_container'):
    col1, col2 = st.columns([2, 6], gap = 'small')
                                    
    with col1:
        with st.container(border = True, 
                        key = 'container_1'):
            uploaded_file = st.file_uploader('Choose a CSV file', type=['csv'])

        with st.container(border = True, 
                            key = 'container_2',
                            #horizontal = True,
                            gap = 'small'):

            if not uploaded_file:
                st.selectbox(label = 'Select ID column', options = [''], disabled = True) 
                st.selectbox(label = 'Select SMILES column', options = [''], disabled = True)
                smiles_column = None
                id_column = None

            else:
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

                # if smiles_column is not None:
                #     st.success(f'Found {molecules_df[smiles_column].nunique()} unique SMILES.')
            
        with st.container(border = True, key = 'container_3'):
            
            if not uploaded_file or not smiles_column or not id_column:
                st.multiselect('Select models', options = [''], disabled = True)
                st.popover('Show models specs', width = 'stretch', disabled = True)
            else:
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
                with st.popover('Show models specs', width = 'stretch'):
                    st.dataframe(specs_df, hide_index = True)
        
        with st.container(border = False, key = 'button_container'):

            if not uploaded_file or not smiles_column or not id_column or not chosen_models:
                st.button('Predict', use_container_width = True, key = 'predict_button_disabled', disabled = True)   
            else:
                if st.button('Predict', use_container_width = True, key = 'predict_button_enabled'):
                        payload_rows_df = molecules_df[[id_column, smiles_column]].rename(columns = {id_column: 'id', smiles_column: 'smiles'})
                        payload = {'config': {'models': chosen_models}, 'data': {'rows': payload_rows_df.to_dict(orient = 'records')}}

                        r = requests.post('http://127.0.0.1:8000/predict', json = payload)

                        if r.ok:
                            st.session_state.results_df = pd.DataFrame(r.json())
                            st.session_state.request_error = None
                        else:
                            st.session_state.results_df = None
                            st.session_state.request_error = f'Request failed with status code {r.status_code}'

    with col2:
    
        if st.session_state.results_df is None and st.session_state.request_error is None: 
            st.markdown('<div style="align-text: center; align-items: center; justify-content: center; display: flex; height: 520px;"> Load compounds and define settings to start predictions. </div>', unsafe_allow_html = True)
        elif st.session_state.request_error is not None:
            st.error(st.session_state.request_error)
        else:
            with st.container(border = False, height = 'stretch', key = 'results_container'):
                col2_1, col2_2 = st.columns([3, 1], gap = 'small')
                results_df = st.session_state.results_df.copy()
                results_df['svg_text'] = results_df['smiles'].apply(smiles_to_svg)
                results_df['svg_datauri'] = results_df['svg_text'].apply(svg_to_datauri)
                results_df.drop(columns = ['svg_text'], inplace = True)
               
                # need to join predictions with data in original csv!

                with col2_2:
                    with st.container(border = True, height = 'stretch', key = 'filters_container'):
                        min_value = results_df['MDR1_ER'].min()
                        max_value = results_df['MDR1_ER'].max()
                        value_range = st.slider('label', min_value = min_value, max_value = max_value, value = (min_value, max_value), key = 'slider_key')

                with col2_1:
                    with st.container(border = True, height = 'stretch', key = 'df_container'):
                        # need to change col names back to original
                        
                        # filter data
                        results_df = results_df[results_df['MDR1_ER'].between(*value_range)]



                        st.data_editor(
                                        results_df,
                                        column_config = {'svg_datauri': st.column_config.ImageColumn(width = 'large')},
                                        row_height = 110,
                                        height = 580, 
                                        hide_index = True
                                        )

