import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import requests
import os

CONFIG_PATH = "./config.yaml"

st.set_page_config(page_title="🏠 Real Estate Dashboard", layout="wide")

# ---------- Load or create config ----------
def load_config():
    if not os.path.exists(CONFIG_PATH):
        return {
            "credentials": {"usernames": {}},
            "cookie": {"name": "realestate", "key": "some_key", "expiry_days": 30},
            "preauthorized": {"emails": []}
        }
    with open(CONFIG_PATH, "r") as file:
        return yaml.load(file, Loader=SafeLoader)

def save_config(config):
    with open(CONFIG_PATH, "w") as file:
        yaml.dump(config, file, default_flow_style=False)

def user_exists(username, config):
    return username in config["credentials"]["usernames"]

# ---------- Modern Register Form ----------
st.markdown("""
<style>
    .register-box {
        padding: 1rem;
        background-color: #f0f2f6;
        border-radius: 10px;
        box-shadow: 0 0 10px rgba(0,0,0,0.1);
    }
    .register-title {
        color: #0f4c81;
        font-size: 1.2rem;
        font-weight: bold;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

with st.sidebar.expander("📝 New here? Register"):
    st.markdown("<div class='register-box'>", unsafe_allow_html=True)
    st.markdown("<div class='register-title'>Create a New Account</div>", unsafe_allow_html=True)

    with st.form("register_form"):
        name = st.text_input("👤 Full Name")
        username = st.text_input("🧑 Username")
        email = st.text_input("📧 Email")
        password = st.text_input("🔒 Password", type="password")
        confirm = st.text_input("🔒 Confirm Password", type="password")
        register = st.form_submit_button("Register")

        if register:
            config = load_config()
            if not name or not username or not email or not password:
                st.warning("Please fill all fields.")
            elif password != confirm:
                st.error("Passwords do not match.")
            elif user_exists(username, config):
                st.error("Username already exists.")
            else:
                hashed = stauth.Hasher().hash(password)
                config['credentials']['usernames'][username] = {
                    'name': name,
                    'email': email,
                    'password': hashed
                }
                save_config(config)
                st.success("✅ Registered successfully! You can now log in.")

    st.markdown("</div>", unsafe_allow_html=True)

# ---------- Authenticator Setup ----------
config = load_config()
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

name, auth_status, username = authenticator.login(location="sidebar", label="🔐 Login", key="auth")

# ---------- App Content ----------
if auth_status is False:
    st.error("Invalid username or password")
elif auth_status is None:
    st.info("👈 Please login or register to continue.")
elif auth_status:
    authenticator.logout("Logout", "sidebar")
    st.sidebar.success(f"Welcome, {name}")

    st.markdown("<h2 style='color:#0f4c81;'>🏠 Real Estate Price & Risk Prediction</h2>", unsafe_allow_html=True)
    st.markdown("Enter property details to get price and risk score.")

    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        bhk = st.number_input("BHK", 1, 5, step=1, key="input_bhk")
    with col2:
        area = st.number_input("Area (sqft)", 500, 10000, step=100, key="input_area")
    with col3:
        flood_zone = st.selectbox("Flood Zone", options=[0, 1, 2], format_func=lambda x: f"Zone {x}", key="input_flood")

    if st.button("🔍 Predict Price & Risk", key="predict_button"):
        try:
            res = requests.post("http://localhost:5000/api/predict", json={
                "bhk": bhk, "area": area, "floodZone": flood_zone
            })
            if res.ok:
                result = res.json()
                price = result["predicted_price"]
                risk = result["risk_score"]
                st.success(f"💰 Estimated Price: ₹{price} Lakhs")
                st.info(f"⚠️ Risk Score: {risk}/100")

                st.components.v1.html(f"""
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
                st.error("❌ API error. Please check your backend.")
        except Exception as e:
            st.error(f"Error contacting API: {e}")



