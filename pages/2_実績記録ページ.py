import streamlit as st
import base64
import io
import os
import re
import requests
from PIL import Image
from datetime import datetime
from openai import OpenAI

import auth_utils # Import Firebase authentication


# Google Apps Script (GAS) and Google Drive information (GAS for legacy spreadsheet, will be removed later if not needed)
GAS_URL = "https://script.google.com/macros/s/AKfycby_uD6Jtb9GT0-atbyPKOPc8uyVKodwYVIQ2Tpe-_E8uTOPiir0Ce1NAPZDEOlCUxN4/exec" # Update this URL to your latest GAS deployment URL


# Helper function to sanitize values
def sanitize(value):
    """Replaces None or specific strings with 'エラー' (Error)"""
    if value is None or value == "取得できず":
        return "エラー"
    return value


# Streamlit UI configuration
st.set_page_config(layout="wide", page_title="バナスコAI")

# --- Logo Display ---
logo_path = "banasuko_logo_icon.png"

try:
    logo_image = Image.open(logo_path)
    st.sidebar.image(logo_image, use_container_width=True) # Display logo in sidebar, adjusting to column width
except FileNotFoundError:
    st.sidebar.error(f"ロゴ画像 '{logo_path}' が見つかりません。ファイルが正しく配置されているか確認してください。")

# --- Login Check ---
# This is crucial! Code below this line will only execute if the user is logged in.
auth_utils.check_login()

# --- OpenAI Client Initialization ---
# Initialize OpenAI client after login check, when OpenAI API key is available from environment variables
openai_api_key = os.getenv("OPENAI_API_KEY")
if openai_api_key:
    client = OpenAI(api_key=openai_api_key)
else:
    # For demo purposes without API key
    client = None
    st.warning("デモモード - OpenAI APIが設定されていません")


# --- Ultimate Professional CSS Theme ---
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@300;400;500;600;700&display=swap');
    
    /* Professional dark gradient background */
    .stApp {
        background: linear-gradient(135deg, #0f0f1a 0%, #1a1c29 15%, #2d3748 35%, #1a202c 50%, #2d3748 65%, #4a5568 85%, #2d3748 100%) !important;
        background-attachment: fixed;
        background-size: 400% 400%;
        animation: background-flow 15s ease-in-out infinite;
    }
    
    @keyframes background-flow {
        0%, 100% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
    }
    
    body {
        background: transparent !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    /* Professional main container with glassmorphism */
    .main .block-container {
        background: rgba(26, 32, 44, 0.4) !important;
        backdrop-filter: blur(60px) !important;
        border: 2px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 32px !important;
        box-shadow: 
            0 50px 100px -20px rgba(0, 0, 0, 0.6),
            0 0 0 1px rgba(255, 255, 255, 0.05),
            inset 0 2px 0 rgba(255, 255, 255, 0.15) !important;
        padding: 5rem 4rem !important;
        position: relative !important;
        margin: 2rem auto !important;
        max-width: 1400px !important;
        min-height: 95vh !important;
    }
    
    .main .block-container::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(135deg, 
            rgba(56, 189, 248, 0.04) 0%, 
            rgba(147, 51, 234, 0.04) 25%, 
            rgba(59, 130, 246, 0.04) 50%, 
            rgba(168, 85, 247, 0.04) 75%, 
            rgba(56, 189, 248, 0.04) 100%);
        border-radius: 32px;
        pointer-events: none;
        z-index: -1;
        animation: container-glow 8s ease-in-out infinite alternate;
    }
    
    @keyframes container-glow {
        from { opacity: 0.3; }
        to { opacity: 0.7; }
    }

    /* Professional sidebar */
    .stSidebar {
        background: linear-gradient(180deg, rgba(15, 15, 26, 0.98) 0%, rgba(26, 32, 44, 0.98) 100%) !important;
        backdrop-filter: blur(40px) !important;
        border-right: 2px solid rgba(255, 255, 255, 0.1) !important;
        box-shadow: 8px 0 50px rgba(0, 0, 0, 0.5) !important;
    }
    
    .stSidebar > div:first-child {
        background: transparent !important;
    }
    
    /* Ultimate gradient button styling */
    .stButton > button {
        background: linear-gradient(135deg, #38bdf8 0%, #a855f7 50%, #06d6a0 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 60px !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 700 !important;
        font-size: 1.1rem !important;
        padding: 1.25rem 3rem !important;
        letter-spacing: 0.05em !important;
        box-shadow: 
            0 15px 35px rgba(56, 189, 248, 0.4),
            0 8px 20px rgba(168, 85, 247, 0.3),
            0 0 60px rgba(6, 214, 160,
