# House Price Prediction App

This is an end-to-end Machine Learning application built with Python and Streamlit to predict house prices.

## Features
- Synthetic housing dataset generator.
- Linear Regression model trained using `scikit-learn`.
- Interactive web UI built with `streamlit`.

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Train the model:**
   This will generate a mock dataset `data/house_data.csv` and train the model saving it to `models/house_price_model.pkl`.
   ```bash
   python train.py
   ```

3. **Run the Streamlit App:**
   ```bash
   streamlit run app.py
   ```