# Copyright 2023 Google LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import streamlit as st
import pandas as pd
from google.cloud import bigquery
from main import run
from utils.bq import BigQueryInteractor

_CHAR_COUNT_COL_NAME = 'Character Count'
_SHORT_TITLE_COL_NAME = 'Short Title'
_COLUMN_SELECT_HELP = 'Select relevant columns from the feed, from which Shrinkify will generate short titles. Select informative columns, where values vary between entries.'
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
    examples = get_random_rows(st.session_state.selected_dataset,
                               st.session_state.selected_table, st.session_state.selected_columns)
    # Create a DataFrame with the selected columns and add a "Short Title" column
    st.session_state.df = pd.DataFrame(
        examples, columns=st.session_state.selected_columns)
    st.session_state.df[_SHORT_TITLE_COL_NAME] = st.session_state.df.get(
        "name", '')  # Initialize Short Title column


def run_shrinkify():
    st.session_state.run_clicked = True
    examples_df = st.session_state.edited_df
    examples_df.drop('Character Count', axis=1)
    conifg_params = {
        "industry": st.session_state.industry,
        "product_type": st.session_state.product_type,
        "char_limit": st.session_state.char_limit,
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
    if "char_limit" not in st.session_state:
        st.session_state.char_limit = 0

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
    col1, col2, col3 = st.columns(3)
    with col1:
        st.session_state.industry = st.text_input("Industry", value="")

    with col2:
        st.session_state.product_type = st.text_input("Product Type", value="")

    with col3:
        st.session_state.char_limit = st.number_input(
            label=":rainbow[Max Length]", max_value=60, value=30, help="It is recommended to use a slightly lower limit than you require. i.e. if you need a maximum of 30 chars, use a limit of 28")
    # Step 2: Select a dataset
    st.session_state.selected_dataset = st.selectbox(
        "Select a BigQuery Dataset", get_datasets())

    if st.session_state.selected_dataset:
        # Step 3: Select a table from the chosen dataset
        st.session_state.selected_table = st.selectbox(
            "Select a Table from the Dataset", get_tables(st.session_state.selected_dataset))

        if st.session_state.selected_table:
            # Step 4: Select Columns
            st.session_state.selected_columns = st.multiselect("Select Relevant Columns from the Table", get_column_names(
                st.session_state.selected_dataset, st.session_state.selected_table),help=_COLUMN_SELECT_HELP)

            if st.session_state.selected_columns:
                # Step 5: Create Examples
                st.button("Create Examples", on_click=create_examples)

elif not st.session_state.run_clicked:
    st.write(f'Shrinkify has randomly selected 5 entries from your feed.  \n Change their short titles and make sure they are shorter then your selected characters limit of :blue[{st.session_state.char_limit}].  \n Once you are done click the "RUN" button.')
    edited_df = st.data_editor(st.session_state.df, key="examples_table", disabled=(
        st.session_state.selected_columns), use_container_width=True)
    edited_df[_CHAR_COUNT_COL_NAME] = edited_df[_SHORT_TITLE_COL_NAME].apply(
        lambda x: len(x))

    cc_df = edited_df[[_CHAR_COUNT_COL_NAME]]
    st.write(
        f'<div style="display: flex; justify-content: center;">{cc_df.to_html()} </div>',
        unsafe_allow_html=True
    )

    st.session_state.edited_df = edited_df
    st.text("")
    st.button("RUN", on_click=run_shrinkify)

else:
    st.write("Shrinkify Running")
