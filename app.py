import streamlit as st
import pandas as pd
import random
from google.cloud import bigquery
from main import run
from utils.bq import BigQueryInteractor

# Initialize the BigQuery client
client = bigquery.Client()

# Function to fetch all available datasets
@st.cache_data
def get_datasets():
    return st.session_state.bq_client.get_datasets()

# Function to fetch tables within a dataset
@st.cache_data
def get_tables(dataset_id):
    return st.session_state.bq_client.get_tables(dataset_id)

# Function to fetch column names from a table
@st.cache_data
def get_column_names(dataset_id, table_id):
    return st.session_state.bq_client.get_column_names(dataset_id, table_id)

# Function to fetch random rows from the selected table
def get_random_rows(dataset_id, table_id, selected_columns, num_rows=5):
    query = f"SELECT {', '.join(selected_columns)} FROM `{dataset_id}.{table_id}` ORDER BY RAND() LIMIT {num_rows}"
    results = st.session_state.bq_client.run_query(query)
    rows = [list(row.values()) for row in results]
    return rows

def create_examples():
    examples = get_random_rows(st.session_state.selected_dataset, st.session_state.selected_table, st.session_state.selected_columns)
    # Create a DataFrame with the selected columns and add a "Short Title" column
    st.session_state.df = pd.DataFrame(examples, columns=st.session_state.selected_columns)
    st.session_state.df["Short Title"] = st.session_state.df["name"] # Initialize Short Title column

def run_shrinkify():
    st.session_state.run_clicked = True
    examples_df = st.session_state.edited_df
    examples_df.drop('Character Count', axis=1)
    conifg_params = {
        "industry": st.session_state.industry,
        "product_type": st.session_state.product_type,
        "source_dataset": st.session_state.selected_dataset,
        "source_table": st.session_state.selected_table,
        "columns": st.session_state.selected_columns,
        "examples_df": examples_df
    }
    run(conifg_params)


def initialize_session_state():
    if "bq_client" not in st.session_state:
        st.session_state.bq_client = BigQueryInteractor()
    if "industry" not in st.session_state:
        st.session_state.industry = ""
    if "product_type" not in st.session_state:
        st.session_state.product_type = ""
    if "selected_dataset" not in st.session_state:
        st.session_state.selected_dataset = None
    if "selected_table" not in st.session_state:
        st.session_state.selected_table = None
    if "selected_columns" not in st.session_state:
        st.session_state.selected_columns = []
    if "examples" not in st.session_state:
        st.session_state.examples = []
    if "df" not in st.session_state:
        st.session_state.df = None
    if "edited_df" not in st.session_state:
        st.session_state.edited_df = None
    if "run_clicked" not in st.session_state:
        st.session_state.run_clicked = False

st.set_page_config(
    page_title="Shrinkify🤏",
    page_icon="🤏",
    layout="centered",
)

customized_button = st.markdown("""
        <style >
            div.stButton {text-align:center}
    }
        </style>""", unsafe_allow_html=True)

st.header("Shrinkify 🤏")
initialize_session_state()

if st.session_state.df is None:
    
    # Step 1: Select industry and product type
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.industry = st.text_input("Industry", value="")

    with col2:
        st.session_state.product_type = st.text_input("Product Type", value="")
    
    # Step 2: Select a dataset
    st.session_state.selected_dataset = st.selectbox("Select a BigQuery Dataset", get_datasets())

    if st.session_state.selected_dataset:
        # Step 3: Select a table from the chosen dataset
        st.session_state.selected_table = st.selectbox("Select a Table from the Dataset", get_tables(st.session_state.selected_dataset))

        if st.session_state.selected_table:
            # Step 4: Select Columns
            st.session_state.selected_columns = st.multiselect("Select Relevant Columns from the Table", get_column_names(st.session_state.selected_dataset, st.session_state.selected_table))

            if st.session_state.selected_columns:
                # Step 5: Create Examples
                    st.button("Create Examples",on_click=create_examples)
                    
elif not st.session_state.run_clicked:
    edited_df = st.data_editor(st.session_state.df, key="examples_table",disabled=(st.session_state.selected_columns),use_container_width=True)
    edited_df['Character Count'] = edited_df['Short Title'].apply(lambda x: len(x))
    
    cc_df = edited_df[["Character Count"]]
    st.write(
    f'<div style="display: flex; justify-content: center;">{cc_df.to_html()} </div>',
    unsafe_allow_html=True
    )

    st.session_state.edited_df = edited_df
    st.text("")
    st.button("RUN", on_click=run_shrinkify)
        
else:
    st.write("Shrinkify Running")