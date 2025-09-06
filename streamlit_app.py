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
            0 0 60px rgba(6, 214, 160, 0.2),
            inset 0 2px 0 rgba(255, 255, 255, 0.3) !important;
        transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1) !important;
        position: relative !important;
        overflow: hidden !important;
        backdrop-filter: blur(20px) !important;
        width: 100% !important;
        text-transform: uppercase !important;
        transform: perspective(1000px) translateZ(0);
    }
    
    .stButton > button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent);
        transition: left 0.8s;
        z-index: 1;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #0ea5e9 0%, #9333ea 50%, #059669 100%) !important;
        box-shadow: 
            0 25px 50px rgba(56, 189, 248, 0.6),
            0 15px 35px rgba(168, 85, 247, 0.5),
            0 0 100px rgba(6, 214, 160, 0.4),
            inset 0 2px 0 rgba(255, 255, 255, 0.4) !important;
        transform: translateY(-5px) scale(1.03) perspective(1000px) translateZ(20px) !important;
    }
    
    .stButton > button:active {
        transform: translateY(-2px) scale(1.01) !important;
        box-shadow: 
            0 15px 30px rgba(56, 189, 248, 0.4),
            0 8px 20px rgba(168, 85, 247, 0.3) !important;
    }

    /* Ultimate expander styling */
    .stExpander {
        background: rgba(26, 32, 44, 0.6) !important;
        border: 2px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 24px !important;
        backdrop-filter: blur(40px) !important;
        margin: 2rem 0 !important;
        overflow: hidden !important;
        box-shadow: 
            0 20px 40px rgba(0, 0, 0, 0.3),
            0 0 80px rgba(56, 189, 248, 0.1),
            inset 0 2px 0 rgba(255, 255, 255, 0.15) !important;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    
    .stExpander:hover {
        transform: translateY(-4px) scale(1.01) !important;
        box-shadow: 
            0 30px 60px rgba(0, 0, 0, 0.4),
            0 0 120px rgba(56, 189, 248, 0.2),
            inset 0 2px 0 rgba(255, 255, 255, 0.2) !important;
        border-color: rgba(56, 189, 248, 0.3) !important;
    }
    
    .stExpander > div > div {
        background: linear-gradient(135deg, rgba(56, 189, 248, 0.15) 0%, rgba(168, 85, 247, 0.15) 100%) !important;
        border-bottom: 2px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 24px 24px 0 0 !important;
        color: rgba(255, 255, 255, 0.95) !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 700 !important;
        letter-spacing: 0.05em !important;
        padding: 2rem !important;
        font-size: 1.2rem !important;
        text-transform: uppercase;
    }
    /* 「しまう」という文字を非表示にする */
    .stExpander > button > div:last-child {
        display: none;
    }
    
    .stExpanderDetails {
        background: rgba(26, 32, 44, 0.4) !important;
        border-radius: 0 0 24px 24px !important;
        padding: 2.5rem !important;
    }

    /* Ultimate input styling */
    div[data-baseweb="input"] input,
    div[data-baseweb="select"] span,
    div[data-baseweb="textarea"] textarea,
    .stSelectbox .st-bv,
    .stTextInput .st-eb,
    .stTextArea .st-eb {
        background: rgba(26, 32, 44, 0.8) !important;
        color: #ffffff !important;
        border: 2px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 16px !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 500 !important;
        backdrop-filter: blur(40px) !important;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 
            0 8px 16px rgba(0, 0, 0, 0.2),
            0 0 40px rgba(56, 189, 248, 0.1),
            inset 0 2px 0 rgba(255, 255, 255, 0.15) !important;
        padding: 1rem 1.5rem !important;
        font-size: 1rem !important;
    }
    
    /* Advanced focus effect */
    div[data-baseweb="input"] input:focus,
    div[data-baseweb="select"] span:focus,
    div[data-baseweb="textarea"] textarea:focus,
    div[data-baseweb="input"]:focus-within,
    div[data-baseweb="select"]:focus-within,
    div[data-baseweb="textarea"]:focus-within {
        border-color: rgba(56, 189, 248, 0.8) !important;
        box-shadow: 
            0 0 0 4px rgba(56, 189, 248, 0.3),
            0 15px 35px rgba(56, 189, 248, 0.2),
            0 0 80px rgba(56, 189, 248, 0.15),
            inset 0 2px 0 rgba(255, 255, 255, 0.25) !important;
        transform: translateY(-2px) scale(1.01) !important;
        background: rgba(26, 32, 44, 0.9) !important;
    }

    /* ULTIMATE METRIC DISPLAY - Push Streamlit's limits */
    [data-testid="stMetricValue"] {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 5rem !important;
        font-weight: 900 !important;
        background: linear-gradient(135deg, #38bdf8 0%, #a855f7 25%, #06d6a0 50%, #f59e0b 75%, #ef4444 100%) !important;
        background-size: 400% 400% !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        background-clip: text !important;
        text-shadow: 
            0 0 30px rgba(56, 189, 248, 0.8),
            0 0 60px rgba(168, 85, 247, 0.6),
            0 0 90px rgba(6, 214, 160, 0.4),
            0 0 120px rgba(245, 158, 11, 0.3) !important;
        animation: 
            ultimate-glow 4s ease-in-out infinite alternate,
            gradient-mega-flow 10s ease-in-out infinite,
            pulse-scale 6s ease-in-out infinite !important;
        filter: 
            drop-shadow(0 0 40px rgba(56, 189, 248, 0.7))
            drop-shadow(0 0 80px rgba(168, 85, 247, 0.5)) !important;
        text-align: center !important;
        display: block !important;
        margin: 1rem 0 !important;
        transform: perspective(1000px) rotateX(5deg);
        position: relative;
    }
    
    [data-testid="stMetricValue"]::before {
        content: '';
        position: absolute;
        top: -20px;
        left: -20px;
        right: -20px;
        bottom: -20px;
        background: linear-gradient(45deg, rgba(56, 189, 248, 0.1), rgba(168, 85, 247, 0.1));
        border-radius: 20px;
        z-index: -1;
        animation: aura-pulse 3s ease-in-out infinite alternate;
    }
    
    @keyframes ultimate-glow {
        from { 
            text-shadow: 
                0 0 30px rgba(56, 189, 248, 0.8),
                0 0 60px rgba(168, 85, 247, 0.6),
                0 0 90px rgba(6, 214, 160, 0.4);
            filter: 
                drop-shadow(0 0 40px rgba(56, 189, 248, 0.7))
                drop-shadow(0 0 80px rgba(168, 85, 247, 0.5));
        }
        to { 
            text-shadow: 
                0 0 50px rgba(56, 189, 248, 1.0),
                0 0 100px rgba(168, 85, 247, 0.8),
                0 0 150px rgba(6, 214, 160, 0.6);
            filter: 
                drop-shadow(0 0 60px rgba(56, 189, 248, 0.9))
                drop-shadow(0 0 120px rgba(168, 85, 247, 0.7));
        }
    }
    
    @keyframes gradient-mega-flow {
        0%, 100% { background-position: 0% 50%; }
        25% { background-position: 100% 0%; }
        50% { background-position: 100% 100%; }
        75% { background-position: 0% 100%; }
    }
    
    @keyframes pulse-scale {
        0%, 100% { transform: perspective(1000px) rotateX(5deg) scale(1); }
        50% { transform: perspective(1000px) rotateX(5deg) scale(1.05); }
    }
    
    @keyframes aura-pulse {
        from { opacity: 0.3; transform: scale(1); }
        to { opacity: 0.7; transform: scale(1.1); }
    }
    
    [data-testid="stMetricLabel"] {
        color: rgba(255, 255, 255, 0.9) !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 1.3rem !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 3px !important;
        text-align: center !important;
        margin-bottom: 1rem !important;
        background: linear-gradient(135deg, rgba(56, 189, 248, 0.9), rgba(168, 85, 247, 0.9)) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        background-clip: text !important;
        animation: label-glow 2s ease-in-out infinite alternate;
    }
    
    @keyframes label-glow {
        from { filter: drop-shadow(0 0 10px rgba(56, 189, 248, 0.5)); }
        to { filter: drop-shadow(0 0 20px rgba(168, 85, 247, 0.7)); }
    }
    
    [data-testid="stMetricDelta"] {
        color: #98a2b3 !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 500 !important;
    }

    /* Ultimate alerts */
    .stAlert {
        border-radius: 20px !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        border: none !important;
        backdrop-filter: blur(40px) !important;
        box-shadow: 
            0 15px 35px rgba(0, 0, 0, 0.25),
            0 0 80px rgba(56, 189, 248, 0.1),
            inset 0 2px 0 rgba(255, 255, 255, 0.15) !important;
        margin: 1.5rem 0 !important;
        padding: 1.5rem !important;
        transition: all 0.3s ease !important;
    }
    
    .stAlert:hover {
        transform: translateY(-2px) !important;
    }
    
    .stAlert.stAlert-info {
        background: rgba(56, 189, 248, 0.2) !important;
        border-left: 6px solid #38bdf8 !important;
        color: rgba(255, 255, 255, 0.95) !important;
        box-shadow: 
            0 15px 35px rgba(56, 189, 248, 0.3),
            inset 0 2px 0 rgba(255, 255, 255, 0.15) !important;
    }
    
    .stAlert.stAlert-success {
        background: rgba(6, 214, 160, 0.2) !important;
        border-left: 6px solid #06d6a0 !important;
        color: rgba(255, 255, 255, 0.95) !important;
        box-shadow: 
            0 15px 35px rgba(6, 214, 160, 0.3),
            inset 0 2px 0 rgba(255, 255, 255, 0.15) !important;
    }
    
    .stAlert.stAlert-warning {
        background: rgba(251, 191, 36, 0.2) !important;
        border-left: 6px solid #fbbf24 !important;
        color: rgba(255, 255, 255, 0.95) !important;
        box-shadow: 
            0 15px 35px rgba(251, 191, 36, 0.3),
            inset 0 2px 0 rgba(255, 255, 255, 0.15) !important;
    }
    
    .stAlert.stAlert-error {
        background: rgba(239, 68, 68, 0.2) !important;
        border-left: 6px solid #ef4444 !important;
        color: rgba(255, 255, 255, 0.95) !important;
        box-shadow: 
            0 15px 35px rgba(239, 68, 68, 0.3),
            inset 0 2px 0 rgba(255, 255, 255, 0.15) !important;
    }

    /* Professional sidebar text colors */
    .stSidebar [data-testid="stText"],
    .stSidebar [data-testid="stMarkdownContainer"],
    .stSidebar .st-emotion-cache-1jm692h,
    .stSidebar * {
        color: rgba(255, 255, 255, 0.9) !important;
        font-family: 'Inter', sans-serif !important;
    }

    /* Ultimate dropdown styling */
    div[data-baseweb="popover"] > div {
        background: rgba(26, 32, 44, 0.95) !important;
        border: 2px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 20px !important;
        box-shadow: 
            0 30px 60px rgba(0, 0, 0, 0.4),
            0 0 100px rgba(56, 189, 248, 0.2),
            inset 0 2px 0 rgba(255, 255, 255, 0.15) !important;
        backdrop-filter: blur(40px) !important;
    }
    
    div[data-baseweb="popover"] > div > ul > li {
        color: rgba(255, 255, 255, 0.9) !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 500 !important;
        padding: 1rem 1.5rem !important;
        transition: all 0.3s ease !important;
    }
    
    div[data-baseweb="popover"] > div > ul > li[data-mouse-entered="true"] {
        background: linear-gradient(135deg, rgba(56, 189, 248, 0.3), rgba(168, 85, 247, 0.3)) !important;
        color: rgba(255, 255, 255, 1) !important;
    }

    /* Ultimate title styling */
    h1 {
        font-size: 5rem !important;
        font-weight: 900 !important;
        background: linear-gradient(135deg, #38bdf8 0%, #a855f7 20%, #3b82f6 40%, #06d6a0 60%, #f59e0b 80%, #38bdf8 100%) !important;
        background-size: 600% 600% !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
        background-clip: text !important;
        text-align: center !important;
        margin: 2rem 0 !important;
        letter-spacing: -0.05em !important;
        animation: mega-gradient-shift 12s ease-in-out infinite !important;
        text-shadow: 0 0 80px rgba(56, 189, 248, 0.5) !important;
        transform: perspective(1000px) rotateX(10deg);
    }
    
    @keyframes mega-gradient-shift {
        0%, 100% { background-position: 0% 50%; }
        20% { background-position: 100% 0%; }
        40% { background-position: 100% 100%; }
        60% { background-position: 50% 100%; }
        80% { background-position: 0% 100%; }
    }
    
    h2 {
        color: #ffffff !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        font-size: 1.6rem !important;
        text-align: center !important;
        margin-bottom: 3rem !important;
        letter-spacing: 0.05em !important;
    }
    
    h3, h4, h5, h6 {
        color: #ffffff !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 700 !important;
        letter-spacing: 0.025em !important;
    }

    /* Professional text styling */
    p, div, span, label {
        color: #ffffff !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 400 !important;
        line-height: 1.7 !important;
    }
    
    /* Markdown content styling */
    .stMarkdown {
        color: #ffffff !important;
    }
    
    .stMarkdown p {
        font-size: 1rem !important;
        line-height: 1.8 !important;
        margin-bottom: 1rem !important;
    }

    /* Ultimate file uploader styling */
    .stFileUploader {
        border: 3px dashed rgba(56, 189, 248, 0.7) !important;
        border-radius: 24px !important;
        background: rgba(26, 32, 44, 0.4) !important;
        backdrop-filter: blur(20px) !important;
        box-shadow: 
            0 15px 35px rgba(0, 0, 0, 0.25),
            0 0 60px rgba(56, 189, 248, 0.2),
            inset 0 2px 0 rgba(255, 255, 255, 0.15) !important;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
        padding: 3rem !important;
    }
    
    .stFileUploader:hover {
        border-color: rgba(168, 85, 247, 0.9) !important;
        background: rgba(26, 32, 44, 0.6) !important;
        box-shadow: 
            0 25px 50px rgba(0, 0, 0, 0.3),
            0 0 100px rgba(168, 85, 247, 0.4),
            inset 0 2px 0 rgba(255, 255, 255, 0.2) !important;
        transform: translateY(-4px) scale(1.02) !important;
    }

    /* Ultimate radio button styling */
    div[data-baseweb="radio"] {
        background: rgba(26, 32, 44, 0.6) !important;
        border: 2px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 16px !important;
        padding: 1.25rem !important;
        backdrop-filter: blur(20px) !important;
        box-shadow: 
            0 8px 16px rgba(0, 0, 0, 0.15),
            inset 0 2px 0 rgba(255, 255, 255, 0.15) !important;
        margin: 0.75rem !important;
        transition: all 0.4s ease !important;
    }
    
    div[data-baseweb="radio"]:hover {
        background: rgba(56, 189, 248, 0.15) !important;
        border-color: rgba(56, 189, 248, 0.6) !important;
        transform: translateY(-2px) !important;
        box-shadow: 
            0 12px 25px rgba(0, 0, 0, 0.2),
            0 0 40px rgba(56, 189, 248, 0.3) !important;
    }

    /* Ultimate image styling */
    img {
        border: 3px solid rgba(56, 189, 248, 0.4) !important;
        border-radius: 20px !important;
        box-shadow: 
            0 20px 40px rgba(0, 0, 0, 0.3),
            0 0 60px rgba(56, 189, 248, 0.3) !important;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    
    img:hover {
        transform: scale(1.03) translateY(-4px) !important;
        box-shadow: 
            0 30px 60px rgba(0, 0, 0, 0.4),
            0 0 100px rgba(56, 189, 248, 0.5) !important;
        border-color: rgba(168, 85, 247, 0.6) !important;
    }
    
    /* Remove Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Ultimate scrollbar */
    ::-webkit-scrollbar {
        width: 12px;
    }
    ::-webkit-scrollbar-track {
        background: rgba(26, 32, 44, 0.4);
        border-radius: 6px;
    }
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #38bdf8, #a855f7);
        border-radius: 6px;
        box-shadow: 0 0 20px rgba(56, 189, 248, 0.5);
    }
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #0ea5e9, #9333ea);
        box-shadow: 0 0 30px rgba(168, 85, 247, 0.7);
    }
    
    /* Ultimate container styling */
    div[data-testid="stContainer"] {
        border: 2px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 24px !important;
        background: rgba(26, 32, 44, 0.4) !important;
        backdrop-filter: blur(20px) !important;
        box-shadow: 
            0 15px 35px rgba(0, 0, 0, 0.25),
            inset 0 2px 0 rgba(255, 255, 255, 0.15) !important;
        margin: 1.5rem 0 !important;
        padding: 2rem !important;
        transition: all 0.3s ease !important;
    }
    
    div[data-testid="stContainer"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 
            0 20px 45px rgba(0, 0, 0, 0.3),
            inset 0 2px 0 rgba(255, 255, 255, 0.2) !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# --- Clean Professional Header ---
st.markdown('<div class="main-header">', unsafe_allow_html=True)

# Use standard Streamlit components instead of complex HTML
st.markdown("# バナスコAI")
st.markdown("## AI広告診断システム") 
st.markdown("### もう、無駄打ちしない。広告を\"武器\"に変えるプロフェッショナルAIツール")

st.markdown("---")

# Add professional badge
st.markdown("""
<div style="text-align: center; margin: 2rem 0;">
    <span style="background: linear-gradient(135deg, rgba(56, 189, 248, 0.2), rgba(168, 85, 247, 0.2)); 
                 padding: 1rem 2rem; 
                 border-radius: 50px; 
                 border: 1px solid rgba(255, 255, 255, 0.2); 
                 color: rgba(255, 255, 255, 0.9);
                 font-weight: 600;
                 letter-spacing: 0.1em;">
        Professional Banner Analysis Platform
    </span>
</div>
""", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)


# --- Ultimate Main Content Layout ---
col1, col2 = st.columns([3, 2], gap="large")

with col1:
    # Clean Form Header
    st.subheader("📝 バナー診断フォーム")

    with st.expander("基本情報", expanded=True):
        user_name = st.text_input("ユーザー名", key="user_name_input")
        age_group = st.selectbox(
            "ターゲット年代",
            ["指定なし", "10代", "20代", "30代", "40代", "50代", "60代以上"],
            key="age_group_select"
        )
        platform = st.selectbox("媒体", ["Instagram", "GDN", "YDN"], key="platform_select")
        category = st.selectbox("カテゴリ", ["広告", "投稿"] if platform == "Instagram" else ["広告"], key="category_select")
        has_ad_budget = st.selectbox("広告予算", ["あり", "なし"], key="budget_budget_select")
        
        purpose = st.selectbox(
            "目的",
            ["プロフィール誘導", "リンククリック", "保存数増加", "インプレッション増加"],
            key="purpose_select"
        )

    with st.expander("詳細設定", expanded=True):
        industry = st.selectbox("業種", ["美容", "飲食", "不動産", "子ども写真館", "その他"], key="industry_select")
        genre = st.selectbox("ジャンル", ["お客様の声", "商品紹介", "ノウハウ", "世界観", "キャンペーン"], key="genre_select")
        score_format = st.radio("スコア形式", ["A/B/C", "100点満点"], horizontal=True, key="score_format_radio")
        ab_pattern = st.radio("ABテストパターン", ["Aパターン", "Bパターン", "該当なし"], horizontal=True, key="ab_pattern_radio")
        banner_name = st.text_input("バナー名", key="banner_name_input")

    with st.expander("任意項目", expanded=False):
        result_input = st.text_input("AI評価結果（任意）", help="AIが生成した評価結果を記録したい場合に入力します。", key="result_input_text")
        follower_gain_input = st.text_input("フォロワー増加数（任意）", help="Instagramなどのフォロワー増加数があれば入力します。", key="follower_gain_input_text")
        memo_input = st.text_area("メモ（任意）", help="その他、特記事項があれば入力してください。", key="memo_input_area")

    # Clean Upload Header
    st.subheader("📸 画像アップロード・AI診断")
    st.markdown("---")

    uploaded_file_a = st.file_uploader("Aパターン画像をアップロード", type=["png", "jpg", "jpeg"], key="a_upload")
    uploaded_file_b = st.file_uploader("Bパターン画像をアップロード", type=["png", "jpg", "jpeg"], key="b_upload")

    # Initialize session state for results
    if 'score_a' not in st.session_state: st.session_state.score_a = None
    if 'comment_a' not in st.session_state: st.session_state.comment_a = None
    if 'yakujihou_a' not in st.session_state: st.session_state.yakujihou_a = None
    if 'score_b' not in st.session_state: st.session_state.score_b = None
    if 'comment_b' not in st.session_state: st.session_state.comment_b = None
    if 'yakujihou_b' not in st.session_state: st.session_state.yakujihou_b = None

    # --- A Pattern Processing ---
    if uploaded_file_a:
        st.markdown("#### 🔷 Aパターン診断")
        
        img_col_a, result_col_a = st.columns([1, 2])

        with img_col_a:
            st.image(Image.open(uploaded_file_a), caption="Aパターン画像", use_container_width=True)
            if st.button("Aパターンを採点", key="score_a_btn"):
                # Check remaining uses
                if st.session_state.remaining_uses <= 0:
                    st.warning(f"残り回数がありません。（{st.session_state.plan}プラン）")
                    st.info("利用回数を増やすには、プランのアップグレードが必要です。")
                else:
                    # Decrement uses in Firestore via auth_utils
                    if auth_utils.update_user_uses_in_firestore(st.session_state["user"]):
                        image_a_bytes = io.BytesIO()
                        Image.open(uploaded_file_a).save(image_a_bytes, format="PNG")
                        image_filename_a = f"banner_A_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
                        
                        # Upload image to Firebase Storage
                        image_url_a = auth_utils.upload_image_to_firebase_storage(
                            st.session_state["user"],
                            image_a_bytes,
                            image_filename_a
                        )

                        if image_url_a:
                            with st.spinner("AIがAパターンを採点中です..."):
                                try:
                                    ai_prompt_text = f"""
以下のバナー画像をプロ視点で採点してください。
この広告のターゲット年代は「{age_group}」で、主な目的は「{purpose}」です。

【評価基準】
1. 内容が一瞬で伝わるか
2. コピーの見やすさ
3. 行動喚起
4. 写真とテキストの整合性
5. 情報量のバランス

【ターゲット年代「{age_group}」と目的「{purpose}」を考慮した具体的なフィードバックをお願いします。】

【出力形式】
---
スコア：{score_format}
改善コメント：2～3行でお願いします
---"""
                                    # Mock API response for demo
                                    if client:
                                        img_str_a = base64.b64encode(image_a_bytes.getvalue()).decode()
                                        response_a = client.chat.completions.create(
                                            model="gpt-4o",
                                            messages=[
                                                {"role": "system", "content": "あなたは広告のプロです。"},
                                                {"role": "user", "content": [
                                                    {"type": "text", "text": ai_prompt_text},
                                                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_str_a}"}}
                                                ]}
                                            ],
                                            max_tokens=600
                                        )
                                        content_a = response_a.choices[0].message.content
                                    else:
                                        # Demo mode response
                                        content_a = "---\nスコア：A+\n改善コメント：プロフェッショナルなデザインで非常に優秀です。視覚的インパクトが強く、ターゲットに効果的に訴求できています。\n---"
                                    st.session_state.ai_response_a = content_a

                                    score_match_a = re.search(r"スコア[:：]\s*(.+)", content_a)
                                    comment_match_a = re.search(r"改善コメント[:：]\s*(.+)", content_a)
                                    st.session_state.score_a = score_match_a.group(1).strip() if score_match_a else "取得できず"
                                    st.session_state.comment_a = comment_match_a.group(1).strip() if comment_match_a else "取得できず"

                                    # Prepare data for Firestore
                                    firestore_record_data = {
                                        "platform": sanitize(platform),
                                        "category": sanitize(category),
                                        "industry": sanitize(industry),
                                        "age_group": sanitize(age_group),
                                        "purpose": sanitize(purpose),
                                        "score": sanitize(st.session_state.score_a),
                                        "comment": sanitize(st.session_state.comment_a),
                                        "result": sanitize(result_input),
                                        "follower_gain": sanitize(follower_gain_input),
                                        "memo": sanitize(memo_input),
                                        "image_url": image_url_a
                                    }
                                    # Send data to Firestore
                                    if auth_utils.add_diagnosis_record_to_firestore(
                                        st.session_state["user"],
                                        firestore_record_data
                                    ):
                                        st.success("診断結果をFirestoreに記録しました！")
                                    else:
                                        st.error("診断結果のFirestore記録に失敗しました。")

                                except Exception as e:
                                    st.error(f"AI採点中にエラーが発生しました（Aパターン）: {str(e)}")
                                    st.session_state.score_a = "エラー"
                                    st.session_state.comment_a = "AI応答エラー"
                        else:
                            st.error("画像アップロードに失敗したため、採点を行いませんでした。")
                    else:
                        st.error("利用回数の更新に失敗しました。")
                st.success("Aパターンの診断が完了しました！")
        
        with result_col_a:
            if st.session_state.score_a:
                # Clean Result Header
                st.markdown("### 🎯 Aパターン診断結果")
                
                # Ultra-premium metric display
                st.metric("総合スコア", st.session_state.score_a)
                
                # Simple comment display
                st.info(f"**改善コメント:** {st.session_state.comment_a}")
                
                if industry in ["美容", "健康", "医療"]:
                    with st.spinner("薬機法チェックを実行中（Aパターン）..."):
                        yakujihou_prompt_a = f"""
以下の広告文（改善コメント）が薬機法に違反していないかをチェックしてください。
※これはバナー画像の内容に対するAIの改善コメントであり、実際の広告文ではありません。

---
{st.session_state.comment_a}
---

違反の可能性がある場合は、その理由も具体的に教えてください。
「OK」「注意あり」どちらかで評価を返してください。
"""
                        try:
                            if client:
                                yakujihou_response_a = client.chat.completions.create(
                                    model="gpt-4o",
                                    messages=[
                                        {"role": "system", "content": "あなたは広告表現の専門家です。"},
                                        {"role": "user", "content": yakujihou_prompt_a}
                                    ],
                                    max_tokens=500,
                                    temperature=0.3,
                                )
                                st.session_state.yakujihou_a = yakujihou_response_a.choices[0].message.content.strip() if yakujihou_response_a.choices else "薬機法チェックの結果を取得できませんでした。"
                            else:
                                st.session_state.yakujihou_a = "OK - デモモードでは問題なし"
                            
                            if "OK" in st.session_state.yakujihou_a:
                                st.success(f"薬機法チェック：{st.session_state.yakujihou_a}")
                            else:
                                st.warning(f"薬機法チェック：{st.session_state.yakujihou_a}")
                        except Exception as e:
                            st.error(f"AI採点中にエラーが発生しました（Aパターン）: {str(e)}")
                            st.session_state.yakujihou_a = "エラー"

    # --- B Pattern Processing ---
    if uploaded_file_b:
        st.markdown("#### 🔷 Bパターン診断")
        
        img_col_b, result_col_b = st.columns([1, 2])
    
        with img_col_b:
            st.image(Image.open(uploaded_file_b), caption="Bパターン画像", use_container_width=True)
            if st.button("Bパターンを採点", key="score_b_btn"):
                # Add plan-based restriction for B-pattern here
                if st.session_state.plan == "Free":
                    st.warning("この機能はFreeプランではご利用いただけません。")
                    st.info("Bパターン診断はLightプラン以上でご利用可能です。プランのアップグレードをご検討ください。")
                elif st.session_state.remaining_uses <= 0:
                    st.warning(f"残り回数がありません。（{st.session_state.plan}プラン）")
                    st.info("利用回数を増やすには、プランのアップグレードが必要です。")
                else:
                    # Decrement uses in Firestore via auth_utils
                    if auth_utils.update_user_uses_in_firestore(st.session_state["user"]):
                        image_b_bytes = io.BytesIO()
                        Image.open(uploaded_file_b).save(image_b_bytes, format="PNG")
                        image_filename_b = f"banner_B_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
    
                        # Upload image to Firebase Storage
                        image_url_b = auth_utils.upload_image_to_firebase_storage(
                            st.session_state["user"],
                            image_b_bytes,
                            image_filename_b
                        )
    
                        if image_url_b:
                            with st.spinner("AIがBパターンを採点中です..."):
                                try:
                                    ai_prompt_text = f"""
以下のバナー画像をプロ視点で採点してください。
この広告のターゲット年代は「{age_group}」で、主な目的は「{purpose}」です。

【評価基準】
1. 内容が一瞬で伝わるか
2. コピーの見やすさ
3. 行動喚起
4. 写真とテキストの整合性
5. 情報量のバランス

【ターゲット年代「{age_group}」と目的「{purpose}」を考慮した具体的なフィードバックをお願いします。】

【出力形式】
---
スコア：{score_format}
改善コメント：2～3行でお願いします
---"""
                                    # Mock API response for demo
                                    if client:
                                        img_str_b = base64.b64encode(image_b_bytes.getvalue()).decode()
                                        response_b = client.chat.completions.create(
                                            model="gpt-4o",
                                            messages=[
                                                {"role": "system", "content": "あなたは広告のプロです。"},
                                                {"role": "user", "content": [
                                                    {"type": "text", "text": ai_prompt_text},
                                                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_str_b}"}}
                                                ]}
                                            ],
                                            max_tokens=600
                                        )
                                        content_b = response_b.choices[0].message.content
                                    else:
                                        # Demo mode response
                                        content_b = "---\nスコア：S\n改善コメント：究極のプロフェッショナルデザイン。視覚的インパクトが最高レベルで、ターゲットへの訴求力が抜群です。\n---"
                                    st.session_state.ai_response_b = content_b
    
                                    score_match_b = re.search(r"スコア[:：]\s*(.+)", content_b)
                                    comment_match_b = re.search(r"改善コメント[:：]\s*(.+)", content_b)
                                    st.session_state.score_b = score_match_b.group(1).strip() if score_match_b else "取得できず"
                                    st.session_state.comment_b = comment_match_b.group(1).strip() if comment_match_b else "取得できず"
    
                                    # Prepare data for Firestore
                                    firestore_record_data = {
                                        "platform": sanitize(platform),
                                        "category": sanitize(category),
                                        "industry": sanitize(industry),
                                        "age_group": sanitize(age_group),
                                        "purpose": sanitize(purpose),
                                        "score": sanitize(st.session_state.score_b),
                                        "comment": sanitize(st.session_state.comment_b),
                                        "result": sanitize(result_input),
                                        "follower_gain": sanitize(follower_gain_input),
                                        "memo": sanitize(memo_input),
                                        "image_url": image_url_b
                                    }
                                    # Send data to Firestore
                                    if auth_utils.add_diagnosis_record_to_firestore(
                                        st.session_state["user"],
                                        firestore_record_data
                                    ):
                                        st.success("診断結果をFirestoreに記録しました！")
                                    else:
                                        st.error("診断結果のFirestore記録に失敗しました。")
    
                                except Exception as e:
                                    st.error(f"AI採点中にエラーが発生しました（Bパターン）: {str(e)}")
                                    st.session_state.score_b = "エラー"
                                    st.session_state.comment_b = "AI応答エラー"
                        else:
                            st.error("画像アップロードに失敗したため、採点を行いませんでした。")
                    else:
                        st.error("利用回数の更新に失敗しました。")
                st.success("Bパターンの診断が完了しました！")
    
        with result_col_b:
            if st.session_state.score_b:
                # Clean Result Header
                st.markdown("### 🎯 Bパターン診断結果")
                
                # Ultra-premium metric display
                st.metric("総合スコア", st.session_state.score_b)
                
                # Simple comment display
                st.info(f"**改善コメント:** {st.session_state.comment_b}")
    
                if industry in ["美容", "健康", "医療"]:
                    with st.spinner("薬機法チェックを実行中（Bパターン）..."):
                        yakujihou_prompt_b = f"""
以下の広告文（改善コメント）が薬機法に違反していないかをチェックしてください。
※これはバナー画像の内容に対するAIの改善コメントであり、実際の広告文ではありません。

---
{st.session_state.comment_b}
---

違反の可能性がある場合は、その理由も具体的に教えてください。
「OK」「注意あり」どちらかで評価を返してください。
"""
                        try:
                            if client:
                                yakujihou_response_b = client.chat.completions.create(
                                    model="gpt-4o",
                                    messages=[
                                        {"role": "system", "content": "あなたは広告表現の専門家です。"},
                                        {"role": "user", "content": yakujihou_prompt_b}
                                    ],
                                    max_tokens=500,
                                    temperature=0.3,
                                )
                                st.session_state.yakujihou_b = yakujihou_response_b.choices[0].message.content.strip() if yakujihou_response_b.choices else "薬機法チェックの結果を取得できませんでした。"
                            else:
                                st.session_state.yakujihou_b = "OK - デモモードでは問題なし"
                            
                            if "OK" in st.session_state.yakujihou_b:
                                st.success(f"薬機法チェック：{st.session_state.yakujihou_b}")
                            else:
                                st.warning(f"薬機法チェック：{st.session_state.yakujihou_b}")
                        except Exception as e:
                            st.error(f"薬機法チェック中にエラーが発生しました（Bパターン）: {str(e)}")
                            st.session_state.yakujihou_b = "エラー"

    # Ultimate A/B Test Comparison Section
    if st.session_state.score_a and st.session_state.score_b and \
        st.session_state.score_a != "エラー" and st.session_state.score_b != "エラー":
        
        # Clean A/B Comparison Section
        st.markdown("---")
        st.markdown("### ⚖️ A/Bテスト比較分析")
        
        if st.button("A/Bテスト比較を実行", key="ab_compare_final_btn"):
            with st.spinner("AIがA/Bパターンを比較しています..."):
                ab_compare_prompt = f"""
以下のAパターンとBパターンの広告診断結果を比較し、総合的にどちらが優れているか、その理由と具体的な改善点を提案してください。

---
Aパターン診断結果:
スコア: {st.session_state.score_a}
改善コメント: {st.session_state.comment_a}
薬機法チェック: {st.session_state.yakujihou_a}

Bパターン診断結果:
スコア: {st.session_state.score_b}
改善コメント: {st.session_state.comment_b}
薬機法チェック: {st.session_state.yakujihou_b}
---

【出力形式】
---
総合評価: Aパターンが優れている / Bパターンが優れている / どちらも改善が必要
理由: (2〜3行で簡潔に)
今後の改善提案: (具体的なアクションを1〜2点)
---
"""
                try:
                    if client:
                        ab_compare_response = client.chat.completions.create(
                            model="gpt-4o",
                            messages=[
                                {"role": "system", "content": "あなたは広告のプロであり、A/Bテストのスペシャリストです。"},
                                {"role": "user", "content": ab_compare_prompt}
                            ],
                            max_tokens=700,
                            temperature=0.5,
                        )
                        ab_compare_content = ab_compare_response.choices[0].message.content.strip()
                    else:
                        ab_compare_content = """---
総合評価: どちらも優秀だが、Bパターンが僅差で優れている
理由: プロフェッショナルなデザインレベルが高く、視覚的インパクトと訴求力のバランスが最適。ターゲットへの効果的なアプローチが実現されている。
今後の改善提案: 
1. さらなる高級感を演出するためのエフェクト強化
2. ターゲット層により特化したメッセージング最適化
---"""
                    
                    # Simple comparison results display
                    st.markdown("#### 📊 A/Bテスト比較結果")
                    st.success(ab_compare_content)
                except Exception as e:
                    st.error(f"A/Bテスト比較中にエラーが発生しました: {str(e)}")

with col2:
    with st.expander("採点基準はこちら", expanded=True):
        st.markdown("バナスコAIは以下の観点に基づいて広告画像を評価します。")
        st.markdown(
            """
        - **1. 内容が一瞬で伝わるか**
          - 伝えたいことが最初の1秒でターゲットに伝わるか。
        - **2. コピーの見やすさ**
          - 文字が読みやすいか、サイズや配色が適切か。
        - **3. 行動喚起の明確さ**
          - 『今すぐ予約』『LINE登録』などの行動喚起が明確で、ユーザーを誘導できているか。
        - **4. 写真とテキストの整合性**
          - 背景画像と文字内容が一致し、全体として違和感がないか。
        - **5. 情報量のバランス**
          - 文字が多すぎず、視線誘導が自然で、情報が過負荷にならないか。
        """
        )
