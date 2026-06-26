import streamlit as st
import pandas as pd
import numpy as np
import joblib
import os
import database as db

st.set_page_config(page_title="House Price Predictor", page_icon="🏠", layout="wide")

# Initialize DB (and seed inventory if empty)
if not os.path.exists(db.DB_PATH):
    db.init_db()
else:
    # Ensure tables/seed exist even if DB file existed before this update
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

    menu = ["Predict Price", "Plots & Sites", "Ready-Made Houses", "Prediction Logs", "Login Logs"]
    choice = st.sidebar.selectbox("Navigation", menu)
    
    if choice == "Predict Price":
        if not lr_model:
            st.error("Models not found. Run train.py first.")
            st.stop()
            
        st.header("Predict House Price")
        
        col1, col2 = st.columns(2)
        with col1:
            area = st.number_input("Area (sq ft)", min_value=500, max_value=10000, value=1500, step=50)
            bedrooms = st.number_input("Bedrooms", min_value=1, max_value=10, value=3, step=1)
            location = st.selectbox("Location", db.LOCATIONS)
            
        with col2:
            bathrooms = st.number_input("Bathrooms", min_value=1, max_value=10, value=2, step=1)
            age = st.number_input("Property Age (years)", min_value=0, max_value=100, value=10, step=1)
            model_choice = st.selectbox("Model", ["Linear Regression", "Random Forest"])
            
        if st.button("Predict Price", type="primary"):
            input_dict = {
                'Area': area, 'Bedrooms': bedrooms, 'Bathrooms': bathrooms, 'Age': age, 'Location': location
            }
            input_df = pd.DataFrame([input_dict])
            
            input_encoded = pd.get_dummies(input_df, columns=['Location'])
            for col in feature_cols:
                if col not in input_encoded.columns:
                    input_encoded[col] = 0
            input_encoded = input_encoded[feature_cols]
            
            if model_choice == "Linear Regression":
                prediction = lr_model.predict(input_encoded)[0]
                st.success(f"### Estimated Price: **${prediction:,.2f}**")
            else:
                prediction = rf_model.predict(input_encoded)[0]
                st.success(f"### Estimated Price: **${prediction:,.2f}**")
                
                import warnings
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", UserWarning)
                    tree_predictions = [tree.predict(input_encoded.values)[0] for tree in rf_model.estimators_]
                std_dev = np.std(tree_predictions)
                confidence = max(0, 100 - (std_dev / prediction * 100))
                st.info(f"**Prediction Confidence:** {confidence:.2f}% (Std Dev: ${std_dev:,.2f})")
                
            db.log_prediction(st.session_state['user_id'], area, bedrooms, bathrooms, age, location, model_choice, prediction)

    elif choice == "Plots & Sites":
        st.header("🗺️ Available Plots & Sites")
        plots = db.get_available_plots()
        
        if not plots:
            st.info("No plots are currently available.")
        else:
            df_plots = pd.DataFrame(plots, columns=["ID", "Location", "Size (sqft)", "Price ($)", "Status"])
            
            # Filters
            col1, col2 = st.columns(2)
            with col1:
                loc_filter = st.selectbox("Filter by Location", ["All"] + db.LOCATIONS)
            with col2:
                max_price = st.slider("Max Price ($)", min_value=10000, max_value=int(df_plots["Price ($)"].max() + 10000), value=int(df_plots["Price ($)"].max()))
            
            # Apply Filters
            if loc_filter != "All":
                df_plots = df_plots[df_plots["Location"] == loc_filter]
            df_plots = df_plots[df_plots["Price ($)"] <= max_price]
            
            st.write(f"Showing **{len(df_plots)}** available plots:")
            
            # Display items
            for _, row in df_plots.iterrows():
                with st.container(border=True):
                    c1, c2, c3 = st.columns([2, 2, 1])
                    c1.write(f"**Location:** {row['Location']}")
                    c1.write(f"**Size:** {row['Size (sqft)']:,.0f} sqft")
                    c2.write(f"**Price:** ${row['Price ($)']:,.2f}")
                    if c3.button("Reserve", key=f"plot_{row['ID']}"):
                        db.reserve_plot(row['ID'])
                        st.success("Successfully reserved!")
                        st.rerun()

    elif choice == "Ready-Made Houses":
        st.header("🏡 Available Ready-Made Houses")
        houses = db.get_available_houses()
        
        if not houses:
            st.info("No houses are currently available.")
        else:
            df_houses = pd.DataFrame(houses, columns=["ID", "Location", "Bedrooms", "Bathrooms", "Area (sqft)", "Price ($)", "Status"])
            
            # Filters
            col1, col2, col3 = st.columns(3)
            with col1:
                loc_filter = st.selectbox("Filter by Location", ["All"] + db.LOCATIONS, key="h_loc")
            with col2:
                bed_filter = st.selectbox("Min Bedrooms", ["All", 1, 2, 3, 4, 5])
            with col3:
                max_price = st.slider("Max Price ($)", min_value=50000, max_value=int(df_houses["Price ($)"].max() + 50000), value=int(df_houses["Price ($)"].max()), key="h_price")
            
            # Apply Filters
            if loc_filter != "All":
                df_houses = df_houses[df_houses["Location"] == loc_filter]
            if bed_filter != "All":
                df_houses = df_houses[df_houses["Bedrooms"] >= bed_filter]
            df_houses = df_houses[df_houses["Price ($)"] <= max_price]
            
            st.write(f"Showing **{len(df_houses)}** available houses:")
            
            # Display items
            for _, row in df_houses.iterrows():
                with st.container(border=True):
                    c1, c2, c3 = st.columns([2, 2, 1])
                    c1.write(f"**Location:** {row['Location']} | **Area:** {row['Area (sqft)']:,.0f} sqft")
                    c1.write(f"🛏️ {row['Bedrooms']} Beds | 🛁 {row['Bathrooms']} Baths")
                    c2.write(f"**Price:** ${row['Price ($)']:,.2f}")
                    if c3.button("Reserve", key=f"house_{row['ID']}"):
                        db.reserve_house(row['ID'])
                        st.success("Successfully reserved!")
                        st.rerun()

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
