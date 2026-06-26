import streamlit as st
import pandas as pd
import numpy as np
import joblib
import os
import database as db

st.set_page_config(page_title="House Price Predictor", page_icon="🏠", layout="wide")

# Initialize DB
if not os.path.exists(db.DB_PATH):
    db.init_db()

# Load Models
@st.cache_resource
def load_models():
    if os.path.exists('models/lr_model.pkl'):
        lr_model = joblib.load('models/lr_model.pkl')
        rf_model = joblib.load('models/rf_model.pkl')
        feature_cols = joblib.load('models/feature_columns.pkl')
        return lr_model, rf_model, feature_cols
    return None, None, None

lr_model, rf_model, feature_cols = load_models()

# Session State for Login
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user_id' not in st.session_state:
    st.session_state['user_id'] = None
if 'username' not in st.session_state:
    st.session_state['username'] = None

def login_register_page():
    st.title("Welcome to House Price Predictor")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        st.subheader("Login")
        log_user = st.text_input("Username", key="log_user")
        log_pass = st.text_input("Password", type="password", key="log_pass")
        if st.button("Login"):
            user_id = db.verify_user(log_user, log_pass)
            if user_id:
                st.session_state['logged_in'] = True
                st.session_state['user_id'] = user_id
                st.session_state['username'] = log_user
                db.log_login(user_id)
                st.success("Logged in successfully!")
                st.rerun()
            else:
                st.error("Invalid username or password")
                
    with tab2:
        st.subheader("Register")
        reg_user = st.text_input("New Username", key="reg_user")
        reg_pass = st.text_input("New Password", type="password", key="reg_pass")
        if st.button("Register"):
            if reg_user and reg_pass:
                if db.create_user(reg_user, reg_pass):
                    st.success("Registration successful! You can now login.")
                else:
                    st.error("Username already exists.")
            else:
                st.warning("Please enter both username and password.")

def dashboard_page():
    st.title(f"🏠 Welcome, {st.session_state['username']}!")
    
    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.session_state['user_id'] = None
        st.session_state['username'] = None
        st.rerun()

    menu = ["Predict", "Prediction Logs", "Login Logs"]
    choice = st.sidebar.selectbox("Navigation", menu)
    
    if choice == "Predict":
        if not lr_model:
            st.error("Models not found. Run train.py first.")
            st.stop()
            
        st.header("Predict House Price")
        
        col1, col2 = st.columns(2)
        with col1:
            area = st.number_input("Area (sq ft)", min_value=500, max_value=10000, value=1500, step=50)
            bedrooms = st.number_input("Bedrooms", min_value=1, max_value=10, value=3, step=1)
            location = st.selectbox("Location", ['Downtown', 'Suburbs', 'Uptown', 'Rural'])
            
        with col2:
            bathrooms = st.number_input("Bathrooms", min_value=1, max_value=10, value=2, step=1)
            age = st.number_input("Property Age (years)", min_value=0, max_value=100, value=10, step=1)
            model_choice = st.selectbox("Model", ["Linear Regression", "Random Forest"])
            
        if st.button("Predict Price", type="primary"):
            # Prepare Input Data
            input_dict = {
                'Area': area, 'Bedrooms': bedrooms, 'Bathrooms': bathrooms, 'Age': age, 'Location': location
            }
            input_df = pd.DataFrame([input_dict])
            
            # One-hot encode using same columns as training
            input_encoded = pd.get_dummies(input_df, columns=['Location'])
            # Ensure all columns from training exist
            for col in feature_cols:
                if col not in input_encoded.columns:
                    input_encoded[col] = 0
            input_encoded = input_encoded[feature_cols] # Reorder to match training
            
            if model_choice == "Linear Regression":
                prediction = lr_model.predict(input_encoded)[0]
                st.success(f"### Estimated Price: **${prediction:,.2f}**")
            else:
                prediction = rf_model.predict(input_encoded)[0]
                st.success(f"### Estimated Price: **${prediction:,.2f}**")
                
                # Confidence / Uncertainty calculation (std deviation of tree predictions)
                import warnings
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", UserWarning)
                    tree_predictions = [tree.predict(input_encoded.values)[0] for tree in rf_model.estimators_]
                std_dev = np.std(tree_predictions)
                # Roughly convert standard deviation to a % confidence assuming standard dev relates to price
                confidence = max(0, 100 - (std_dev / prediction * 100))
                st.info(f"**Prediction Confidence:** {confidence:.2f}% (Std Dev: ${std_dev:,.2f})")
                
            # Log Prediction
            db.log_prediction(st.session_state['user_id'], area, bedrooms, bathrooms, age, location, model_choice, prediction)

    elif choice == "Prediction Logs":
        st.header("History of Predictions")
        logs = db.get_prediction_logs()
        if logs:
            df_logs = pd.DataFrame(logs, columns=["Username", "Area", "Bedrooms", "Bathrooms", "Age", "Location", "Model", "Predicted Price", "Time"])
            st.dataframe(df_logs, use_container_width=True)
        else:
            st.write("No predictions found.")
            
    elif choice == "Login Logs":
        st.header("Login History")
        logs = db.get_login_logs()
        if logs:
            df_logs = pd.DataFrame(logs, columns=["Username", "Login Time"])
            st.dataframe(df_logs, use_container_width=True)
        else:
            st.write("No logins found.")

if not st.session_state['logged_in']:
    login_register_page()
else:
    dashboard_page()
