"""
frontend/pages/settings.py
— stub, to be built next
"""
import streamlit as st
from components.layout import render_layout

def render() -> None:
    render_layout(
        active_page="settings",
        page_content_html='<div style="padding:40px;color:var(--text-p);font-size:18px;font-weight:600">Settings page — coming soon</div>',
        height=900,
    )