import os
import streamlit as st
import requests
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import streamlit.components.v1 as components
from dotenv import load_dotenv

# ------------------ Load .env Variables ------------------
load_dotenv()
API_URL = os.getenv("FLASK_API_URL")

# ------------------ Page Config ------------------
st.set_page_config(page_title="🏠 Real Estate Dashboard", layout="wide")

# ------------------ Load YAML Auth Config ------------------
try:
    with open("config.yaml") as file:
        config = yaml.load(file, Loader=SafeLoader)
except FileNotFoundError:
    st.error("❌ 'config.yaml' not found. Please upload it to the same folder as app.py.")
    st.stop()

# ------------------ Initialize Authenticator ------------------
authenticator = stauth.Authenticate(
    config["credentials"],
    config["cookie"]["name"],
    config["cookie"]["key"],
    config["cookie"]["expiry_days"]
)

# ------------------ Login UI ------------------
authenticator.login(location="sidebar", max_concurrent_users=5)

# ------------------ User Registration ------------------
with st.sidebar.expander("🔐 Register New User"):
    with st.form("register_form", clear_on_submit=True):
        new_username = st.text_input("Username")
        new_name = st.text_input("Full Name")
        new_password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        submitted = st.form_submit_button("Register")

        if submitted:
            if new_password == confirm_password:
                hashed_pw = stauth.Hasher([new_password]).generate()[0]
                config["credentials"]["usernames"][new_username] = {
                    "name": new_name,
                    "password": hashed_pw
                }
                with open("config.yaml", "w") as file:
                    yaml.dump(config, file, default_flow_style=False)
                st.success("✅ User registered. You can now log in.")
            else:
                st.error("❌ Passwords do not match")

# ------------------ Main Dashboard ------------------
if st.session_state.get("authentication_status"):
    authenticator.logout("Logout", "sidebar")
    st.sidebar.success(f"✅ Logged in as: {st.session_state['name']}")

    # Custom UI Styling
    st.markdown("""
    <style>
        .main {
            background-color: #f8fafc;
            font-family: 'Segoe UI', sans-serif;
        }
        .title {
            color: #0f4c81;
            font-weight: bold;
        }
        .stButton>button {
            background-color: #0f4c81;
            color: white;
            border: none;
            padding: 0.6rem 1.4rem;
            border-radius: 8px;
        }
        .stButton>button:hover {
            background-color: #093b66;
        }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<h2 class='title'>🏠 Real Estate Price & Risk Prediction</h2>", unsafe_allow_html=True)
    st.info("Enter the property details below to get an estimated price and risk score.")

    # Input Form
    with st.form("prediction_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            bhk = st.number_input("BHK", 1, 5, step=1)
        with col2:
            area = st.number_input("Area (sqft)", 500, 10000, step=100)
        with col3:
            flood_zone = st.selectbox("Flood Zone", options=[0, 1, 2], format_func=lambda x: f"Zone {x}")

        predict = st.form_submit_button("🔍 Predict Price & Risk")

    if predict:
        payload = {"bhk": bhk, "area": area, "floodZone": flood_zone}
        try:
            res = requests.post(f"{API_URL}/api/predict", json=payload)
            if res.ok:
                result = res.json()
                price = result["predicted_price"]
                risk = result["risk_score"]

                st.success(f"💰 Estimated Price: ₹{price} Lakhs")
                st.warning(f"⚠️ Risk Score: {risk} / 100")

                # Risk Meter Gauge
                components.html(f"""
                <div style='margin-top:30px;'>
                    <h4>📊 Risk Visualization</h4>
                    <div style="width:100%; max-width:400px;">
                        <svg width="100%" viewBox="0 0 200 100">
                            <defs>
                                <linearGradient id="g" x1="0" x2="1" y1="0" y2="0">
                                    <stop offset="0%" stop-color="#3ac569"/>
                                    <stop offset="50%" stop-color="#fbc634"/>
                                    <stop offset="100%" stop-color="#f34a4a"/>
                                </linearGradient>
                            </defs>
                            <path d="M10,100 A90,90 0 0,1 190,100" fill="none" stroke="url(#g)" stroke-width="20" />
                            <circle cx="{10 + 180 * risk / 100}" cy="100" r="10" fill="#000"/>
                        </svg>
                    </div>
                </div>
                """, height=180)
            else:
                st.error("❌ Prediction failed. Check API server.")
        except Exception as e:
            st.error(f"❌ Error contacting API: {e}")

elif st.session_state.get("authentication_status") is False:
    st.error("❌ Incorrect username or password")
elif st.session_state.get("authentication_status") is None:
    st.warning("🛡️ Please enter your login credentials")
