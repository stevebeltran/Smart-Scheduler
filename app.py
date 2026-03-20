import streamlit as st
import streamlit.components.v1 as components

# 1. Setup the page to be wide to match your 1280px design
st.set_page_config(
    page_title="BRINC DFR · Operator Optimizer",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. Read your HTML file
with open("index.html", "r", encoding="utf-8") as f:
    html_code = f.read()

# 3. Embed the HTML into the Streamlit app
# We use a large height (2000px) to ensure your dashboard doesn't get cut off
components.html(html_code, height=2000, scrolling=True)
