import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
import joblib

# Create directories if they don't exist
os.makedirs('data', exist_ok=True)
os.makedirs('models', exist_ok=True)

data_path = 'data/house_data.csv'
locations = ['Downtown', 'Suburbs', 'Uptown', 'Rural']

# 1. Generate Mock Data
print("Generating mock data...")
np.random.seed(42)
n_samples = 1000

area = np.random.randint(800, 5000, n_samples)
bedrooms = np.random.randint(1, 6, n_samples)
bathrooms = np.random.randint(1, 4, n_samples)
age = np.random.randint(0, 50, n_samples)
loc = np.random.choice(locations, n_samples)

# Price calculation logic with location impact
price = (area * 150) + (bedrooms * 20000) + (bathrooms * 15000) - (age * 1000)
# Location multiplier
loc_mult = {'Downtown': 1.5, 'Uptown': 1.2, 'Suburbs': 1.0, 'Rural': 0.8}
price = price * np.array([loc_mult[l] for l in loc])
price += np.random.randint(-50000, 50000, n_samples)

df = pd.DataFrame({
    'Area': area,
    'Bedrooms': bedrooms,
    'Bathrooms': bathrooms,
    'Age': age,
    'Location': loc,
    'Price': price
})

df.to_csv(data_path, index=False)
print(f"Mock data saved to {data_path}")

# 2. Preprocess
# One-hot encoding for Location
X = df[['Area', 'Bedrooms', 'Bathrooms', 'Age', 'Location']]
y = df['Price']

X_encoded = pd.get_dummies(X, columns=['Location'])
feature_columns = X_encoded.columns.tolist()

X_train, X_test, y_train, y_test = train_test_split(X_encoded, y, test_size=0.2, random_state=42)

# 3. Train Models
print("Training Linear Regression model...")
lr_model = LinearRegression()
lr_model.fit(X_train, y_train)

print("Training Random Forest model...")
rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
rf_model.fit(X_train, y_train)

# 4. Evaluate
lr_pred = lr_model.predict(X_test)
rf_pred = rf_model.predict(X_test)

print(f"Linear Regression - R2: {r2_score(y_test, lr_pred):.2f}")
print(f"Random Forest - R2: {r2_score(y_test, rf_pred):.2f}")

# 5. Save Models and Features
joblib.dump(lr_model, 'models/lr_model.pkl')
joblib.dump(rf_model, 'models/rf_model.pkl')
joblib.dump(feature_columns, 'models/feature_columns.pkl')
print("Models and features saved to models/")
