import pandas as pd
import streamlit as st
import datetime

#Will use this to compile all the necesary data & configs applied across each files

#Declare object shared across pages
expense_cols = [
    "Breakfast/Coffee","Lunch", "Dinner", "Snack", "Misc", "Utilities", "Entertainment"
]

budget_file = r"C:\Users\Emerson Anwar\Desktop\Projects\Data\Budgets.csv"

demo_budgets = {
    "Breakfast/Coffee": 250000, "Lunch": 400000, "Dinner": 450000,
    "Snack": 100000, "Entertainment": 1500000,
    "Misc": 150000, "Utilities": 250000,
}

def load_budgets():
    try:
        b = pd.read_csv(budget_file)
        return dict(zip(b["Category"], b["Budget"]))
    except Exception as e:
        print(f"load_budgets failed:{e}")
        return demo_budgets

budgets = load_budgets()

#GENERATE SCALED DEMO
def generate_scaled_demo():
    import numpy as np    
    rng = np.random.default_rng(42)

    BASE = 3600000

    dates = pd.date_range(
        start="2026-05-01",
        end="2026-10-31",
        freq="D"
    )

    monthly_multiplier = {
        "2026-06": 0.75, "2026-07": 0.85, "2026-08": 1.10,
        "2026-09": 1.25, "2026-10": 1.05,
    }

    shares = {
        "Entertainment": 0.50, "Utilities": 0.15, "Dinner": 0.12,
        "Lunch": 0.11, "Breakfast/Coffee": 0.07, "Snack": 0.03, "Misc": 0.02,
    }
    spend_prob = {
        "Entertainment": 0.5, "Utilities": 0.3, "Dinner": 0.8, "Lunch": 0.8,
        "Breakfast/Coffee": 0.7, "Snack": 0.3, "Misc": 0.2,
    }

    df = pd.DataFrame({"Date": pd.date_range("2026-06-01", "2026-10-31", freq="D")})
    df["Month_Sort"] = df["Date"].dt.to_period("M").astype(str)
    df["Month"] = df["Date"].dt.strftime("%b %Y")
    n = len(df)

    weighting = {c: rng.random(n) * (rng.random(n) < spend_prob[c]) for c in shares}

    for c in shares:
        df[c] = 0.0
    for month_key, pos in df.groupby("Month_Sort").indices.items():
        target = BASE * monthly_multiplier.get(month_key, 1.0)
        for c, share in shares.items():
            w = weighting[c][pos]
            if w.sum() == 0:
                w = np.ones(len(pos))
            df.loc[pos, c] = (w / w.sum() * target * share).round(-3)

    df["Remarks"] = "No Remarks"
    return df


#Load Data
def load_data(): #define function loaddata to be reused later
    try: 
        df1 = pd.read_csv(r"C:\Users\Emerson Anwar\Desktop\Projects\Data\Clean Data\May-Jun Expenses Clean.csv")
        df2 = pd.read_csv(r"C:\Users\Emerson Anwar\Desktop\Projects\Data\Clean Data\Jun-Jul Expenses Clean.csv")
        df3 = pd.read_csv(r"C:\Users\Emerson Anwar\Desktop\Projects\Data\Clean Data\Jul-Aug Expenses Clean.csv")
        df4 = pd.read_csv(r"C:\Users\Emerson Anwar\Desktop\Projects\Data\Clean Data\Aug-Sep Expenses Clean.csv")
        df5 = pd.read_csv(r"C:\Users\Emerson Anwar\Desktop\Projects\Data\Clean Data\Sep-Oct Expenses Clean.csv")

        df = pd.concat([df1,df2,df3,df4,df5], ignore_index=True)
        df["Date"] = pd.to_datetime(df["Date"], dayfirst=True)
        df["Month_Sort"] = df["Date"].dt.to_period("M").astype(str)
        
        df["Month"] = df["Date"].dt.strftime("%b %Y") # stringify, %b = abbreviated Month, %Y  = year
        #df["Month"] = df["Date"].dt.to_period("M").astype(str)
        df = df[df["Month_Sort"]>="2026-06"]
        return df, False
    except Exception as e:
        print(f"load_data failed: {e}")
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
    

def privacy_toggle():
    if "privacy" not in st.session_state :
        st.session_state.privacy = True
    st.session_state.privacy = st.sidebar.checkbox(
        "🔒 Privacy Mode", value=st.session_state.privacy
    )
    return st.session_state.privacy

def get_sidebar_single(df, is_demo = False):
    st.sidebar.title("Menu")

    use_demo = privacy_toggle() and not is_demo

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


