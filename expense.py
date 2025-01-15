import streamlit as st
import numpy as np
import plotly.graph_objects as go
import requests
from bs4 import BeautifulSoup


st.set_page_config(page_title="Financial Planning Calculator")
st.title('Financial Budget Calculator')
# Set default currency to USD
currency_symbols = {"USD": "$", "CAD": "C$", "INR": "₹"}

# Function to update the currency symbol
def get_currency_symbol(currency):
    return currency_symbols.get(currency, "$")

# Create a dropdown to select currency
currency = st.selectbox("Select Currency", options=["USD", "CAD", "INR", 'MEX'])

country_tags = {
    'USD': 'www',
    'CAD': 'ca',
    'INR': 'in',
    'MEX': 'mx'
}

currency_symbol = get_currency_symbol(currency)

# Enhanced UI/UX - Adding tabs for organization
menu_tabs = st.tabs([ "Income", "Expenses", "Forecast", "Reports", "Savings Goals"])

# Variables to store the data globally
salary = 0.0
monthly_takehome_salary = 0.0
total_expenses = 0.0
forecast_savings = []
cumulative_savings = []
goal_amount = 0.0
current_savings = 0.0

# Income Tab
with menu_tabs[0]:
    st.header("**Monthly Income**")
    st.subheader("Salary")
    colAnnualSal, colTax = st.columns(2)

    with colAnnualSal:
        salary = st.number_input(f"Enter your annual salary ({currency_symbol}): ", min_value=0.0, format='%f')
    with colTax:
        base_url = f'https://{country_tags[currency]}.talent.com/tax-calculator?salary={salary}&from=year'
        response = requests.get(base_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        tax_element = soup.select_one('#taxes > div:nth-child(2) > div.c-card.c-card--bottom > div > div.c-card__pie-chart > div > div.l-card__tag-container.l-card__tag-right > div.c-card__tax-number')
        tax_rate = tax_element.text.strip()
        st.metric(label="Anual Tax rate", value=f"{tax_rate}")


    tax_rate = float(tax_rate.replace('%','')) / 100.0
    salary_after_taxes = salary * (1 - tax_rate)
    monthly_takehome_salary = round(salary_after_taxes / 12.0, 2)
    st.metric(label="Monthly Take-Home Income", value=f"{currency_symbol}{monthly_takehome_salary:,.2f}")

# Expenses Tab
with menu_tabs[1]:
    st.header(f"**Monthly Expenses ({currency_symbol})**")
    categories = ["Housing Rent", "Food", "Transport", "Utilities", "Entertainment", "Others"]
    expense_inputs = {}

    for category in categories:
        expense_inputs[category] = st.number_input(f"{category} Expenses ({currency_symbol}):", min_value=0.0, step=50.0, format="%f")

    total_expenses = sum(expense_inputs.values())
    st.metric(label="Total Monthly Expenses", value=f"{currency_symbol}{total_expenses:,.2f}")

# Forecast Tab
with menu_tabs[2]:
    st.header(f"**Forecast Savings ({currency_symbol})**")
    colForecast1, colForecast2 = st.columns(2)
    with colForecast1:
        st.subheader("Forecast Year")
        forecast_year = st.number_input("Enter your forecast year (Min 1 year): ", min_value=0, format='%d')
        forecast_months = 12 * forecast_year 

        st.subheader("Annual Inflation Rate")
        annual_inflation = st.number_input("Enter annual inflation rate (%): ", min_value=0.0, format='%f')
        monthly_inflation = (1+annual_inflation)**(1/12) - 1
        cumulative_inflation_forecast = np.cumprod(np.repeat(1 + monthly_inflation, forecast_months))
        forecast_expenses = total_expenses * cumulative_inflation_forecast
    with colForecast2:
        st.subheader("Annual Salary Growth Rate")
        annual_growth = st.number_input("Enter your expected annual salary growth (%): ", min_value=0.0, format='%f')
        monthly_growth = (1 + annual_growth) ** (1/12) - 1
        cumulative_salary_growth = np.cumprod(np.repeat(1 + monthly_growth, forecast_months))
        forecast_salary = monthly_takehome_salary * cumulative_salary_growth 

    forecast_savings = forecast_salary - forecast_expenses 
    cumulative_savings = np.cumsum(forecast_savings)

    x_values = np.arange(forecast_year + 1)

    fig = go.Figure()

    # Adding animated data
    fig.add_trace(
        go.Scatter(
            x=x_values, 
            y=forecast_salary,
            mode='lines',
            name="Forecast Salary",
            line=dict(color='blue')
        )
    )

    fig.add_trace(
        go.Scatter(
            x=x_values,
            y=forecast_expenses,
            mode='lines',
            name="Forecast Expenses",
            line=dict(color='red')
        )
    )

    fig.add_trace(
        go.Scatter(
            x=x_values, 
            y=cumulative_savings,
            mode='lines+markers',
            name="Forecast Savings",
            line=dict(color='green'),
            marker=dict(size=6)
        )
    )

    fig.update_layout(
        title=f'Forecast Salary, Expenses & Savings Over the Years ({currency_symbol})',
        xaxis_title='Year',
        yaxis_title=f'Amount ({currency_symbol})',
    )

    st.plotly_chart(fig, use_container_width=True)

# Reports Tab
with menu_tabs[3]:
    st.header("Reports")
    
    # Display the summary of financial data
    if salary and total_expenses:
        st.subheader("Income and Expenses Overview")
        st.write(f"Annual Salary: {currency_symbol}{salary:,.2f}")
        st.write(f"Monthly Take-Home Salary: {currency_symbol}{monthly_takehome_salary:,.2f}")
        st.write(f"Total Monthly Expenses: {currency_symbol}{total_expenses:,.2f}")
        st.write(f"Net Savings: {currency_symbol}{monthly_takehome_salary - total_expenses:,.2f}")
        
        # Display forecast details
        if len(forecast_savings) > 0:
            st.subheader("Forecast Overview")
            st.write(f"Estimated Savings Over {forecast_year} Year(s):")
            st.write(f"Total Forecast Savings: {currency_symbol}{cumulative_savings[-1]:,.2f}")
    
    else:
        st.write("Please enter your income and expense details to generate reports.")

# Savings Goals Tab
with menu_tabs[4]:
    st.header("Savings Goals")
    goal_name = st.text_input("Enter the name of your savings goal:")
    goal_amount = st.number_input(f"Enter the target amount for '{goal_name}' ({currency_symbol}):", min_value=0.0, format='%f')
    current_savings = st.number_input(f"Enter your current savings for '{goal_name}' ({currency_symbol}):", min_value=0.0, format='%f')

    if goal_amount > 0:
        progress = (current_savings / goal_amount) * 100
        st.progress(progress / 100)
        st.write(f"You have achieved {progress:.2f}% of your goal '{goal_name}'.")

    st.write("Add multiple goals to track your progress effectively!")
# Define theme and branding styles
def apply_branding_styles():
    st.markdown(
        """
        <style>
        /* General styles */
        body {
            font-family: 'Arial', sans-serif;
        }
        h1, h2, h3 {
            color: #E31837; 
        }
        div[data-testid="stMetricValue"] {
            color: #E31837; 
        }
        div[data-testid="stProgress"] div[role="progressbar"] {
            background-color: #E31837; 
        }
        div[data-baseweb="tab"] > button {
            color: #E31837;
            font-weight: bold;
        }
        div[data-baseweb="tab"] > button[aria-selected="true"] {
            border-bottom: 2px solid #E31837;
            color: black;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

apply_branding_styles()
