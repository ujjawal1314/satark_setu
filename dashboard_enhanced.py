from __future__ import annotations

import calendar
import subprocess
from html import escape
from pathlib import Path
from textwrap import dedent

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from detection_engine import SatarkSetuDetector
from repositories import BorrowerRepository



DATA_FILES = ["borrowers.csv", "loan_transactions.csv", "regional_context.csv"]
ADMIN_CREDENTIALS = {
    "ujjwal": "ujjwal",
    "sumedha": "sumedha",
    "jyoti": "jyoti",
}
BORROWER_PASSWORD = "borrower123"


def ensure_demo_data() -> None:
    required = ["borrowers.csv", 
                "loan_transactions.csv", 
                "regional_context.csv"]
    if all(Path(f).exists() for f in required):
        return
    subprocess.run(
        ["python3", "data_generator.py"], check=True
    )


@st.cache_data(show_spinner=False)
def load_data():
    ensure_demo_data()
    borrowers = pd.read_csv("borrowers.csv")
    transactions = pd.read_csv("loan_transactions.csv", parse_dates=["timestamp"])
    regional = pd.read_csv("regional_context.csv")
    return borrowers, transactions, regional


@st.cache_resource(show_spinner=False)
def initialize_detector(borrowers: pd.DataFrame, transactions: pd.DataFrame, regional: pd.DataFrame):
    detector = SatarkSetuDetector(borrowers, transactions, regional)
    detector.build_graph()
    return detector


st.set_page_config(page_title="SatarkSetu", layout="wide", page_icon="🏦")

