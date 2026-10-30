import streamlit as st

from app.agent_workspace import render_agent_workspace


st.set_page_config(
    page_title="Agent Workspace",
    page_icon="🐾",
    layout="wide",
)

render_agent_workspace()