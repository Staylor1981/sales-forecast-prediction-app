import streamlit as st
import requests
import pandas as pd
import json

# Configure Streamlit page
st.set_page_config(page_title="SuperKart Sales Predictor", layout="wide")

st.title("🏪 SuperKart Sales Forecast Prediction App")
st.write("This interactive app forecasts the weekly/monthly sales total for SuperKart products based on product and store characteristics.")

# Backend URL inside the Docker network or local machine
BACKEND_URL = "http://backend:7860"  # 'backend' is the service/container name in our docker network setup

# Create tabs for Single Prediction and Batch Prediction
tab1, tab2 = st.tabs(["🎯 Single Product Prediction", "📂 Batch Prediction"])

with tab1:
    st.subheader("Enter Product and Store Details")

    # Input layout columns
    col1, col2 = st.columns(2)

    with col1:
        product_weight = st.number_input("Product Weight (kg)", min_value=1.0, max_value=30.0, value=12.5, step=0.1)
        product_sugar_content = st.selectbox("Sugar Content", ["Low Sugar", "Regular", "No Sugar"])
        product_allocated_area = st.number_input("Product Allocated Area (Ratio)", min_value=0.001, max_value=0.5, value=0.05, format="%f")
        product_mrp = st.number_input("Product Maximum Retail Price (MRP in $)", min_value=1.0, max_value=500.0, value=150.0, step=0.5)
        product_type = st.selectbox("Product Category", [
            "Fruits and Vegetables", "Snack Foods", "Frozen Foods", "Dairy",
            "Household", "Baking Goods", "Canned", "Health and Hygiene",
            "Meat", "Soft Drinks", "Breads", "Hard Drinks", "Others",
            "Starchy Foods", "Breakfast", "Seafood"
        ])

    with col2:
        store_establishment_year = st.slider("Store Establishment Year", min_value=1980, max_value=2026, value=2000, step=1)
        store_size = st.selectbox("Store Size", ["Small", "Medium", "High"])
        store_location_city_type = st.selectbox("City Type", ["Tier 1", "Tier 2", "Tier 3"])
        store_type = st.selectbox("Store Classification", ["Supermarket Type1", "Supermarket Type2", "Departmental Store", "Food Mart"])
        product_store_sales_total = st.number_input("Historical Store Total Sales Benchmark ($)", min_value=0.0, max_value=50000.0, value=3000.0, step=100.0)

    # Predict button
    if st.button("Forecast Sales Total"):
        payload = {
            "Product_Weight": product_weight,
            "Product_Sugar_Content": product_sugar_content,
            "Product_Allocated_Area": product_allocated_area,
            "Product_MRP": product_mrp,
            "Store_Establishment_Year": store_establishment_year,
            "Product_Store_Sales_Total": product_store_sales_total,
            "Product_Sugar_Content": product_sugar_content,
            "Product_Type": product_type,
            "Store_Size": store_size,
            "Store_Location_City_Type": store_location_city_type,
            "Store_Type": store_type
        }

        try:
            response = requests.post(f"{BACKEND_URL}/v1/predict", json=payload)
            if response.status_code == 200:
                result = response.json()
                predicted_sales = result.get("Predicted Sales Total (in dollars)", 0.0)
                st.success(f"### 💰 Projected Sales Total: ${predicted_sales:,.2f}")
            else:
                st.error(f"Backend returned an error: {response.status_code} - {response.text}")
        except Exception as e:
            st.error(f"Failed to connect to the backend server. Error: {str(e)}")

with tab2:
    st.subheader("Upload CSV File for Batch Forecasting")
    st.write("The CSV file must include the exact feature columns required by the model.")

    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

    if uploaded_file is not None:
        # Read and display a preview of the data
        df = pd.read_csv(uploaded_file)
        st.write("### Preview of uploaded dataset:")
        st.dataframe(df.head(10))

        if st.button("Run Batch Forecast"):
            # Rewind file pointer to the beginning for sending via requests
            uploaded_file.seek(0)
            files = {'file': (uploaded_file.name, uploaded_file, 'text/csv')}

            try:
                with st.spinner('Generating predictions...'):
                    response = requests.post(f"{BACKEND_URL}/v1/predictbatch", files=files)

                if response.status_code == 200:
                    predictions = response.json()

                    # Map predictions back into our dataframe
                    # Assuming predictions dict keys are string representation of the index or Product_Id
                    df['Predicted_Sales'] = df.index.map(lambda x: predictions.get(str(x), predictions.get(df.iloc[x].get('Product_Id', None), None)))

                    st.success("🎉 Predictions generated successfully!")
                    st.write("### Forecasted Sales Output Preview:")
                    st.dataframe(df)

                    # Option to download the prediction CSV
                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Download Forecast Results as CSV",
                        data=csv,
                        file_name="SuperKart_Sales_Forecasts.csv",
                        mime="text/csv"
                    )
                else:
                    st.error(f"Backend API returned an error: {response.status_code}")
            except Exception as e:
                st.error(f"Could not connect to prediction engine: {str(e)}")
