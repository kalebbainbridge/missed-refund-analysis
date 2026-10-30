import streamlit as st

from app.manager_workspace import render_manager_workspace


st.set_page_config(
    page_title="Manager and Senior Workspace",
    page_icon="🐾",
    layout="wide",
)

render_manager_workspace()
