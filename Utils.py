import pandas as pd
import streamlit as st
import datetime

#Will use this to compile all the necesary data & configs applied across each files

#Declare object shared across pages
expense_cols = [
    "Breakfast/Coffee","Lunch",    "Dinner", "Snack", "Transport",    "Misc",    "Utilities", "Entertainment"
]

budgets = {
    "Breakfast/Coffee" : 200000,
    "Lunch"            : 350000,
    "Dinner"           : 350000,
    "Snack"            : 100000,
    "Transport"        : 50000,
    "Entertainment"    : 1500000,
    "Misc"             : 150000,
    "Utilities"        : 300000
}

#GENERATE SCALED DEMO
def generate_scaled_demo():
    import numpy as np
    dates = pd.date_range(
        start="2026-05-01",
        end="2026-08-31",
        freq="D"
    )

    monthly_multiplier = {
        "2026-05": 0.75,
        "2026-06": 0.90,
        "2026-07": 1.15,
        "2026-08": 1.00
    }

    base_daily = {
        "Breakfast/Coffee": 5000,
        "Lunch":            9000,
        "Dinner":           8000,
        "Snack":            3000,
        "Transport":        4000,
        "Misc":             2000,
        "Utilities":        9000,
        "Entertainment":    35000
    }

    rows = []
    for date in dates:
        month_key = date.strftime("%Y-%m")
        multiplier = monthly_multiplier.get(month_key, 1.0)
        row = {"Date": date}

        for col, base in base_daily.items():
            if col in ["Breakfast/Coffee", "Lunch", "Dinner"]:
                spend = base * multiplier if np.random.random() > 0.2 else 0
            elif col in ["Entertainment", "Transport"]:
                spend = base * multiplier if np.random.random() > 0.5 else 0
            else:
                spend = base * multiplier if np.random.random() > 0.7 else 0

            row[col] = round(spend / 1000) * 1000

        rows.append(row)

    df = pd.DataFrame(rows)
    df["Date"] = pd.to_datetime(df["Date"])
    df["Month_Sort"] = df["Date"].dt.to_period("M").astype(str)
    df["Month"] = df["Date"].dt.strftime("%b %Y")
    df["Remarks"] = "No Remarks"
    return df


#Load Data
def load_data(): #define function loaddata to be reused later
    try: 
        df1 = pd.read_csv(r"C:\Users\Emerson Anwar\Desktop\Projects\Data\Clean Data\May-Jun Expenses Clean.csv")
        df2 = pd.read_csv(r"C:\Users\Emerson Anwar\Desktop\Projects\Data\Clean Data\Jun-Jul Expenses Clean.csv")
        df3 = pd.read_csv(r"C:\Users\Emerson Anwar\Desktop\Projects\Data\Clean Data\Jul-Aug Expenses Clean.csv")

        df = pd.concat([df1,df2,df3], ignore_index=True)
        df["Date"] = pd.to_datetime(df["Date"], dayfirst=True)
        df["Month_Sort"] = df["Date"].dt.to_period("M").astype(str)
        df["Month"] = df["Date"].dt.strftime("%b %Y") # stringify, %b = abbreviated Month, %Y  = year
        #df["Month"] = df["Date"].dt.to_period("M").astype(str)
        return df, False
    except:
        df = generate_scaled_demo()
        return df, True

#SCALE EXPENSE 
def scale_data(df, seed =42):
    import random
    random.seed(seed) #seeds number generator, having seed in place will help generate consistent random numbers across apps
    factor = round(random.uniform(0.6,0.9),4) #generate random value between 0.6 * 0.9,, then round factor to 4 decimals

    df_scaled = df.copy() #create copy of df_scaled dataframe, so it doesnt mess with real data
    for col in expense_cols:
        if col in df_scaled.columns:
            df_scaled[col] = (df_scaled[col] * factor).round(-3) #Loopsthrough expense cols, then multiply by random factor, scale to nearest 1k
    return df_scaled, factor


#Get SCALE BUDGETS
def get_scaled_data(factor):
    return{
        col : round(budgets[col]* factor/50000)*50000
        for col in budgets
    }
    
    
#Month Filter Dropdowns - Scarping multi-select to focus on single select for now
    month_filter = st.sidebar.selectbox(
        "Select Month", #Labels 
        options = available_months, #get options from available_months
        index = default_list #Defaults to Latest Month
    )

#Apply logic to dropdown
    df_filtered =   (
        df[df["Month"] == month_filter] #only returns single month string
    )
    return df_filtered, month_filter

def get_sidebar_multi(df):
    st.sidebar.title("Menu")
    
    available_months = (
        df.sort_values("Month_Sort")["Month"].unique().tolist() #Get Unique Month, sort, then add to List
        ) 
                
    #Month Filter Dropdowns - Scarping multi-select to focus on single select for now
    month_filter = st.sidebar.multiselect(
        "Select Month(s)", #Labels 
        options = available_months, #get options from available_months
        default= available_months #Defaults to Latest Month
    )

#Apply logic to dropdown
    df_filtered =   (
        df[df["Month"].isin(month_filter)]
        if month_filter #if user selects 1 month, then get month and filter based on month, result = value_if_true if condition else value_if_false
        else df.copy() #create fresh copy of original
    )
    return df_filtered, month_filter

#() to call functions,  wrap long lines for variable definition, tuples
#[] For Lists, Get Columns or Rows, and for Filtering
#{} Dictionaries - List Column and its value, Sets, f-string

def color_value(val, good_if="positive"):
    try :
        if isinstance(val, str) and "%" in val :
            number = float(val.replace("%",""))
        elif isinstance(val, str):
            number = float(
                val.replace("Rp","")
                    .replace(",","")
                    .strip()
            )
        else:
            number = float(val)

        if good_if == "positive":
            color = "green" if number>=0 else "red"
        elif good_if == "negative":
            color = "red" if number > 100 else "green"
        elif good_if == "decrease":
            color = "green" if number <= 0 else "red"
            
    except:
        color = "black"

    return f"color: {color}"


#Budget Logic - round to nearest 50k
def round_to_50 (amount, base =50000): #Base will default to 50 if don't pass base
    import math
    return math.ceil(amount/base)*base #Round up
    

def get_sidebar_single(df):
    st.sidebar.title("Menu")

    use_demo = st.sidebar.checkbox(
        "Privacy Mode",    )

    if use_demo:
        df, factor = scale_data(df)
        active_budgets = get_scaled_data(factor)
    else:
        active_budgets = budgets

    available_months = (
        df.sort_values("Month_Sort")["Month"].unique().tolist()
    )

    current_month = datetime.datetime.now().strftime("%b %Y")

    default_index = (
        available_months.index(current_month)
        if current_month in available_months
        else len(available_months) - 1
    )

    month_filter = st.sidebar.selectbox(
        "Select Month",
        options=available_months,
        index=default_index
    )

    df_filtered = df[df["Month"] == month_filter]

    return df_filtered, month_filter, active_budgets