st.markdown(
    """
    <style>
    [data-testid="stStatusWidget"] {
        display: none !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"], [class*="st-"] {
        font-family: 'Inter', sans-serif !important;
    }
    .stApp {
        background: 
            radial-gradient(circle at top left, rgba(255,255,255,0.8), transparent 40%),
            linear-gradient(135deg, #fadce4 0%, #f3d1df 50%, #ebd4de 100%);
        color: #1c1c1e;
    }
    .main h1, .main h2, .main h3, .main h4, .main p, .main label, .main span, .main div {
        color: #1c1c1e;
    }
    .hero {
        background: rgba(255, 255, 255, 0.45);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.6);
        color: #1c1c1e;
        border-radius: 32px;
        padding: 32px 36px;
        margin-bottom: 24px;
        box-shadow: 0 24px 48px rgba(180, 140, 150, 0.15);
    }
    .hero h1 {
        color: #1c1c1e !important;
        font-weight: 700 !important;
        margin-bottom: 0.5rem;
        letter-spacing: -0.5px;
    }
    .hero p {
        margin: 0;
        color: #3a3a3c;
        font-weight: 500;
        font-size: 1.05rem;
    }
    .focus-card {
        background: rgba(255, 255, 255, 0.5);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.8);
        border-radius: 24px;
        padding: 24px 28px;
        margin: 12px 0 28px 0;
        box-shadow: 0 16px 32px rgba(180, 140, 150, 0.12);
    }
    .focus-card h4, .focus-card p {
        color: #1c1c1e !important;
        margin: 0;
    }
    .focus-card p {
        margin-top: 8px;
        color: #48484a !important;
        line-height: 1.5;
    }
    [data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.55);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.8);
        border-radius: 24px;
        padding: 18px 22px;
        box-shadow: 0 12px 28px rgba(180, 140, 150, 0.1);
    }
    [data-testid="stMetricLabel"] {
        color: #636366 !important;
        font-weight: 500 !important;
        font-size: 0.95rem !important;
    }
    [data-testid="stMetricValue"] {
        color: #1c1c1e !important;
        font-weight: 700 !important;
        font-size: 2rem !important;
    }
    .flag-pill {
        background: rgba(255, 255, 255, 0.55);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.8);
        border-radius: 20px;
        padding: 12px 18px;
        margin-bottom: 12px;
        box-shadow: 0 8px 24px rgba(180, 140, 150, 0.1);
        color: #1c1c1e;
        font-weight: 600;
        font-size: 1rem;
        display: block;
    }
    [data-baseweb="tab-list"] {
        gap: 12px;
        padding: 4px;
        background: rgba(255, 255, 255, 0.3);
        border-radius: 999px;
        border: 1px solid rgba(255, 255, 255, 0.4);
        display: flex;
        width: 100%;
    }
    [data-testid="stTabs"] button[role="tab"] {
        color: #3a3a3c !important;
        background: transparent !important;
        border-radius: 999px !important;
        border: none !important;
        padding: 12px 20px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        flex: 1 !important;
        text-align: center !important;
    }
    [data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
        background: #1c1c1e !important;
        color: #ffffff !important;
        box-shadow: 0 4px 12px rgba(28, 28, 30, 0.3);
        border-bottom: none !important;
        outline: none !important;
    }
    [data-baseweb="tab-highlight"], [data-baseweb="tab-border"] {
        display: none !important;
    }
    .stButton button {
        border-radius: 999px !important;
        border: 1px solid rgba(255, 255, 255, 0.8) !important;
        background: rgba(255, 255, 255, 0.6) !important;
        backdrop-filter: blur(10px);
        color: #1c1c1e !important;
        font-weight: 600 !important;
        min-height: 48px !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 12px rgba(180, 140, 150, 0.1);
    }
    .stForm [data-testid="stFormSubmitButton"] button,
    button[kind="primary"] {
        background: linear-gradient(90deg, #ff5f2e 0%, #e0287d 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 999px !important;
        box-shadow: 0 8px 16px rgba(224, 40, 125, 0.25) !important;
    }

    .run-ai-btn button:hover,
    .run-ai-btn button:focus,
    .run-ai-btn button:active,
    .run-contagion-btn button:hover,
    .run-contagion-btn button:focus,
    .run-contagion-btn button:active {
        transform: none !important;
        box-shadow: 0 8px 16px 
            rgba(224, 40, 125, 0.25) !important;
        filter: none !important;
        background: linear-gradient(
            90deg, #ff5f2e 0%, #e0287d 100%) !important;
        transition: none !important;
    }
    .stForm [data-testid="stFormSubmitButton"] button p,
    .stForm [data-testid="stFormSubmitButton"] button span,
    button[kind="primary"] p,
    button[kind="primary"] span {
        color: #ffffff !important;
    }
    .stButton button:hover {
        background: rgba(255, 255, 255, 0.6) !important;
        color: #1c1c1e !important;
        transform: translateY(-3px) !important;
        box-shadow: 0 16px 32px rgba(0, 0, 0, 0.12) !important;
        transition: all 0.2s ease !important;
    }
    .stForm [data-testid="stFormSubmitButton"] button:hover,
    button[kind="primary"]:hover {
        filter: brightness(1.1) !important;
        color: #ffffff !important;
        transform: translateY(-4px) scale(1.02) !important;
        box-shadow: 0 12px 28px 
            rgba(224, 40, 125, 0.35) !important;
    }

    .run-ai-btn button:hover,
    .run-contagion-btn button:hover {
        filter: none !important;
        transform: none !important;
        box-shadow: none !important;
        background: linear-gradient(
            90deg, #ff5f2e 0%, #e0287d 100%
        ) !important;
        color: #1c1c1e !important;
        cursor: pointer !important;
    }

    .run-ai-btn button:hover p,
    .run-ai-btn button:hover span,
    .run-contagion-btn button:hover p,
    .run-contagion-btn button:hover span {
        color: #1c1c1e !important;
    }
    /* SideBar */
    [data-testid="stSidebar"] {
        background: rgba(255, 255, 255, 0.35) !important;
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-right: 1px solid rgba(255, 255, 255, 0.5);
    }
    [data-testid="stSidebar"] * {
        color: #1c1c1e !important;
    }
    [data-testid="stSidebar"] [data-baseweb="select"] > div,
    [data-testid="stSidebar"] [data-baseweb="input"] > div {
        background: rgba(255, 255, 255, 0.6) !important;
        border: 1px solid rgba(255, 255, 255, 0.9) !important;
        border-radius: 12px !important;
    }
    [data-testid="stSidebar"] [data-baseweb="select"] *,
    [data-testid="stSidebar"] [data-baseweb="input"] *,
    [data-testid="stSidebar"] .stSlider * {
        color: #1c1c1e !important;
    }
    /* Section Cards */
    .section-card {
        background: rgba(255, 255, 255, 0.5);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.8);
        border-radius: 28px;
        padding: 24px;
        box-shadow: 0 16px 36px rgba(180, 140, 150, 0.1);
    }
    /* Headers Fix */
    div[data-testid="stMarkdownContainer"] > h1, 
    div[data-testid="stMarkdownContainer"] > h2, 
    div[data-testid="stMarkdownContainer"] > h3 {
        color: #1c1c1e !important;
        font-weight: 700 !important;
        letter-spacing: -0.5px;
    }
    .glass-table-shell {
        background: rgba(255, 255, 255, 0.26);
        backdrop-filter: blur(18px);
        -webkit-backdrop-filter: blur(18px);
        border: 1px solid rgba(255, 255, 255, 0.75);
        border-radius: 22px;
        box-shadow: 0 16px 32px rgba(180, 140, 150, 0.1);
        overflow: hidden;
    }
    .glass-table-wrap {
        overflow-x: auto;
    }
    .glass-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        color: #1c1c1e;
        font-size: 0.98rem;
        background: transparent;
    }
    .glass-table thead th {
        position: sticky;
        top: 0;
        z-index: 1;
        background: rgba(255, 255, 255, 0.98);
        backdrop-filter: none;
        -webkit-backdrop-filter: none;
        color: #2c2c2e;
        text-align: left;
        padding: 14px 16px;
        font-weight: 700;
        border-bottom: 1px solid rgba(255, 255, 255, 0.78);
    }
    .glass-table tbody td {
        padding: 13px 16px;
        background: rgba(255, 255, 255, 0.12);
        border-bottom: 1px solid rgba(255, 255, 255, 0.34);
        color: #1c1c1e;
    }
    .glass-table tbody tr:nth-child(even) td {
        background: rgba(255, 255, 255, 0.18);
    }
    .glass-table tbody tr:hover td {
        background: rgba(255, 255, 255, 0.28);
    }
    .status-pill {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: 600;
        text-align: center;
    }
    .status-success {
        background: rgba(34, 197, 94, 0.15);
        color: #15803d;
        border: 1px solid rgba(34, 197, 94, 0.4);
    }
    .status-error {
        background: rgba(239, 68, 68, 0.15);
        color: #b91c1c;
        border: 1px solid rgba(239, 68, 68, 0.4);
    }
    .status-warning {
        background: rgba(234, 179, 8, 0.15);
        color: #a16207;
        border: 1px solid rgba(234, 179, 8, 0.4);
    }
    /* Turfingo Blueprint */
    .landing-hero {
        padding: 4vh 2vw 2vh 2vw;
        display: grid;
        grid-template-columns: minmax(0, 0.95fr) minmax(360px, 1.05fr);
        gap: 32px;
        align-items: center;
        min-height: 75vh;
        position: relative;
        overflow: hidden;
    }
    .landing-copy {
        position: relative;
        z-index: 2;
    }
    .landing-logo-chip {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 88px;
        height: 88px;
        margin-bottom: 20px;
        border-radius: 24px;
        background: rgba(255,255,255,0.38);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255,255,255,0.75);
        box-shadow: 0 18px 32px rgba(120, 60, 80, 0.12);
    }
    .landing-logo-chip img {
        width: 62px;
        height: 62px;
        object-fit: contain;
    }
    .landing-hero h1 {
        font-size: 7.5rem;
        font-weight: 800;
        font-style: italic;
        line-height: 1;
        letter-spacing: -3px;
        color: #174229;
        margin: 0 0 24px 0;
        text-transform: uppercase;
    }
    .landing-hero p.subtext {
        font-size: 1.35rem;
        color: #3a3a3c;
        max-width: 580px;
        line-height: 1.6;
        font-weight: 500;
        margin-bottom: 48px;
        border-left: 4px solid #174229;
        padding-left: 24px;
    }
    .landing-metrics {
        display: flex;
        gap: 80px;
        border-top: 1px solid rgba(23,66,41,0.15);
        padding-top: 32px;
        margin-top: 60px;
    }
    .metric-box h3 {
        font-size: 2.8rem;
        font-weight: 800;
        margin: 0 0 4px 0;
        color: #174229;
    }
    .metric-box p {
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        color: #636366;
        margin: 0;
        font-weight: 700;
    }
    .landing-art {
        position: relative;
        min-height: 620px;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .hero-cutout {
        position: absolute;
        overflow: hidden;
        border-radius: 34px;
        background: rgba(255,255,255,0.14);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.55);
        box-shadow: 0 26px 44px rgba(120, 60, 80, 0.14);
    }
    .hero-cutout img {
        position: absolute;
        max-width: none;
        filter: drop-shadow(0 18px 26px rgba(15, 60, 34, 0.14));
    }
    .hero-cutout.main {
        width: 56%;
        height: 78%;
        right: 6%;
        top: 10%;
        transform: rotate(7deg);
    }
    .hero-cutout.main img {
        width: 132%;
        left: -18%;
        top: -8%;
        transform: rotate(-5deg);
    }
    .hero-cutout.hand {
        width: 30%;
        height: 34%;
        left: 8%;
        top: 18%;
        transform: rotate(-10deg);
    }
    .hero-cutout.hand img {
        width: 188%;
        left: -96%;
        top: 2%;
    }
    .hero-cutout.bag {
        width: 28%;
        height: 32%;
        left: 24%;
        bottom: 14%;
        transform: rotate(9deg);
    }
    .hero-cutout.bag img {
        width: 186%;
        left: -18%;
        top: -54%;
    }
    .hero-cutout.arrow {
        width: 24%;
        height: 22%;
        right: 18%;
        bottom: 8%;
        transform: rotate(-8deg);
    }
    .hero-cutout.arrow img {
        width: 165%;
        left: -66%;
        top: -16%;
    }
    .hero-echo {
        position: absolute;
        width: 78%;
        max-width: none;
        opacity: 0.08;
        right: 2%;
        top: 9%;
        transform: rotate(8deg);
    }
    @media (max-width: 1100px) {
        .landing-hero {
            grid-template-columns: 1fr;
            gap: 20px;
        }
        .landing-art {
            min-height: 440px;
        }
        .landing-hero h1 {
            font-size: 5.4rem;
        }
    }
    
    .mission-row {
        padding: 10vh 2vw;
        border-top: 1px solid rgba(23,66,41,0.15);
        background: transparent;
    }
    .mission-card {
        padding: 20px 40px;
        height: 100%;
        background: transparent;
        border-right: 1px solid rgba(23,66,41,0.15);
    }
    .mission-card:last-child {
        border-right: none;
    }
    .mission-number {
        font-size: 3.5rem;
        font-weight: 300;
        font-style: italic;
        color: rgba(23,66,41,0.2);
        margin-bottom: 24px;
        line-height: 1;
    }
    .mission-card h3 {
        font-size: 2.2rem;
        font-weight: 800;
        font-style: italic;
        margin-bottom: 16px;
        color: #1c1c1e;
    }
    .mission-card p {
        font-size: 1.1rem;
        color: #48484a;
        line-height: 1.6;
    }

    .about-section {
        padding: 10vh 2vw;
        border-top: 1px solid rgba(23,66,41,0.15);
    }
    .about-mini-title {
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 2px;
        font-weight: 700;
        color: #174229;
        margin-bottom: 16px;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .about-mini-title::before {
        content: "";
        display: inline-block;
        width: 32px;
        height: 2px;
        background: #174229;
    }
    .about-header {
        font-size: 5rem;
        font-weight: 800;
        font-style: italic;
        text-transform: uppercase;
        color: #174229;
        line-height: 1.1;
        margin-bottom: 32px;
        letter-spacing: -2px;
    }
    .about-text {
        font-size: 1.3rem;
        color: #3a3a3c;
        max-width: 500px;
        line-height: 1.6;
        font-weight: 500;
    }
    .staggered-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 24px;
        margin-top: 40px;
    }
    .staggered-item {
        background: rgba(255,255,255,0.4);
        border: 1px solid rgba(255,255,255,0.6);
        border-radius: 20px;
        height: 280px;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 16px 40px rgba(0,0,0,0.06);
        font-weight: 700;
        font-size: 1.2rem;
        color: #174229;
        overflow: hidden;
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
    }
    .staggered-item:nth-child(2n) {
        transform: translateY(60px);
    }
    .contact-card {
        background: rgba(255,255,255,0.7);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 16px;
        border: 1px solid rgba(255,255,255,0.9);
        box-shadow: 0 8px 24px rgba(0,0,0,0.03);
    }
    .contact-card p.small {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #636366;
        margin: 0 0 8px 0;
        font-weight: 700;
    }
    .contact-card h4 {
        margin: 0;
        font-size: 1.2rem;
        font-weight: 700;
        color: #1c1c1e;
    }
    /* Fix all widget labels — make them dark */
    [data-testid="stWidgetLabel"] p,
    [data-testid="stWidgetLabel"] label,
    .stSlider label,
    .stSelectbox label {
        color: #1c1c1e !important;
        font-weight: 600 !important;
        opacity: 1 !important;
    }

    /* Fix selectbox — light background, dark text */
    [data-baseweb="select"] > div {
        background: rgba(255, 255, 255, 0.85) !important;
        border: 1px solid rgba(255,255,255,0.9) !important;
        border-radius: 12px !important;
    }
    [data-baseweb="select"] span,
    [data-baseweb="select"] div {
        color: #1c1c1e !important;
        background: transparent !important;
    }

    /* Fix slider value */
    [data-testid="stSlider"] p {
        color: #1c1c1e !important;
    }

    /* Fix metric labels */
    [data-testid="stMetricLabel"] p {
        color: #636366 !important;
        opacity: 1 !important;
    }

    /* IMPORTANT — restore selected tab white text */
    [data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
        color: #ffffff !important;
        background: #1c1c1e !important;
        box-shadow: 0 4px 12px rgba(28, 28, 30, 0.3);
    }

    /* Unselected tab text must be dark */
    [data-testid="stTabs"] button[role="tab"][aria-selected="false"] {
        color: #3a3a3c !important;
    }

    /* Ensure radio options are explicitly black */
    [data-testid="stRadio"] label p,
    [data-testid="stRadio"] label span {
        color: #1c1c1e !important;
        background: transparent !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

@st.cache_resource(show_spinner=False)
def get_detector():
    d = SatarkSetuDetector(
        borrowers_df, transactions_df, regional_df
    )
    d.build_graph()
    return d

@st.cache_resource(show_spinner=False)  
def get_repo():
    return BorrowerRepository()

_loading = st.empty()
_loading.markdown(
    """
    <div style="
        position: fixed;
        top: 0; left: 0;
        width: 100vw; height: 100vh;
        background: linear-gradient(
            135deg, #fadce4 0%, 
            #f3d1df 50%, 
            #ebd4de 100%
        );
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        z-index: 9999;
    ">
        <div style="
            background: rgba(255,255,255,0.6);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(255,255,255,0.8);
            border-radius: 32px;
            padding: 48px 56px;
            text-align: center;
            box-shadow: 0 24px 48px 
                rgba(180,140,150,0.2);
            min-width: 360px;
        ">
            <div style="
                font-size: 3rem;
                font-weight: 800;
                font-style: italic;
                background: linear-gradient(
                    90deg, #FF9933 0%, 
                    #1c1c1e 50%, 
                    #138808 100%
                );
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                letter-spacing: -2px;
                margin-bottom: 8px;
            ">SatarkSetu</div>
            <div style="
                font-size: 0.9rem;
                color: #48484a;
                font-weight: 500;
                margin-bottom: 32px;
            ">
                Borrower Health Intelligence Platform
            </div>
            <div style="
                width: 100%;
                height: 6px;
                background: rgba(28,28,30,0.08);
                border-radius: 999px;
                overflow: hidden;
                margin-bottom: 16px;
            ">
                <div style="
                    height: 100%;
                    width: 100%;
                    background: linear-gradient(
                        90deg, 
                        #FF9933, 
                        #e0287d, 
                        #138808
                    );
                    border-radius: 999px;
                    animation: loadbar 2s ease-in-out;
                "></div>
            </div>
            <div style="
                font-size: 0.82rem;
                color: #636366;
                font-weight: 500;
            ">
                Initialising risk intelligence engine...
            </div>
        </div>
        <style>
            @keyframes loadbar {
                0%   { width: 0%; }
                30%  { width: 40%; }
                60%  { width: 70%; }
                85%  { width: 90%; }
                100% { width: 100%; }
            }
        </style>
    </div>
    """,
    unsafe_allow_html=True
)

borrowers_df, transactions_df, regional_df = \
    load_data()
detector = get_detector()
repo     = get_repo()

_loading.empty()


def style_figure(fig: go.Figure) -> go.Figure:
    fig.update_layout(
        template=None,
        paper_bgcolor="rgba(255,255,255,0.18)",
        plot_bgcolor="rgba(255,255,255,0.10)",
        font=dict(color="#1c1c1e"),
        title_font=dict(color="#1c1c1e", size=22),
        legend=dict(
            bgcolor="rgba(255,255,255,0.16)",
            bordercolor="rgba(255,255,255,0.35)",
            borderwidth=1,
            font=dict(color="#1c1c1e"),
        ),
        margin=dict(l=16, r=16, t=56, b=56),
    )
    fig.update_xaxes(
        showgrid=True,
        gridcolor="rgba(120, 120, 135, 0.16)",
        zeroline=False,
        linecolor="rgba(120, 120, 135, 0.24)",
        tickfont=dict(color="#3a3a3c"),
        title_font=dict(color="#1c1c1e"),
        title_standoff=16,
        automargin=True,
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor="rgba(120, 120, 135, 0.16)",
        zeroline=False,
        linecolor="rgba(120, 120, 135, 0.24)",
        tickfont=dict(color="#3a3a3c"),
        title_font=dict(color="#1c1c1e"),
        title_standoff=12,
        automargin=True,
    )
    return fig


def render_glass_table(df: pd.DataFrame, *, max_height: int | None = None) -> None:
    if df.empty:
        st.info("No records available.")
        return

    display_df = df.fillna("")
    cols = display_df.columns.tolist()
    head_html = "".join(f"<th>{escape(str(column))}</th>" for column in cols)
    body_rows = []
    for row in display_df.itertuples(index=False):
        cells = []
        for i, col in enumerate(cols):
            val = str(row[i])
            if col.lower() == "status":
                status_lower = val.lower()
                if status_lower in ["paid", "completed", "success", "posted", "active"]:
                    color_class = "status-success"
                elif status_lower in ["delayed", "failed", "overdue", "support required", "support_required"]:
                    color_class = "status-error"
                else:
                    color_class = "status-warning"
                cells.append(f'<td><span class="status-pill {color_class}">{escape(val)}</span></td>')
            else:
                cells.append(f"<td>{escape(val)}</td>")
        body_rows.append(f"<tr>{''.join(cells)}</tr>")
    height_style = f"max-height:{max_height}px;" if max_height else ""
    st.markdown(
        f"""
        <div class="glass-table-shell">
            <div class="glass-table-wrap" style="{height_style}">
                <table class="glass-table">
                    <thead><tr>{head_html}</tr></thead>
                    <tbody>{''.join(body_rows)}</tbody>
                </table>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

@st.cache_data(ttl=600, show_spinner=False)
def build_portfolio_df(_borrowers_df, _transactions_df, 
                       _regional_df):
    borrowers  = _borrowers_df.copy()
    regional   = _regional_df.copy()
    
    # Merge regional data into borrowers directly
    # instead of calling detector per borrower
    merged = borrowers.merge(
        regional[["region", "npa_rate", 
                  "economic_stress_index",
                  "peer_health_baseline"]],
        on="region", how="left"
    )
    
    # Compute risk score vectorised — no per-borrower loop
    missed_norm = (merged["missed_payments_90d"]
                   .clip(0, 4) / 4.0)
    dpd_norm    = (merged["days_past_due"]
                   .clip(0, 90) / 90.0)
    peer_norm   = 1.0 - (merged["peer_score"] / 100.0)
    stress      = merged["regional_stress_factor"]
    repayment   = merged["repayment_consistency"]
    inflow_st   = merged["inflow_stability"]

    risk_score = (
        missed_norm    * 30 +
        dpd_norm       * 25 +
        peer_norm      * 15 +
        (1 - repayment)* 15 +
        stress         * 10 +
        (1 - inflow_st)* 5
    ).clip(0, 100).round(1)

    merged["risk_score"]   = risk_score
    merged["health_score"] = (100 - risk_score).round(1)

    def risk_level(score):
        if score >= 70:   return "High Risk"
        elif score >= 50: return "Medium Risk"
        elif score >= 30: return "Low Risk"
        else:             return "Healthy"

    merged["risk_level"] = merged["risk_score"].apply(
        risk_level
    )
    merged["status"] = "ACTIVE"
    merged["name"]   = merged["name"].str.title()

    return merged


def logout() -> None:
    for key in ["view", "admin_authenticated", "borrower_authenticated", "borrower_id"]:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()


def render_app_hero() -> None:
    img_html = ""
    try:
        import base64
        with open("logo_transparent.png", "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
        img_html = f'<img src="data:image/png;base64,{encoded_string}" style="height: 180px; border-radius: 40px; box-shadow: 0 20px 48px rgba(180, 140, 150, 0.15); margin-bottom: 32px;"/>'
    except Exception:
        pass

    st.markdown(
        f"""
        <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; padding: 80px 40px 60px 40px;">
            {img_html}
            <h1 style="font-size: 6.5rem; line-height: 1.1; margin-bottom: 24px; background: linear-gradient(90deg, #FF9933 0%, #FFFFFF 50%, #138808 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; filter: drop-shadow(0px 6px 12px rgba(0,0,0,0.12)); display: inline-block; font-weight: 800; letter-spacing: -3px;">SatarkSetu</h1>
            <p style="font-size: 1.6rem; color: #2c2c2e; max-width: 800px; line-height: 1.5; font-weight: 500;">Borrower health and contextual recovery intelligence for MSME and government-scheme portfolios.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_segmented_health_bar(score: int, title: str = "Health score") -> str:
    total_segments = 28
    filled = max(0, min(total_segments, round((score / 100.0) * total_segments)))
    segs = "".join(
        [
            f'<div style="width: 8px; height: 34px; background: {"linear-gradient(180deg, #76d596 0%, #47bf6a 100%)" if i < filled else "#eef1f7"}; border-radius: 999px;"></div>'
            for i in range(total_segments)
        ]
    )

    return dedent(
        f"""
        <div style="background: rgba(255,255,255,0.92); border-radius: 28px; padding: 26px 24px; border: 1px solid rgba(255,255,255,0.88); box-shadow: 0 18px 34px rgba(180,140,150,0.10); margin-top: 8px; margin-bottom: 24px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <span style="font-size: 1.05rem; font-weight: 600; color: #1c1c1e;">{title}</span>
                <div style="display: inline-flex; align-items: center; gap: 10px; border: 1px solid rgba(28,28,30,0.08); border-radius: 999px; overflow: hidden;">
                    <span style="padding: 8px 16px; font-size: 0.95rem; color: #1c1c1e;">Apply</span>
                    <span style="display: inline-flex; align-items: center; justify-content: center; width: 42px; height: 42px; background: #f5f6fa; font-size: 1.8rem; color: #a1a7b3;">+</span>
                </div>
            </div>
            <div style="border-top: 1px solid rgba(28,28,30,0.08); margin-bottom: 20px;"></div>
            <h3 style="margin: 0 0 8px 0; font-size: 2.5rem; font-weight: 500; color: #1c1c1e; letter-spacing: -1px;">Your credit score is {score}</h3>
            <p style="margin: 0 0 22px 0; color: #636366; font-size: 0.98rem;">Build a stronger repayment history to keep improving this score.</p>
            <div style="display: flex; gap: 5px; margin-bottom: 24px; width: 100%; align-items: end;">{segs}</div>
            <div style="border-top: 1px solid rgba(28,28,30,0.08); padding-top: 18px;">
                <p style="margin: 0; color: #636366; font-size: 0.92rem; line-height: 1.55;">Your credit score reflects your payment reliability. A higher score supports smoother loan servicing and better repayment standing.</p>
            </div>
        </div>
        """
    ).strip()


def render_transaction_days_card(txns: pd.DataFrame, selected_window_days: int | None = None) -> str:
    if txns.empty:
        return """
        <div style="background: rgba(255,255,255,0.92); border-radius: 28px; padding: 26px 24px; border: 1px solid rgba(255,255,255,0.88); box-shadow: 0 18px 34px rgba(180,140,150,0.10); margin-bottom: 24px;">
            <h3 style="margin: 0 0 10px 0; font-size: 1.9rem; font-weight: 500; color: #1c1c1e;">Transactions days</h3>
            <p style="margin: 0; color: #636366;">No recent transactions available.</p>
        </div>
        """

    recent = txns.copy().sort_values("timestamp")
    recent["day"] = recent["timestamp"].dt.normalize()
    end_day = recent["day"].max()
    available_days = max(1, int((end_day - recent["day"].min()).days) + 1)
    if selected_window_days is None:
        window_days = min(62, max(21, available_days))
    else:
        window_days = min(selected_window_days, available_days)
    days = pd.date_range(end=end_day, periods=window_days, freq="D")
    recent = recent[recent["day"].isin(days)]

    per_day: dict[pd.Timestamp, list[dict]] = {}
    for _, row in recent.iterrows():
        per_day.setdefault(row["day"], []).append(row.to_dict())

    def cell_style(entries: list[dict] | None) -> tuple[str, str]:
        if not entries:
            return ("background:#e9edf7;", "&nbsp;")
        paid = sum(1 for item in entries if str(item["transaction_type"]).upper() == "EMI_PAYMENT" and str(item["status"]).upper() in {"ON_TIME", "COMPLETED", "SUCCESS", "PAID"})
        missed = sum(1 for item in entries if str(item["transaction_type"]).upper() == "EMI_PAYMENT" and str(item["status"]).upper() in {"MISSED", "DELAYED", "FAILED", "OVERDUE"})
        inflow = sum(1 for item in entries if str(item["transaction_type"]).upper() == "BUSINESS_INFLOW")
        outflow = sum(1 for item in entries if str(item["transaction_type"]).upper() == "BUSINESS_OUTFLOW")
        other = len(entries) - paid - missed
        if missed:
            return ("background:#ff8d61; color:white;", str(missed))
        if paid:
            return ("background:#64c983; color:white;", str(paid))
        if inflow:
            return ("background:#4d61e8; color:white;", str(other))
        if outflow:
            return ("background:#8a7cf4; color:white;", str(other))
        return ("background:#e9edf7;", "&nbsp;")

    week_labels = "".join(f"<div style='text-align:center; color:#5e6472; font-size:0.92rem;'>{day}</div>" for day in ["M", "T", "W", "T", "F", "S", "S"])

    start_pad = days[0].weekday()
    cells = ["<div></div>" for _ in range(start_pad)]
    active_days = 0
    paid_days = 0
    missed_days = 0
    inflow_days = 0
    outflow_days = 0
    paid_amount = 0.0
    missed_amount = 0.0
    inflow_amount = 0.0
    outflow_amount = 0.0
    for day in days:
        entries = per_day.get(day.normalize())
        if entries:
            active_days += 1
            paid_today = [item for item in entries if str(item["transaction_type"]).upper() == "EMI_PAYMENT" and str(item["status"]).upper() in {"ON_TIME", "COMPLETED", "SUCCESS", "PAID"}]
            missed_today = [item for item in entries if str(item["transaction_type"]).upper() == "EMI_PAYMENT" and str(item["status"]).upper() in {"MISSED", "DELAYED", "FAILED", "OVERDUE"}]
            inflow_today = [item for item in entries if str(item["transaction_type"]).upper() == "BUSINESS_INFLOW"]
            outflow_today = [item for item in entries if str(item["transaction_type"]).upper() == "BUSINESS_OUTFLOW"]
            paid_days += bool(paid_today)
            missed_days += bool(missed_today)
            inflow_days += bool(inflow_today)
            outflow_days += bool(outflow_today)
            paid_amount += sum(float(item.get("amount") or 0) for item in paid_today)
            missed_amount += sum(float(item.get("amount") or 0) for item in missed_today)
            inflow_amount += sum(float(item.get("amount") or 0) for item in inflow_today)
            outflow_amount += sum(float(item.get("amount") or 0) for item in outflow_today)
        style, value = cell_style(entries)
        cells.append(
            f"<div style='width:48px;height:48px;border-radius:999px;display:flex;align-items:center;justify-content:center;font-size:1.45rem;font-weight:500;{style}'>{value}</div>"
        )
    cells_html = "".join(cells)
    start_day = days.min()
    if start_day.month == end_day.month:
        month_label = f"{calendar.month_name[end_day.month]} {end_day.year}"
    else:
        month_label = f"{calendar.month_abbr[start_day.month]}-{calendar.month_abbr[end_day.month]} {end_day.year}"

    return dedent(
        f"""
        <div style="background: rgba(255,255,255,0.92); border-radius: 28px; padding: 26px 24px; border: 1px solid rgba(255,255,255,0.88); box-shadow: 0 18px 34px rgba(180,140,150,0.10); margin-bottom: 24px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:18px;">
                <h3 style="margin:0; font-size:1.9rem; font-weight:500; color:#1c1c1e;">Transactions days</h3>
                <div style="width:48px;height:48px;border-radius:999px;border:1px solid rgba(28,28,30,0.08);display:flex;align-items:center;justify-content:center;color:#a1a7b3;font-size:1.7rem;">⋮</div>
            </div>
            <div style="border-top:1px solid rgba(28,28,30,0.08); margin-bottom:20px;"></div>
            <div style="display:flex; align-items:center; gap:14px; margin-bottom:22px; flex-wrap:wrap;">
                <div style="font-size:3rem; line-height:1; color:#1c1c1e;">{window_days}</div>
                <div style="font-size:1.5rem; color:#5e6472;">Days</div>
                <div style="margin-left:12px; width:54px;height:54px;border-radius:999px;border:1px solid rgba(28,28,30,0.08);display:flex;align-items:center;justify-content:center;font-size:2rem;color:#1c1c1e;">{active_days}</div>
                <div style="font-size:1.35rem; color:#4b5563;">{month_label}</div>
                <div style="margin-left:auto; display:flex; gap:10px; flex-wrap:wrap;">
                    <span style="padding:8px 12px; border-radius:999px; background:#eef8f1; color:#2f8c57; font-size:0.88rem;">Paid EMI: {paid_days}</span>
                    <span style="padding:8px 12px; border-radius:999px; background:#fff0eb; color:#d86a43; font-size:0.88rem;">Delayed: {missed_days}</span>
                    <span style="padding:8px 12px; border-radius:999px; background:#eef1ff; color:#4d61e8; font-size:0.88rem;">Inflow days: {inflow_days}</span>
                    <span style="padding:8px 12px; border-radius:999px; background:#f1eeff; color:#7a69d9; font-size:0.88rem;">Outflow days: {outflow_days}</span>
                </div>
            </div>
            <div style="border-top:1px solid rgba(28,28,30,0.08); padding-top:18px;">
                <div style="display:grid; grid-template-columns: repeat(7, 48px); gap:12px 14px; justify-content:start; margin-bottom:16px;">{week_labels}</div>
                <div style="display:grid; grid-template-columns: repeat(7, 48px); gap:12px 14px; justify-content:start;">{cells_html}</div>
            </div>
            <div style="margin-top:22px; border-top:1px solid rgba(28,28,30,0.08); padding-top:18px;">
                <p style="margin:0 0 10px 0; color:#636366; font-size:0.95rem; line-height:1.45;">Green shows successful EMI payments, orange shows missed or delayed EMI days, blue marks business inflows, and purple marks business outflows in this borrower's latest activity window.</p>
                <div style="display:flex; gap:20px; flex-wrap:wrap; color:#4b5563; font-size:0.95rem;">
                    <span><strong>Rs {paid_amount:,.0f}</strong> EMI paid</span>
                    <span><strong>Rs {missed_amount:,.0f}</strong> delayed/default EMI</span>
                    <span><strong>Rs {inflow_amount:,.0f}</strong> inflow received</span>
                    <span><strong>Rs {outflow_amount:,.0f}</strong> outflow posted</span>
                </div>
            </div>
        </div>
        """
    ).strip()


def render_borrower_dashboard(borrower_id: str) -> None:
    transparency = detector.analyze_borrower(borrower_id).as_dict()

    _, top_right = st.columns([6, 1])
    with top_right:
        if st.button("Logout", key="borrower_logout", use_container_width=True):
            logout()

    borrower_name = transparency.get("name", "Borrower").title()
    st.markdown(f"<h2 style='margin-top: -32px; margin-bottom: 24px;'>Hello, {escape(borrower_name)} 👋</h2>", unsafe_allow_html=True)
    card_left, card_right = st.columns([1.15, 1])
    with card_left:
        st.markdown(f"### Loan Health Summary for {transparency['name']}")
        st.caption(f"Borrower ID: {borrower_id}")
        st.markdown(render_segmented_health_bar(transparency['health_score'], "Borrower Health"), unsafe_allow_html=True)
        st.info(f"The portfolio peer benchmark for similar borrowers is {transparency['peer_score']}/100.")
        st.write("Regional context:")
        st.write(
            f"Your loan region has a stress factor of {transparency['regional_stress_factor']}. "
            "This is used so the bank does not evaluate borrowers without context."
        )
        st.write("Repayment guidance:")
        st.write(transparency["recommendation"])

    with card_right:
        borrower_peer = pd.DataFrame(
            [
                {"Label": "Borrower Health", "Score": transparency["health_score"]},
                {"Label": "Peer Benchmark", "Score": transparency["peer_score"]},
                {"Label": "Regional Stress x100", "Score": int(transparency["regional_stress_factor"] * 100)},
            ]
        )
        fig = px.bar(
            borrower_peer,
            x="Label",
            y="Score",
            color="Label",
            title="Borrower vs Context",
            text="Score",
        )
        fig.update_layout(showlegend=False, margin=dict(l=0, r=0, t=40, b=0))
        st.plotly_chart(style_figure(fig), use_container_width=True, theme=None)

    txns = transactions_df[transactions_df["borrower_id"] == borrower_id].sort_values("timestamp", ascending=False)
    st.markdown("### Transaction Summary")
    borrower_window_label = st.selectbox(
        "Transaction window",
        ["30 Days", "60 Days", "90 Days", "All Available"],
        index=1,
        key=f"borrower_window_{borrower_id}",
    )
    borrower_window_days = {"30 Days": 30, "60 Days": 60, "90 Days": 90, "All Available": 10000}[borrower_window_label]
    st.markdown(render_transaction_days_card(txns, borrower_window_days), unsafe_allow_html=True)

    st.markdown("### Payment Schedule")
    schedule_data = []
    for _, row in txns.iterrows():
        if pd.notnull(row["timestamp"]):
            date_str = row["timestamp"].strftime("%m/%d/%Y") if hasattr(row["timestamp"], "strftime") else str(row["timestamp"])
        else:
            date_str = ""
        schedule_data.append({
            "Payment Date": date_str,
            "Name": transparency["name"],
            "Payment Amount": f"Rs {row['amount']:,.2f}" if pd.notna(row['amount']) else "-",
            "Type": str(row["transaction_type"]).replace("_", " ").title(),
            "Status": "Paid" if str(row["status"]).upper() in ["COMPLETED", "SUCCESS", "PAID"] else str(row["status"]).title(),
            "Balance Left": f"Rs {row['balance_after']:,.2f}" if pd.notna(row['balance_after']) else "-"
        })
    schedule_df = pd.DataFrame(schedule_data)
    if not schedule_df.empty:
        render_glass_table(schedule_df, max_height=520)
    else:
        st.info("No payment history available.")


def render_borrower_knowledge_graph(borrower_id: str, detector, portfolio_df: pd.DataFrame) -> None:
    G_full = detector.get_networkx_graph()
    if not G_full or borrower_id not in G_full.nodes:
        st.info("Graph data not available for this borrower.")
        return

    import networkx as nx
    G = nx.ego_graph(G_full, borrower_id, radius=2)
    
    pos = nx.spring_layout(G, k=0.25, iterations=40, seed=42)
    
    edge_x = []
    edge_y = []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
    
    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=0.4, color='rgba(160, 160, 175, 0.5)'),
        hoverinfo='none',
        mode='lines'
    )

    node_x = []
    node_y = []
    node_text = []
    node_color = []
    node_size = []
    node_symbol = []
    node_line_width = []
    node_line_color = []
    
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        
        node_type = G.nodes[node].get("type", "unknown")
        
        if node == borrower_id:
            node_size.append(22)
            node_line_width.append(4)
            node_line_color.append('rgba(0,0,0,0.9)')
        else:
            node_line_width.append(1)
            node_line_color.append('rgba(255,255,255,0.8)')
            
        if node_type == "borrower":
            try:
                b_risk = portfolio_df.loc[portfolio_df["borrower_id"] == node, "risk_score"].values[0]
                b_name = portfolio_df.loc[portfolio_df["borrower_id"] == node, "name"].values[0]
            except:
                b_risk = 50
                b_name = node
            node_color.append(b_risk)
            if node != borrower_id:
                node_size.append(12)
            node_symbol.append('circle')
            h_text = "<b>(Selected) " if node == borrower_id else ""
            node_text.append(f"{h_text}Borrower: {b_name}<br>GNN Risk: {b_risk}")
        elif node_type == "scheme":
            node_color.append(30)
            if node != borrower_id: node_size.append(24)
            node_symbol.append('diamond')
            node_text.append(f"Scheme Hub<br>{str(node).replace('SCHEME::', '')}")
        elif node_type == "region":
            node_color.append(75)
            if node != borrower_id: node_size.append(28)
            node_symbol.append('square')
            node_text.append(f"Region Hub<br>{str(node).replace('REGION::', '')}")
        else:
            node_color.append(50)
            if node != borrower_id: node_size.append(20)
            node_symbol.append('star')
            node_text.append(f"Category Hub<br>{str(node).replace('CATEGORY::', '')}")

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers',
        hoverinfo='text',
        text=node_text,
        marker=dict(
            showscale=True,
            colorscale='YlOrRd',
            color=node_color,
            size=node_size,
            symbol=node_symbol,
            colorbar=dict(
                thickness=10,
                title='Embedded Risk'
            ),
            line=dict(width=node_line_width, color=node_line_color)
        )
    )

    fig = go.Figure(data=[edge_trace, node_trace],
        layout=go.Layout(
            showlegend=False,
            hovermode='closest',
            height=450,
            margin=dict(b=10,l=5,r=5,t=10),
            paper_bgcolor="rgba(255,255,255,0.45)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
    )
    
    fig.update_layout(
        margin=dict(l=16, r=16, t=16, b=16),
        paper_bgcolor="rgba(255, 255, 255, 0.45)"
    )

    st.plotly_chart(fig, use_container_width=True, theme=None)


def render_ego_network(borrower_id: str, detector) -> None:
    import networkx as nx
    import plotly.graph_objects as go
    
    G = detector.get_networkx_graph()
    if borrower_id not in G:
        st.warning("Borrower not found in the graph.")
        return
        
    ego = nx.ego_graph(G, borrower_id, radius=2)
    pos = nx.spring_layout(ego, seed=42)
    
    edge_x = []
    edge_y = []
    for edge in ego.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
        
    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=0.5, color='rgba(150, 150, 150, 0.5)'),
        hoverinfo='none',
        mode='lines'
    )
    
    node_x = []
    node_y = []
    node_color = []
    node_text = []
    node_size = []
    
    for node in ego.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        
        if node == borrower_id:
            color = '#3b82f6'  # Blue center
            size = 24
        elif str(node).startswith("SCHEME") or str(node).startswith("REGION") or str(node).startswith("CATEGORY"):
            color = '#9ca3af'  # Gray for attributes
            size = 12
        else:
            try:
                risk = detector.calculate_risk_score(node)
                if risk >= 70:
                    color = '#ef4444' # Red
                elif risk >= 45:
                    color = '#f59e0b' # Yellow
                else:
                    color = '#10b981' # Green
            except Exception:
                color = '#10b981'
            size = 16
            
        node_color.append(color)
        node_size.append(size)
        node_text.append(str(node))
        
    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers',
        hoverinfo='text',
        marker=dict(
            showscale=False,
            color=node_color,
            size=node_size,
            line=dict(width=1, color='white')
        ),
        text=node_text
    )
    
    fig = go.Figure(data=[edge_trace, node_trace],
                 layout=go.Layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    showlegend=False,
                    hovermode='closest',
                    margin=dict(b=0,l=0,r=0,t=0),
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                 )
    fig.update_layout(height=450)
    st.plotly_chart(fig, use_container_width=True, theme=None)

def render_explainability(borrower_id: str) -> None:
    import requests
    import plotly.graph_objects as go
    try:
        resp = requests.get(
            f"http://localhost:8000/explain/{borrower_id}",
            timeout=10
        )
        data = resp.json()
        
        if resp.status_code != 200:
            st.error("Could not load explainability data.")
            return

        contributions = data["feature_contributions"]
        top_driver    = data["top_driver"]
        summary       = data["explanation_summary"]

        st.markdown(
            f"""
            <div style="
                background: rgba(255,255,255,0.65);
                backdrop-filter: blur(16px);
                -webkit-backdrop-filter: blur(16px);
                border: 1px solid rgba(255,255,255,0.85);
                border-radius: 24px;
                padding: 28px 32px;
                margin-top: 24px;
                box-shadow: 0 16px 40px 
                    rgba(180,140,150,0.12);
            ">
                <div style="
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    margin-bottom: 20px;
                    padding-bottom: 16px;
                    border-bottom: 1px solid 
                        rgba(28,28,30,0.08);
                ">
                    <div style="
                        width: 40px; height: 40px;
                        background: linear-gradient(
                            135deg, #174229, #2c5e3f);
                        border-radius: 12px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-size: 1.2rem;
                    ">🔍</div>
                    <div>
                        <div style="font-weight:700; 
                            font-size:1.1rem; 
                            color:#1c1c1e;">
                            Explainable AI — Decision Breakdown
                        </div>
                        <div style="font-size:0.82rem; 
                            color:#636366;">
                            RBI SACHET Compliant · Feature 
                            Contribution Analysis
                        </div>
                    </div>
                    <div style="
                        margin-left: auto;
                        background: rgba(23,66,41,0.08);
                        border-radius: 999px;
                        padding: 6px 14px;
                        font-size: 0.8rem;
                        font-weight: 600;
                        color: #174229;
                    ">Explainable AI v1.0</div>
                </div>
                <p style="
                    margin: 0 0 20px 0;
                    color: #48484a;
                    font-size: 0.95rem;
                    line-height: 1.6;
                    padding: 12px 16px;
                    background: rgba(23,66,41,0.06);
                    border-radius: 12px;
                    border-left: 3px solid #174229;
                ">{summary}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Build horizontal bar chart
        features = list(contributions.keys())
        values   = list(contributions.values())

        # Colour each bar by contribution size
        bar_colors = []
        for v in values:
            if v >= 30:
                bar_colors.append("#ef4444")
            elif v >= 20:
                bar_colors.append("#f97316")
            elif v >= 10:
                bar_colors.append("#eab308")
            else:
                bar_colors.append("#22c55e")

        fig = go.Figure(go.Bar(
            x=values,
            y=features,
            orientation="h",
            marker_color=bar_colors,
            text=[f"{v:.1f}%" for v in values],
            textposition="outside",
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Contribution: %{x:.1f}%"
                "<extra></extra>"
            )
        ))

        fig.update_layout(
            title="Feature Contribution to Risk Score",
            xaxis_title="Contribution (%)",
            xaxis=dict(
                range=[0, max(values) * 1.3],
                showgrid=True,
                gridcolor="rgba(120,120,135,0.16)",
                zeroline=False,
                tickfont=dict(color="#3a3a3c"),
            ),
            yaxis=dict(
                autorange="reversed",
                tickfont=dict(
                    color="#1c1c1e", 
                    size=13
                ),
            ),
            height=380,
            margin=dict(l=16, r=60, t=48, b=32),
            paper_bgcolor="rgba(255,255,255,0.18)",
            plot_bgcolor="rgba(255,255,255,0.10)",
            font=dict(color="#1c1c1e"),
            showlegend=False,
        )

        st.plotly_chart(
            fig, use_container_width=True, theme=None
        )

        # Colour legend
        st.markdown(
            """
            <div style="display:flex; gap:16px; 
                flex-wrap:wrap; margin-top:8px;
                font-size:0.85rem;">
                <span style="display:flex; 
                    align-items:center; gap:6px;">
                    <span style="width:12px;height:12px;
                        border-radius:3px;
                        background:#ef4444;
                        display:inline-block;"></span>
                    <span style="color:#48484a;">
                        Major Driver (≥30%)
                    </span>
                </span>
                <span style="display:flex; 
                    align-items:center; gap:6px;">
                    <span style="width:12px;height:12px;
                        border-radius:3px;
                        background:#f97316;
                        display:inline-block;"></span>
                    <span style="color:#48484a;">
                        Significant (≥20%)
                    </span>
                </span>
                <span style="display:flex; 
                    align-items:center; gap:6px;">
                    <span style="width:12px;height:12px;
                        border-radius:3px;
                        background:#eab308;
                        display:inline-block;"></span>
                    <span style="color:#48484a;">
                        Moderate (≥10%)
                    </span>
                </span>
                <span style="display:flex; 
                    align-items:center; gap:6px;">
                    <span style="width:12px;height:12px;
                        border-radius:3px;
                        background:#22c55e;
                        display:inline-block;"></span>
                    <span style="color:#48484a;">
                        Minor Factor (&lt;10%)
                    </span>
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )

    except Exception as e:
        st.error(
            f"Explainability unavailable: {e}"
        )

def render_satark_recover_tab(filtered: pd.DataFrame, portfolio_df: pd.DataFrame, detector, repo) -> None:
    st.subheader("Satark-Recover: AI Risk Intelligence")
    
    borrower_options = filtered["borrower_id"].tolist() if not filtered.empty else portfolio_df["borrower_id"].tolist()
    selected_borrower = st.selectbox("Select borrower for AI Analysis", borrower_options, key="satark_recover_select")
    
    if not selected_borrower:
        return

    borrower_record = detector.analyze_borrower(selected_borrower).as_dict()
    profile_series = borrowers_df[borrowers_df["borrower_id"] == selected_borrower]
    if profile_series.empty:
        return
    borrower_profile = profile_series.iloc[0]
    
    st.markdown("---")
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"### Borrower Summary: {borrower_record['name']}")
        st.write(f"**Scheme:** {borrower_record['loan_scheme']} | **Region:** {borrower_record['region']}")
        st.write(f"**Loan Amount:** Rs {borrower_profile.loan_amount:,.0f}")
        st.write(f"**Final Risk Level:** {borrower_record['risk_level']}")
    
    with col2:
        st.metric("Behavioural Risk Score", borrower_record['risk_score'])
        st.metric("Peer Comparison", f"{borrower_record['peer_score']} (Baseline)")
        st.metric("Regional Stress", format(borrower_record['regional_stress_factor'], ".2f"))

    st.markdown("---")
    
    st.markdown("### Local Risk Exposure Network")
    st.caption("This network represents borrower risk propagation patterns used by the AI risk model.")
    render_ego_network(selected_borrower, detector)

    st.markdown("---")
    

    clicked_ai = st.button(
    "Run AI Risk Analysis",
    use_container_width=True,
    key="run_ai_analysis_btn"
    )
   
    st.markdown('</div>', unsafe_allow_html=True)

    if clicked_ai:
        import requests
        with st.spinner("Connecting to RiskNet AI..."):
            try:
                res = requests.get(f"http://localhost:8000/analyze/{selected_borrower}")
                res.raise_for_status()
                data = res.json()
                
                band = data.get("risk_band", "LOW")
                prob = data.get("risk_probability", 0.0) * 100
                action = data.get("recovery_action", "Monitor")
                signals = data.get("key_signals", {})
                
                band_colors = {
                    "CRITICAL": "#ef4444",
                    "HIGH": "#f97316",
                    "MODERATE": "#eab308",
                    "LOW": "#22c55e"
                }
                color = band_colors.get(band, "#22c55e")
                
                st.markdown("### RiskNet Analysis")
                st.markdown(
                    f'''
                    <div style="background: rgba(255,255,255,0.6); backdrop-filter: blur(16px); 
                                border: 1px solid rgba(255,255,255,0.9); border-radius: 24px; 
                                padding: 24px; box-shadow: 0 12px 28px rgba(180, 140, 150, 0.1); margin-bottom: 24px;">
                        <h4 style="margin: 0; color: #636366; font-size: 0.95rem; text-transform: uppercase;">Risk Band</h4>
                        <div style="font-size: 2.2rem; font-weight: 800; color: {color}; margin: 8px 0;">{band}</div>
                        <p style="margin: 0; font-size: 1.1rem; color: #1c1c1e;"><b>Probability:</b> {prob:.1f}%</p>
                        <p style="margin: 8px 0 0 0; font-size: 1.05rem; color: #48484a;"><b>Recommended Action:</b> {action}</p>
                    </div>
                    ''', 
                    unsafe_allow_html=True
                )
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Repayment Consistency", f"{signals['repayment_consistency']:.2f}")
                col2.metric("Peer Score", f"{signals['peer_score']:.0f}")
                col3.metric("Regional Stress", f"{signals['regional_stress']:.2f}")

                col4, col5, col6 = st.columns(3)
                col4.metric("EMI Miss Rate", f"{signals['txn_miss_rate']*100:.1f}%")
                col5.metric("Buffer Ratio", f"{signals['buffer_ratio']:.2f}")
                col6.metric("Days Past Due", f"{signals.get('days_past_due', 0)}")
                
                try:
                    narr_res = requests.get(f"http://localhost:8000/narrative/{selected_borrower}")
                    narr_res.raise_for_status()
                    narr_data = narr_res.json()
                    narrative_text = narr_data.get("narrative", "")
                    
                    st.markdown(
                        f"""
                        <div style="
                            background: rgba(255,255,255,0.65);
                            backdrop-filter: blur(16px);
                            -webkit-backdrop-filter: blur(16px);
                            border: 1px solid rgba(255,255,255,0.85);
                            border-radius: 24px;
                            padding: 28px 32px;
                            margin-top: 16px;
                            box-shadow: 0 16px 40px rgba(180,140,150,0.12);
                        ">
                            <div style="
                                display: flex;
                                align-items: center;
                                gap: 12px;
                                margin-bottom: 20px;
                                padding-bottom: 16px;
                                border-bottom: 1px solid rgba(28,28,30,0.08);
                            ">
                                <div style="
                                    width: 40px; height: 40px;
                                    background: linear-gradient(135deg, #ff5f2e, #e0287d);
                                    border-radius: 12px;
                                    display: flex; align-items: center;
                                    justify-content: center;
                                    font-size: 1.2rem;
                                ">🧠</div>
                                <div>
                                    <div style="font-weight:700; font-size:1.1rem; 
                                                color:#1c1c1e;">
                                        AI Risk Narrative
                                    </div>
                                    <div style="font-size:0.82rem; color:#636366;">
                                        Generated by SatarkSetu RiskNet Intelligence
                                    </div>
                                </div>
                                <div style="
                                    margin-left: auto;
                                    background: rgba(28,28,30,0.06);
                                    border-radius: 999px;
                                    padding: 6px 14px;
                                    font-size: 0.8rem;
                                    font-weight: 600;
                                    color: #48484a;
                                ">Model v1.0</div>
                            </div>
                            <div style="
                                font-size: 1rem;
                                line-height: 1.75;
                                color: #2c2c2e;
                                white-space: pre-wrap;
                            ">{narrative_text}</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                except Exception as e:
                    st.error(f"Failed to fetch narrative: {str(e)}")
                
                st.markdown("<br>", unsafe_allow_html=True)
                render_explainability(selected_borrower)

            except Exception as e:
                st.error(f"Failed to connect to RiskNet backend. Please ensure you are running: `uvicorn main:app --reload --port 8000`. Error: {str(e)}")

def render_contagion_simulator(
    portfolio_df: pd.DataFrame, 
    detector, 
    borrowers_df: pd.DataFrame
) -> None:
    
    st.markdown(
        """
        <div style="background: rgba(255,255,255,0.5);
            backdrop-filter: blur(16px);
            border: 1px solid rgba(255,255,255,0.8);
            border-radius: 24px;
            padding: 24px 28px;
            margin-bottom: 24px;">
            <h3 style="margin:0 0 8px 0; color:#1c1c1e;">
                Stress Contagion Simulator
            </h3>
            <p style="margin:0; color:#48484a;">
                Select a borrower and simulate their default. 
                See how risk propagates through the network 
                to connected borrowers in real time.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Borrower selector
    col1, col2 = st.columns([2, 1])
    with col1:
        selected = st.selectbox(
            "Select borrower to default",
            portfolio_df["borrower_id"].tolist(),
            format_func=lambda x: f"{x} — "
                f"{portfolio_df.loc[portfolio_df['borrower_id']==x, 'name'].values[0]} "
                f"({portfolio_df.loc[portfolio_df['borrower_id']==x, 'region'].values[0]})",
            key="contagion_borrower_select"
        )
    with col2:
        contagion_depth = st.slider(
            "Propagation Depth (hops)", 
            1, 3, 2, 
            key="contagion_depth"
        )

    if not selected:
        return

    # Get selected borrower info
    b_row = portfolio_df[
        portfolio_df["borrower_id"] == selected
    ].iloc[0]
    
    # Show selected borrower card
    st.markdown(
        f"""
        <div style="background: rgba(239,68,68,0.08);
            border: 1px solid rgba(239,68,68,0.25);
            border-radius: 16px;
            padding: 16px 20px;
            margin: 16px 0;
            display: flex;
            align-items: center;
            gap: 16px;">
            <div style="font-size:1.8rem;">⚠️</div>
            <div>
                <div style="font-weight:700; 
                            color:#b91c1c; 
                            font-size:1.05rem;">
                    Simulating Default: {b_row['name']}
                </div>
                <div style="color:#48484a; font-size:0.9rem;">
                    {b_row['region']} · {b_row['loan_scheme']} · 
                    Current Risk Score: {b_row['risk_score']}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Run simulation button


    clicked_contagion = st.button(
    "Run Contagion Simulation",
    use_container_width=True,
    key="run_contagion"
    )
    
    st.markdown('</div>', unsafe_allow_html=True)

    if clicked_contagion:
        with st.spinner("Simulating stress propagation..."):
            import networkx as nx
            import time

            G = detector.get_networkx_graph()
            
            if selected not in G:
                st.warning(
                    "Selected borrower not found in graph."
                )
                return

            # Get affected borrowers within N hops
            affected = {}
            for hop in range(1, contagion_depth + 1):
                neighbors = nx.ego_graph(
                    G, selected, radius=hop
                ).nodes()
                for node in neighbors:
                    if (node != selected and 
                        str(node).startswith("BORR_") and
                        node not in affected):
                        affected[node] = hop

            # Contagion decay — risk increase by hop distance
            # Hop 1 = 35% risk increase
            # Hop 2 = 18% risk increase  
            # Hop 3 = 8% risk increase
            decay = {1: 0.35, 2: 0.18, 3: 0.08}

            # Build before/after comparison
            results = []
            for borrower_id, hop in affected.items():
                b_data = portfolio_df[
                    portfolio_df["borrower_id"] == borrower_id
                ]
                if b_data.empty:
                    continue
                b = b_data.iloc[0]
                original_score = float(b["risk_score"])
                increase = decay.get(hop, 0.05)
                new_score = min(
                    100, 
                    original_score * (1 + increase)
                )
                delta = new_score - original_score

                def get_band(score):
                    if score >= 70: return "CRITICAL"
                    elif score >= 50: return "HIGH"
                    elif score >= 30: return "MODERATE"
                    else: return "LOW"

                results.append({
                    "borrower_id": borrower_id,
                    "name": b["name"],
                    "region": b["region"],
                    "hop_distance": hop,
                    "original_score": round(original_score, 1),
                    "simulated_score": round(new_score, 1),
                    "risk_increase": round(delta, 1),
                    "original_band": get_band(original_score),
                    "new_band": get_band(new_score),
                    "band_changed": (
                        get_band(original_score) != 
                        get_band(new_score)
                    )
                })

            results_df = pd.DataFrame(results)

            if results_df.empty:
                st.info(
                    "No connected borrowers found "
                    "within the selected depth."
                )
                return

            # Summary metrics
            st.markdown("### Contagion Impact Summary")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric(
                "Borrowers Affected", 
                len(results_df)
            )
            m2.metric(
                "Band Escalations",
                int(results_df["band_changed"].sum()),
                help="Borrowers whose risk band worsened"
            )
            m3.metric(
                "Avg Risk Increase",
                f"+{results_df['risk_increase'].mean():.1f}",
            )
            
            at_risk_exposure = borrowers_df[
                borrowers_df["borrower_id"].isin(
                    results_df["borrower_id"]
                )
            ]["outstanding_amount"].sum()
            m4.metric(
                "Exposed Loan Value",
                f"Rs {at_risk_exposure/1e7:.1f} Cr"
            )

            # Before vs After chart
            st.markdown("### Risk Score: Before vs After")
            
            fig = go.Figure()
            
            # Sort by risk increase
            chart_df = results_df.sort_values(
                "risk_increase", ascending=False
            ).head(20)
            
            fig.add_trace(go.Bar(
                name="Original Score",
                x=chart_df["name"],
                y=chart_df["original_score"],
                marker_color="rgba(100, 200, 150, 0.7)",
                text=chart_df["original_score"],
                textposition="outside"
            ))
            fig.add_trace(go.Bar(
                name="Simulated Score",
                x=chart_df["name"],
                y=chart_df["simulated_score"],
                marker_color="rgba(239, 68, 68, 0.7)",
                text=chart_df["simulated_score"],
                textposition="outside"
            ))
            
            fig.update_layout(
                barmode="group",
                bargap=0.3,
                xaxis_tickangle=-35,
                yaxis_title="Risk Score",
                yaxis=dict(range=[0, 110]),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02
                ),
                margin=dict(l=16, r=16, t=48, b=80),
                paper_bgcolor="rgba(255,255,255,0.18)",
                plot_bgcolor="rgba(255,255,255,0.10)",
                font=dict(color="#1c1c1e")
            )
            st.plotly_chart(
                fig, use_container_width=True, theme=None
            )

            # Affected borrowers table
            st.markdown("### Affected Borrowers Detail")
            
            display_results = results_df[[
                "name", "region", "hop_distance",
                "original_score", "simulated_score", 
                "risk_increase", "original_band", 
                "new_band"
            ]].copy()
            display_results.columns = [
                "Name", "Region", "Hop Distance",
                "Original Score", "Simulated Score",
                "Risk Increase", "Original Band", 
                "New Band"
            ]
            display_results = display_results.sort_values(
                "Risk Increase", ascending=False
            )
            
            render_glass_table(
                display_results, max_height=400
            )

            # Network visualization
            st.markdown("### Contagion Network Map")
            st.caption(
                "Red = defaulted borrower | "
                "Orange = hop 1 affected | "
                "Yellow = hop 2 affected | "
                "Green = unaffected"
            )
            
            ego = nx.ego_graph(
                G, selected, radius=contagion_depth
            )
            pos = nx.spring_layout(ego, seed=42, k=0.3)
            
            edge_x, edge_y = [], []
            for edge in ego.edges():
                x0, y0 = pos[edge[0]]
                x1, y1 = pos[edge[1]]
                edge_x.extend([x0, x1, None])
                edge_y.extend([y0, y1, None])
            
            node_x, node_y = [], []
            node_color, node_size, node_text = [], [], []
            
            affected_ids = set(affected.keys())
            
            for node in ego.nodes():
                x, y = pos[node]
                node_x.append(x)
                node_y.append(y)
                
                if node == selected:
                    node_color.append("#ef4444")
                    node_size.append(28)
                    node_text.append(
                        f"DEFAULTED: {node}"
                    )
                elif node in affected_ids:
                    hop = affected[node]
                    if hop == 1:
                        node_color.append("#f97316")
                    elif hop == 2:
                        node_color.append("#eab308")
                    else:
                        node_color.append("#84cc16")
                    node_size.append(18)
                    node_text.append(
                        f"{node} | Hop {hop}"
                    )
                else:
                    node_color.append("#22c55e")
                    node_size.append(12)
                    node_text.append(str(node))
            
            contagion_fig = go.Figure(
                data=[
                    go.Scatter(
                        x=edge_x, y=edge_y,
                        mode="lines",
                        line=dict(
                            width=0.5, 
                            color="rgba(150,150,150,0.4)"
                        ),
                        hoverinfo="none"
                    ),
                    go.Scatter(
                        x=node_x, y=node_y,
                        mode="markers",
                        marker=dict(
                            color=node_color,
                            size=node_size,
                            line=dict(
                                width=1, 
                                color="white"
                            )
                        ),
                        text=node_text,
                        hoverinfo="text"
                    )
                ],
                layout=go.Layout(
                    height=500,
                    showlegend=False,
                    hovermode="closest",
                    paper_bgcolor="rgba(255,255,255,0.4)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    margin=dict(b=0,l=0,r=0,t=0),
                    xaxis=dict(
                        showgrid=False, 
                        zeroline=False, 
                        showticklabels=False
                    ),
                    yaxis=dict(
                        showgrid=False, 
                        zeroline=False, 
                        showticklabels=False
                    )
                )
            )
            st.plotly_chart(
                contagion_fig, 
                use_container_width=True, 
                theme=None
            )

def render_regional_heatmap(
    regional_df: pd.DataFrame,
    portfolio_df: pd.DataFrame
) -> None:

    st.markdown(
        """
        <div style="background: rgba(255,255,255,0.5);
            backdrop-filter: blur(16px);
            border: 1px solid rgba(255,255,255,0.8);
            border-radius: 24px;
            padding: 24px 28px;
            margin-bottom: 24px;">
            <h3 style="margin:0 0 8px 0; color:#1c1c1e;">
                Regional Credit Stress Heatmap
            </h3>
            <p style="margin:0; color:#48484a;">
                NPA rate and economic stress index 
                across monitored regions. Darker = 
                higher stress.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Map toggle
    map_metric = st.radio(
        "Colour map by",
        ["NPA Rate", "Regional Stress Factor", 
         "Economic Stress Index"],
        horizontal=True,
        key="heatmap_metric"
    )

    metric_col = {
        "NPA Rate": "npa_rate",
        "Regional Stress Factor": "regional_stress_factor",
        "Economic Stress Index": "economic_stress_index"
    }[map_metric]

    # Merge portfolio counts into regional
    region_counts = portfolio_df.groupby(
        "region", as_index=False
    ).agg(
        borrower_count=("borrower_id", "count"),
        avg_risk=("risk_score", "mean"),
        high_risk_count=(
            "risk_score", 
            lambda x: (x >= 70).sum()
        )
    )
    
    map_df = regional_df.merge(
        region_counts, on="region", how="left"
    ).fillna(0)

    # Indian state name mapping
    # Our region names → Plotly India GeoJSON state names
    state_map = {
        "Jharkhand":   "Jharkhand",
        "West Bengal": "West Bengal",
        "Bihar":       "Bihar",
        "Odisha":      "Odisha",
        "Maharashtra": "Maharashtra",
        "Uttar Pradesh": "Uttar Pradesh",
        "Rajasthan":   "Rajasthan",
        "Madhya Pradesh": "Madhya Pradesh",
        "Gujarat":     "Gujarat",
        "Tamil Nadu":  "Tamil Nadu",
        "Karnataka":   "Karnataka",
        "Andhra Pradesh": "Andhra Pradesh",
        "Telangana":   "Telangana",
        "Kerala":      "Kerala",
        "Punjab":      "Punjab",
        "Haryana":     "Haryana",
        "Delhi":       "NCT of Delhi",
        "Assam":       "Assam",
        "Chhattisgarh": "Chhattisgarh",
        "Uttarakhand": "Uttarakhand",
        "Himachal Pradesh": "Himachal Pradesh",
        "Jammu and Kashmir": "Jammu & Kashmir",
        "Goa":         "Goa",
        "Tripura":     "Tripura",
        "Meghalaya":   "Meghalaya",
        "Manipur":     "Manipur",
        "Nagaland":    "Nagaland",
        "Sikkim":      "Sikkim"
    }
    
    map_df["state_name"] = map_df["region"].map(
        state_map
    ).fillna(map_df["region"])

    # Build choropleth using plotly
    import requests as req
    
    # Fetch India GeoJSON
    geojson_url = (
        "https://raw.githubusercontent.com/"
        "Subhash9325/GeoJson-Data-of-Indian-States/"
        "master/Indian_States"
    )
    
    try:
        geojson_resp = req.get(geojson_url, timeout=5)
        india_geojson = geojson_resp.json()
        
        fig = px.choropleth(
            map_df,
            geojson=india_geojson,
            locations="state_name",
            featureidkey="properties.NAME_1",
            color=metric_col,
            hover_name="region",
            hover_data={
                "npa_rate": ":.1f",
                "regional_stress_factor": ":.2f",
                "borrower_count": True,
                "avg_risk": ":.1f",
                "high_risk_count": True,
                "state_name": False,
            },
            color_continuous_scale=[
                [0.0, "#d4edda"],
                [0.3, "#ffeaa7"],
                [0.6, "#f97316"],
                [1.0, "#ef4444"],
            ],
            labels={
                "npa_rate": "NPA Rate (%)",
                "regional_stress_factor": "Stress Factor",
                "economic_stress_index": "Stress Index",
                "borrower_count": "Borrowers",
                "avg_risk": "Avg Risk Score",
                "high_risk_count": "High Risk Count",
            },
            title=f"India — {map_metric} by Region"
        )
        
        fig.update_geos(
            fitbounds="locations",
            visible=False,
            bgcolor="rgba(0,0,0,0)"
        )
        
        fig.update_layout(
            height=520,
            margin=dict(l=0, r=0, t=48, b=0),
            paper_bgcolor="rgba(255,255,255,0.18)",
            font=dict(color="#1c1c1e"),
            coloraxis_colorbar=dict(
                title=map_metric,
                thickness=14,
                len=0.6,
                bgcolor="rgba(255,255,255,0.6)",
                bordercolor="rgba(255,255,255,0.8)",
                borderwidth=1,
            ),
            geo=dict(
                bgcolor="rgba(0,0,0,0)"
            )
        )
        
        st.plotly_chart(
            fig, use_container_width=True, theme=None
        )
        
    except Exception:
        # Fallback — bar chart if GeoJSON fails
        st.info(
            "Map requires internet connection. "
            "Showing bar chart instead."
        )
        bar_fig = px.bar(
            map_df.sort_values(metric_col, ascending=False),
            x="region",
            y=metric_col,
            color=metric_col,
            color_continuous_scale=[
                [0.0, "#d4edda"],
                [0.5, "#f97316"],
                [1.0, "#ef4444"],
            ],
            text=metric_col,
            title=f"{map_metric} by Region"
        )
        bar_fig.update_traces(texttemplate="%{text:.2f}")
        bar_fig.update_layout(
            paper_bgcolor="rgba(255,255,255,0.18)",
            plot_bgcolor="rgba(255,255,255,0.10)",
            font=dict(color="#1c1c1e"),
            margin=dict(l=16, r=16, t=48, b=48),
            showlegend=False
        )
        st.plotly_chart(
            bar_fig, use_container_width=True, theme=None
        )

    cols = st.columns(len(map_df))
    # Regional stats cards below map
    st.markdown("### Regional Risk Breakdown")
    
    sorted_regions = map_df.sort_values(
        "npa_rate", ascending=False
    ).reset_index(drop=True)

    # Render in rows of 4 cards each
    cards_per_row = 4
    for row_start in range(
        0, len(sorted_regions), cards_per_row
    ):
        row_data = sorted_regions.iloc[
            row_start:row_start + cards_per_row
        ]
        cols = st.columns(cards_per_row)
        for i, (_, row) in enumerate(
            row_data.iterrows()
        ):
            stress = float(
                row["regional_stress_factor"]
            )
            if stress >= 0.7:
                color = "#ef4444"
                label = "High Stress"
                bg    = "rgba(239,68,68,0.06)"
            elif stress >= 0.5:
                color = "#f97316"
                label = "Moderate"
                bg    = "rgba(249,115,22,0.06)"
            else:
                color = "#22c55e"
                label = "Stable"
                bg    = "rgba(34,197,94,0.06)"

            cols[i].markdown(
                f"""
                <div style="
                    background: rgba(255,255,255,0.7);
                    border-radius: 20px;
                    padding: 20px 16px;
                    border-left: 4px solid {color};
                    border: 1px solid 
                        rgba(255,255,255,0.85);
                    border-left: 4px solid {color};
                    margin-bottom: 12px;
                    box-shadow: 0 8px 24px 
                        rgba(180,140,150,0.08);
                ">
                    <div style="
                        font-weight: 700;
                        font-size: 0.95rem;
                        color: #1c1c1e;
                        margin-bottom: 10px;
                        white-space: nowrap;
                        overflow: hidden;
                        text-overflow: ellipsis;
                    ">{row['region']}</div>
                    <div style="
                        font-size: 1.8rem;
                        font-weight: 800;
                        color: {color};
                        line-height: 1;
                        margin-bottom: 4px;
                    ">{row['npa_rate']:.1f}%</div>
                    <div style="
                        font-size: 0.78rem;
                        color: #636366;
                        margin-bottom: 8px;
                    ">NPA Rate</div>
                    <div style="
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        padding-top: 8px;
                        border-top: 1px solid 
                            rgba(28,28,30,0.06);
                    ">
                        <span style="
                            font-size: 0.78rem;
                            font-weight: 600;
                            color: {color};
                            background: {bg};
                            padding: 3px 8px;
                            border-radius: 999px;
                        ">{label}</span>
                        <span style="
                            font-size: 0.78rem;
                            color: #636366;
                        ">
                            {int(row.get(
                                'borrower_count', 0
                            ))} borrowers
                        </span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        st.markdown(
            "<div style='margin-bottom:4px'></div>",
            unsafe_allow_html=True
        )

def render_admin_dashboard() -> None:
    admin_name = st.session_state.get("admin_username", "Admin").title()
    
    top_left, top_right = st.columns([8, 1])
    with top_right:
        if st.button("Logout", key="admin_logout_top", use_container_width=True):
            logout()

    st.markdown(f"<h2 style='margin-bottom: 24px;'>Hello, {escape(admin_name)} 👋</h2>", unsafe_allow_html=True)

    portfolio_df = build_portfolio_df(
        borrowers_df, transactions_df, regional_df
    )
    summary = detector.portfolio_summary()
    clusters = detector.detect_stress_clusters()

    # Default filtered — used by all tabs
    risk_floor = 45
    filtered = portfolio_df[portfolio_df["risk_score"] >= risk_floor].copy()
    metric_cols = st.columns(4)
    metric_cols[0].metric("Borrowers", f"{summary['total_borrowers']:,}")
    metric_cols[1].metric("Avg Health Score", summary["average_health"])
    metric_cols[2].metric("High Risk Borrowers", summary["high_risk_borrowers"])
    metric_cols[3].metric("Regional Hotspots", len(clusters))

    overview_tab, borrower_tab, cohort_tab, recover_tab, \
    contagion_tab = st.tabs(
        ["Portfolio Overview", "Borrower Explorer", 
         "Context & Cohorts", "Satark-Recover AI",
         "Contagion Simulator"]
    )

    with overview_tab:
        st.markdown("#### Portfolio Filters")
        filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)
        with filter_col1:
            risk_floor = st.slider("Min Risk Score", 0, 100, 45, 5)
        with filter_col2:
            region_filter = st.selectbox("Region", ["All"] + sorted(portfolio_df["region"].unique().tolist()))
        with filter_col3:
            scheme_filter = st.selectbox("Loan Scheme", ["All"] + sorted(portfolio_df["loan_scheme"].unique().tolist()))
        with filter_col4:
            status_filter = st.selectbox("Status", ["All", "ACTIVE", "SUPPORT_REQUIRED", "RECOVERING", "WATCHLIST"])
        
        # Apply filters
        filtered = portfolio_df.copy()
        filtered = filtered[filtered["risk_score"] >= risk_floor]
        if region_filter != "All":
            filtered = filtered[filtered["region"] == region_filter]
        if scheme_filter != "All":
            filtered = filtered[filtered["loan_scheme"] == scheme_filter]
        if status_filter != "All":
            filtered = filtered[filtered["status"] == status_filter]
            
        st.subheader("Borrowers Requiring Attention")
        display_cols = ["borrower_id", "name", "loan_scheme", "region", "risk_score", "health_score", "risk_level", "status"]
        render_glass_table(
            filtered[display_cols].sort_values(["risk_score", "health_score"], ascending=[False, True]).head(40),
            max_height=520,
        )

        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("AI Risk Band Distribution")
        try:
            import requests
            res = requests.get("http://localhost:8000/portfolio/summary")
            if res.status_code == 200:
                summary_data = res.json()
                counts = summary_data.get("band_counts", {})
                
                st.markdown(
                    f'''
                    <div style="background: rgba(255,255,255,0.6); backdrop-filter: blur(16px); 
                                border: 1px solid rgba(255,255,255,0.9); border-radius: 24px; 
                                padding: 24px; box-shadow: 0 12px 28px rgba(180, 140, 150, 0.1); margin-bottom: 24px;">
                        <h4 style="margin: 0; color: #636366; font-size: 1.05rem;">Total At-Risk Exposure</h4>
                        <div style="font-size: 2.5rem; font-weight: 800; color: #ef4444; margin-top: 8px;">Rs {summary_data.get('at_risk_exposure', 0):,.2f}</div>
                    </div>
                    ''', 
                    unsafe_allow_html=True
                )
                
                rc1, rc2, rc3, rc4 = st.columns(4)
                rc1.metric("CRITICAL", counts.get("CRITICAL", 0))
                rc2.metric("HIGH", counts.get("HIGH", 0))
                rc3.metric("MODERATE", counts.get("MODERATE", 0))
                rc4.metric("LOW", counts.get("LOW", 0))
            else:
                st.warning("Could not load backend portfolio summary.")
        except Exception as e:
            st.error(f"Failed to connect to RiskNet backend `uvicorn main:app --reload --port 8000`. Error: {str(e)}")
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("Risk by Region")
        risk_by_region = (
            filtered.groupby("region", as_index=False)
            .agg(average_risk=("risk_score", "mean"), average_health=("health_score", "mean"))
            .sort_values("average_risk", ascending=False)
        )
        if not risk_by_region.empty:
            import plotly.graph_objects as go
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=risk_by_region["region"],
                y=[100] * len(risk_by_region),
                marker_color='rgba(200, 200, 205, 0.25)',
                hoverinfo='skip',
                showlegend=False
            ))
            
            fig.add_trace(go.Bar(
                x=risk_by_region["region"],
                y=risk_by_region["average_risk"],
                marker=dict(
                    color=risk_by_region["average_risk"],
                    colorscale="YlOrRd",
                    colorbar=dict(title="Avg Risk", thickness=15)
                ),
                text=[f"{val:.1f}" for val in risk_by_region["average_risk"]],
                textposition='outside',
                showlegend=False,
                name='Risk'
            ))
            
            fig.update_layout(
                barmode='overlay',
                bargap=0.4,
                yaxis_title="Average Risk",
                xaxis_title="Region",
                yaxis=dict(showgrid=False, zeroline=False, range=[0, 110]),
                xaxis=dict(showgrid=False),
                margin=dict(l=16, r=16, t=32, b=44)
            )
            
            # Safely attempt to add Dribbble-style rounded corners
            try:
                fig.update_traces(marker_cornerradius="30%")
            except Exception:
                pass
            
            avg_risk = risk_by_region["average_risk"].mean() if not risk_by_region["average_risk"].empty else 0
            if avg_risk > 0:
                fig.add_hline(y=avg_risk, line_dash="dot", line_color="rgba(0,0,0,0.3)")
                
            st.plotly_chart(style_figure(fig), use_container_width=True, theme=None)

        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("Loan Scheme Mix")
        scheme_mix = filtered.groupby("loan_scheme", as_index=False).size()
        if not scheme_mix.empty:
            fig = px.pie(scheme_mix, names="loan_scheme", values="size", hole=0.45)
            fig.update_layout(
                margin=dict(l=16, r=16, t=32, b=20),
                paper_bgcolor="rgba(255,255,255,0.18)",
                font=dict(color="#1c1c1e"),
                legend=dict(
                    bgcolor="rgba(255,255,255,0.16)",
                    bordercolor="rgba(255,255,255,0.35)",
                    borderwidth=1,
                ),
            )
            st.plotly_chart(fig, use_container_width=True, theme=None)

    with borrower_tab:
        st.subheader("Borrower Drilldown")
        borrower_options = filtered["borrower_id"].tolist() if not filtered.empty else portfolio_df["borrower_id"].tolist()
        selected_borrower = st.selectbox("Select borrower", borrower_options)
        borrower_record = detector.analyze_borrower(selected_borrower).as_dict()
        borrower_profile = borrowers_df[borrowers_df["borrower_id"] == selected_borrower].iloc[0]
        borrower_state = repo.get_borrower(selected_borrower) or repo.ensure_borrower(selected_borrower, borrower_record["name"])

        top_left, top_right = st.columns([1.2, 1])
        with top_left:
            st.markdown(f"### {borrower_record['name']}")
            st.write(f"Borrower ID: `{selected_borrower}`")
            st.write(f"Scheme: `{borrower_record['loan_scheme']}`")
            st.write(f"Region: `{borrower_record['region']}`")
            st.write(f"Current Status: `{borrower_state.get('status', 'ACTIVE')}`")
            st.write(borrower_record["recommendation"])

            button_cols = st.columns(2)
            if button_cols[0].button("Mark Support Required", use_container_width=True):
                repo.set_status(selected_borrower, "SUPPORT_REQUIRED", "Dashboard intervention recommendation", "dashboard")
                st.success("Borrower successfully marked as Support Required.")
            if button_cols[1].button("Mark Recovering", use_container_width=True):
                repo.set_status(selected_borrower, "RECOVERING", "Borrower moved to recovery monitoring", "dashboard")
                st.success("Borrower successfully marked as Recovering.")

        with top_right:
            metric_a, metric_b, metric_c = st.columns(3)
            metric_a.metric("Risk Score", borrower_record["risk_score"])
            metric_b.metric("Health Score", borrower_record["health_score"])
            metric_c.metric("Peer Score", borrower_record["peer_score"])
            st.markdown(render_segmented_health_bar(borrower_record["health_score"], "Borrower Health"), unsafe_allow_html=True)

        flag_cols = st.columns(2)
        with flag_cols[0]:
            st.markdown("#### Behavioral Flags")
            flags = borrower_record["behavioral_flags"] or ["no_major_behavioral_flags"]
            html = "".join([f'<div class="flag-pill">{f.replace("_", " ").title()}</div>' for f in flags])
            st.markdown(html, unsafe_allow_html=True)
        with flag_cols[1]:
            st.markdown("#### Contextual Flags")
            flags = borrower_record["contextual_flags"] or ["no_major_contextual_flags"]
            html = "".join([f'<div class="flag-pill">{f.replace("_", " ").title()}</div>' for f in flags])
            st.markdown(html, unsafe_allow_html=True)

        txns = transactions_df[transactions_df["borrower_id"] == selected_borrower].sort_values("timestamp")
        
        emi_txns = txns[txns["transaction_type"] == "EMI_PAYMENT"].copy()
        if not emi_txns.empty:
            import plotly.graph_objects as go
            max_amt = emi_txns["amount"].max() * 1.2 if not emi_txns["amount"].empty else 5000
            txn_chart = go.Figure()
            
            txn_chart.add_trace(go.Bar(
                x=emi_txns["timestamp"].astype(str),
                y=[max_amt] * len(emi_txns),
                marker_color='rgba(200, 200, 205, 0.25)',
                hoverinfo='skip',
                showlegend=False
            ))
            
            txn_chart.add_trace(go.Bar(
                x=emi_txns["timestamp"].astype(str),
                y=emi_txns["amount"],
                marker_color='#FF5F2E',
                text=emi_txns["amount"],
                texttemplate='Rs %{text:,.0f}',
                textposition='outside',
                showlegend=False,
                name='Paid'
            ))
            
            txn_chart.update_layout(
                title="Borrower EMI Payment History",
                barmode='overlay',
                bargap=0.45,
                yaxis_title="Amount Paid (Rs)",
                xaxis_title="Payment Date",
                yaxis=dict(showgrid=False, zeroline=False),
                xaxis=dict(showgrid=False)
            )
            
            try:
                txn_chart.update_traces(marker_cornerradius="30%")
            except Exception:
                pass
            
            avg_emi = emi_txns["amount"].mean() if not emi_txns["amount"].empty else 0
            if avg_emi > 0:
                txn_chart.add_hline(y=avg_emi, line_dash="dot", line_color="rgba(0,0,0,0.3)")
        else:
            txn_chart = px.line(
                txns,
                x="timestamp",
                y="balance_after",
                color="transaction_type",
                markers=True,
                title="Recent Borrower Cash-Flow Trail",
            )
        txn_chart.update_layout(margin=dict(l=16, r=16, t=56, b=64))
        st.plotly_chart(style_figure(txn_chart), use_container_width=True, theme=None)

        details = pd.DataFrame(
            [
                {"Metric": "Loan Amount", "Value": f"Rs {borrower_profile.loan_amount:,.0f}"},
                {"Metric": "Outstanding Amount", "Value": f"Rs {borrower_profile.outstanding_amount:,.0f}"},
                {"Metric": "EMI Amount", "Value": f"Rs {borrower_profile.emi_amount:,.0f}"},
                {"Metric": "Days Past Due", "Value": int(borrower_profile.days_past_due)},
                {"Metric": "Regional Stress Factor", "Value": borrower_record["regional_stress_factor"]},
            ]
        )
        render_glass_table(details)

        st.markdown("### Transaction Summary")
        admin_window_label = st.selectbox(
            "Transaction window",
            ["30 Days", "60 Days", "90 Days", "All Available"],
            index=1,
            key=f"admin_window_{selected_borrower}",
        )
        admin_window_days = {"30 Days": 30, "60 Days": 60, "90 Days": 90, "All Available": 10000}[admin_window_label]
        st.markdown(render_transaction_days_card(txns, admin_window_days), unsafe_allow_html=True)

        st.markdown("### Payment Schedule")
        admin_schedule_data = []
        for _, row in txns.sort_values("timestamp", ascending=False).iterrows():
            if pd.notnull(row["timestamp"]):
                date_str = row["timestamp"].strftime("%m/%d/%Y") if hasattr(row["timestamp"], "strftime") else str(row["timestamp"])
            else:
                date_str = ""
            admin_schedule_data.append({
                "Payment Date": date_str,
                "Name": borrower_record["name"],
                "Payment Amount": f"Rs {row['amount']:,.2f}" if pd.notna(row['amount']) else "-",
                "Type": str(row["transaction_type"]).replace("_", " ").title(),
                "Status": "Paid" if str(row["status"]).upper() in ["COMPLETED", "SUCCESS", "PAID"] else str(row["status"]).title(),
                "Balance Left": f"Rs {row['balance_after']:,.2f}" if pd.notna(row['balance_after']) else "-"
            })
        admin_schedule_df = pd.DataFrame(admin_schedule_data)
        if not admin_schedule_df.empty:
            render_glass_table(admin_schedule_df, max_height=520)
        else:
            st.info("No payment history available.")

        st.markdown("<br><div style='font-size: 1.75rem; font-weight: 700; color: #1c1c1e;'>Local Knowledge Graph</div>", unsafe_allow_html=True)
        st.markdown("This live ego-graph visualizes risk contagion within a 2-hop radius around the selected borrower.")
        render_borrower_knowledge_graph(selected_borrower, detector, filtered)

    with cohort_tab:
        render_regional_heatmap(regional_df, portfolio_df)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("Peer Benchmarking and Regional Context")
        peer_view = (
            filtered.groupby(["loan_scheme", "region"], as_index=False)
            .agg(average_risk=("risk_score", "mean"), average_health=("health_score", "mean"), borrowers=("borrower_id", "count"))
            .sort_values("average_risk", ascending=False)
        )
        render_glass_table(peer_view, max_height=420)

        st.markdown("<br>", unsafe_allow_html=True)
        regional_chart = px.scatter(
            regional_df,
            x="regional_stress_factor",
            y="peer_health_baseline",
            size="npa_rate",
            color="region",
            hover_name="region",
            title="Regional Stress vs Peer Baseline",
        )
        regional_chart.update_layout(margin=dict(l=16, r=16, t=56, b=64))
        st.plotly_chart(style_figure(regional_chart), use_container_width=True, theme=None)


    with recover_tab:
        render_satark_recover_tab(filtered, portfolio_df, detector, repo)

    with contagion_tab:
        render_contagion_simulator(
            portfolio_df, detector, borrowers_df
        )


def render_landing_page() -> None:
    # Optional image encoding for logo-2.png
    img_html = ""
    try:
        import base64
        with open("logo_transparent.png", "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode()
        img_html = f"data:image/png;base64,{encoded_string}"
    except Exception:
        pass

    # Top Navigation
    nav_left, nav_right = st.columns([3, 1.2])
    with nav_right:
        st.markdown("<br>", unsafe_allow_html=True)
        btn1, btn2 = st.columns(2)
        if btn1.button("Admin Log In", use_container_width=True):
            st.session_state.view = "admin_login"
            st.rerun()
        if btn2.button("Borrowers", use_container_width=True):
            st.session_state.view = "borrower_login"
            st.rerun()

    # 1. Hero Section
    st.markdown(
        f"""
        <div class="landing-hero">
            <div class="landing-copy">
                <h1>SATARK SETU</h1>
                <p class="subtext">
                    SatarkSetu is proud to present the inaugural risk intelligence protocol — 
                    a high-stakes behavioral analysis engine bringing together the most talented 
                    investigators across the region to foster financial inclusivity.
                </p>
                <div class="landing-metrics">
                    <div class="metric-box">
                        <h3>10k+</h3>
                        <p>Borrowers Monitored</p>
                    </div>
                    <div class="metric-box">
                        <h3>45+</h3>
                        <p>Regions Analyzed</p>
                    </div>
                    <div class="metric-box">
                        <h3>GNN</h3>
                        <p>Live Risk Engine</p>
                    </div>
                </div>
            </div>
            <div class="landing-art" style="padding: 40px;">
                <img src="{img_html}" alt="Satark Setu Hero Art" style="width: 100%; max-width: 500px; filter: drop-shadow(0 30px 50px rgba(0,0,0,0.15)); border-radius: 40px; margin-top: -60px;" />
            </div>
        </div>
        """, unsafe_allow_html=True
    )
    
    # 3. About Section
    st.markdown('<div class="about-section">', unsafe_allow_html=True)
    a_left, a_right = st.columns([1, 1.2])
    with a_left:
        st.markdown(
            """
            <div class="about-mini-title">WHO WE ARE</div>
            <div class="about-header">ABOUT<br>SATARKSETU</div>
            <p class="about-text">
                SatarkSetu builds world-class financial infrastructure and the 
                intelligent technology to manage it. From local schemes to 
                professional scouting, we bridge the gap between raw data 
                and real opportunity.
            </p>
            <br>
            """, unsafe_allow_html=True
        )
    with a_right:
        st.markdown(
            """
            <div class="staggered-grid">
                <div class="staggered-item" style="background: linear-gradient(135deg, #174229 0%, #2c5e3f 100%); color: white; margin-top: 20px;">
                    Intelligent Technology.
                </div>
                <div class="staggered-item" style="background: rgba(255,255,255,0.8);">
                    Real Opportunity.
                </div>
                <div class="staggered-item" style="background: rgba(255,255,255,0.8); margin-top: 20px;">
                    Graph Neural Networks
                </div>
                <div class="staggered-item" style="background: linear-gradient(135deg, #ff9933 0%, #d67a20 100%); color: white;">
                    Financial Inclusion.
                </div>
            </div>
            """, unsafe_allow_html=True
        )
    st.markdown('</div>', unsafe_allow_html=True)

    # 2. Mission Row
    st.markdown('<div class="mission-row">', unsafe_allow_html=True)
    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(
            """
            <div class="mission-card">
                <div class="mission-number">01</div>
                <h3>The Mission</h3>
                <p>SatarkSetu is proud to present intelligent risk monitoring, a high-stakes solution that reflects our core commitment to fostering competitive lending and creating unforgettable experiences for banks of every size.</p>
            </div>
            """, unsafe_allow_html=True
        )
    with m2:
        st.markdown(
            """
            <div class="mission-card">
                <div class="mission-number">02</div>
                <h3>The Engine</h3>
                <p>This is your chance to come play, compete, and own the spotlight. Whether you are a seasoned analyst or a newcomer looking to test your mettle, SatarkSetu delivers professionally organized matches paired with exciting algorithms.</p>
            </div>
            """, unsafe_allow_html=True
        )
    with m3:
        st.markdown(
            """
            <div class="mission-card">
                <div class="mission-number">03</div>
                <h3>The Community</h3>
                <p>Join a community that rewards your talent and become part of something bigger — where passion for fair financial access meets opportunity, competition, and shared growth on and off the ledger.</p>
            </div>
            """, unsafe_allow_html=True
        )
    st.markdown('</div>', unsafe_allow_html=True)



def render_login_page(mode: str = "admin") -> None:

    is_admin = mode == "admin"
    badge_label = "Admin portal" if is_admin else "Borrower portal"
    heading = "Manage your<br>portfolio." if is_admin else "Manage your<br>loans."
    subtext = (
        "Intelligent borrower monitoring, regional stress analysis, and contextual recovery intelligence."
        if is_admin
        else "View your repayment schedule, health score, and personalised recovery guidance."
    )
    eyebrow = "Admin access" if is_admin else "Borrower access"
    subtitle = (
        "Sign in to access the SatarkSetu dashboard."
        if is_admin
        else "Sign in with your Borrower ID to continue."
    )
    id_label = "Username" if is_admin else "Borrower ID"
    id_placeholder = "Enter admin username" if is_admin else "e.g. B00042"
    back_key = "admin_back" if is_admin else "borrower_back"
    form_key = "admin_login_form" if is_admin else "borrower_login_form"

    st.markdown(
        """
        <style>
        div[data-testid="stForm"] {
            background: rgba(255,255,255,0.92) !important;
            border-radius: 32px !important;
            padding: 40px 44px !important;
            border: 1px solid rgba(255,255,255,0.95) !important;
            box-shadow: 0 24px 48px rgba(180,140,150,0.14) !important;
            margin-top: 0 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    left_col, right_col = st.columns(2)

    with left_col:
        st.markdown(
            f"""
            <div style="
                background: linear-gradient(135deg, #fadce4 0%, #f3d1df 50%, #ebd4de 100%);
                border: 1px solid rgba(255,255,255,0.6);
                border-radius: 32px;
                padding: 48px 44px;
                min-height: 540px;
                display: flex;
                flex-direction: column;
                justify-content: flex-end;
                position: relative;
                overflow: hidden;
                box-shadow: 0 24px 48px rgba(180,140,150,0.18);
            ">
                <div style="position:absolute;width:340px;height:340px;border-radius:50%;background:rgba(255,99,132,0.08);top:-80px;right:-80px;"></div>
                <div style="position:absolute;width:220px;height:220px;border-radius:50%;background:rgba(255,153,51,0.07);bottom:60px;left:-60px;"></div>
                <div style="
                    display:inline-flex;align-items:center;gap:7px;
                    background:rgba(255,255,255,0.38);
                    border:1px solid rgba(255,255,255,0.6);
                    border-radius:999px;padding:7px 16px;
                    font-size:11px;font-weight:700;letter-spacing:1.4px;
                    text-transform:uppercase;color:#3a3a3c;
                    margin-bottom:30px;width:fit-content;position:relative;z-index:1;
                ">
                    <span style="width:7px;height:7px;border-radius:50%;background:linear-gradient(135deg,#ff5f2e,#e0287d);display:inline-block;"></span>
                    {escape(badge_label)}
                </div>
                <h2 style="font-size:2.8rem;font-weight:800;line-height:1.05;letter-spacing:-2px;color:#1c1c1e;margin-bottom:16px;position:relative;z-index:1;">{heading}</h2>
                <p style="font-size:0.95rem;color:#48484a;line-height:1.6;max-width:290px;font-weight:500;position:relative;z-index:1;border-left:3px solid rgba(224,40,125,0.35);padding-left:14px;margin-bottom:0;">{escape(subtext)}</p>
                <div style="display:flex;gap:28px;margin-top:36px;padding-top:28px;border-top:1px solid rgba(28,28,30,0.1);position:relative;z-index:1;">
                    <div>
                        <div style="font-size:1.6rem;font-weight:800;color:#1c1c1e;letter-spacing:-1px;margin-bottom:2px;">10k+</div>
                        <div style="font-size:0.72rem;text-transform:uppercase;letter-spacing:1.2px;color:#636366;font-weight:700;">Borrowers</div>
                    </div>
                    <div>
                        <div style="font-size:1.6rem;font-weight:800;color:#1c1c1e;letter-spacing:-1px;margin-bottom:2px;">45+</div>
                        <div style="font-size:0.72rem;text-transform:uppercase;letter-spacing:1.2px;color:#636366;font-weight:700;">Regions</div>
                    </div>
                    <div>
                        <div style="font-size:1.6rem;font-weight:800;color:#1c1c1e;letter-spacing:-1px;margin-bottom:2px;">GNN</div>
                        <div style="font-size:0.72rem;text-transform:uppercase;letter-spacing:1.2px;color:#636366;font-weight:700;">Risk engine</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right_col:
        with st.form(form_key, border=False):
            st.markdown(
                f"""
                <div style="margin-bottom:28px;">
                    <span style="font-size:11px;font-weight:700;letter-spacing:2px;text-transform:uppercase;background:linear-gradient(90deg,#ff5f2e,#e0287d);-webkit-background-clip:text;-webkit-text-fill-color:transparent;display:block;margin-bottom:12px;">{escape(eyebrow)}</span>
                    <h3 style="font-size:2.2rem;font-weight:800;letter-spacing:-1.5px;color:#1c1c1e;margin-bottom:8px;line-height:1.1;">Welcome back</h3>
                    <p style="font-size:0.9rem;color:#636366;margin-bottom:0;line-height:1.5;font-weight:500;">{escape(subtitle)}</p>
                    <div style="height:1px;background:rgba(28,28,30,0.08);margin-top:24px;"></div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(f"<p style='font-size:0.85rem;font-weight:600;color:#1c1c1e;margin-bottom:4px;'>{id_label}</p>", unsafe_allow_html=True)
            identifier = st.text_input("", placeholder=id_placeholder, label_visibility="collapsed")

            st.markdown("<p style='font-size:0.85rem;font-weight:600;color:#1c1c1e;margin-bottom:4px;'>Password</p>", unsafe_allow_html=True)
            password = st.text_input("", type="password", placeholder="Enter your password", label_visibility="collapsed")
            st.markdown(
                "<p style='font-size:0.83rem;color:#e0287d;margin-top:-10px;margin-bottom:24px;font-weight:600;cursor:pointer;text-align:right;'>Forgot password?</p>",
                unsafe_allow_html=True,
            )
            submitted = st.form_submit_button("Sign in →", use_container_width=True, type="primary")

        if st.button("← Back to website", key=back_key):
            st.session_state.view = "landing"
            st.rerun()

    if submitted:
        if is_admin:
            if ADMIN_CREDENTIALS.get(identifier) == password:
                st.session_state.admin_authenticated = True
                st.session_state.admin_username = identifier
                st.session_state.view = "admin"
                st.rerun()
            else:
                st.error("Invalid admin credentials.")
        else:
            borrower_exists = identifier in set(borrowers_df["borrower_id"])
            if borrower_exists and password == identifier:
                st.session_state.borrower_authenticated = True
                st.session_state.borrower_id = identifier
                st.session_state.view = "borrower"
                st.rerun()
            else:
                st.error("Invalid borrower ID or password.")


def render_admin_login() -> None:
    render_login_page("admin")


def render_borrower_login() -> None:
    render_login_page("borrower")


if "view" not in st.session_state:
    st.session_state.view = "landing"

if st.session_state.view == "admin" and st.session_state.get("admin_authenticated"):
    render_admin_dashboard()
    st.stop()
elif st.session_state.view == "borrower" and st.session_state.get("borrower_authenticated"):
    render_borrower_dashboard(st.session_state["borrower_id"])
    st.stop()
elif st.session_state.view == "admin_login":
    render_admin_login()
    st.stop()
elif st.session_state.view == "borrower_login":
    render_borrower_login()
    st.stop()
else:
    render_landing_page()
    st.stop()