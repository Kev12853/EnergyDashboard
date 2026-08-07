import streamlit as st
from streamlit_autorefresh import st_autorefresh

st.title("Test")
st_autorefresh(interval=1000)