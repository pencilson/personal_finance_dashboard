import streamlit as st
import plotly.express as px
import pandas as pd

import sys
import os

#Import Utilities
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from Utils import load_data, get_sidebar_single, expense_cols #Go into Utils, import all the functions

st.set_page_config(
    page_title=  "Finance Dashboard",
    page_icon="💰",
    layout="wide"
)

@st.cache_data #cache data and store in browser memory

def get_data() :
    return load_data()

df, is_demo = get_data()

if is_demo:
    st.sidebar.warning(
        "DEMO - DATA IS NOT REAL"
    )

#Call df_filtered and filters
df_filtered, month_filter, active_budget = get_sidebar_single(df)

#------------------------CALCS---------------------------
total_expense = df_filtered[expense_cols].sum().sum() #sum total per category, then sum all categories
#monthly_avg = total_expense/len(month_filter) if month_filter else 0 #monthly_avg = total_expense / df["Month"].nunique() #total expense divided by number of unique months
top_category = df_filtered[expense_cols].sum().idxmax() #find index with highest value
category_totals = df_filtered[expense_cols].sum().sort_values(ascending=False)
monthly_total = df_filtered.groupby("Month")[expense_cols].sum()
monthly_total["Total Calculated"] = monthly_total.sum(axis=1) #add accross each row
monthly_total = monthly_total[["Total Calculated"]].reset_index()
months_count = df_filtered["Month"].nunique() #count unique months
actual_avg = (df_filtered[expense_cols].sum() / months_count).round(0)

#daily total
daily_amounts = (
    df_filtered.groupby("Date")[expense_cols]
    .sum()
    .sum(axis=1)
    .reset_index()
)

daily_amounts.columns = ["Date","Amount"]


top_expense_category = category_totals.index[0]
top_expense_amount = category_totals.iloc[0]
top_expense_portion = ((top_expense_amount/category_totals.sum())*100).round(1)

#Budgets Variables
budget_df = pd.DataFrame({ 
    "Category" : expense_cols,
    "Budget" : [active_budget[col] for col in expense_cols], #for each column in expense columns, get value from budgets 
    "Actual" : [actual_avg[col] for col in expense_cols]

})

budget_df["Difference"] = budget_df["Budget"] - budget_df["Actual"]

#Health Score Calcs
frq_categories = len(expense_cols)
frq_under_budget = (budget_df["Difference"] >= 0).sum()
health_score = round((frq_under_budget/frq_categories)*100)

#Health Score Status
if health_score >= 80:
    health_status = "Healthy"
    health_status_color = "#28a745"
elif health_score >=50:
    health_status ="Monitor"
    health_status_color = "#ffc107"
else :
    health_status = "Need Action"
    health_status_color = "#dc3545"

#Insights Banner Type
if health_score >= 80:
    banner_type = "success"    # green
elif health_score >= 50:
    banner_type = "warning"    # yellow
else:
    banner_type = "error"      # red
       
#------------------------UI---------------------------

#Title

st.title("Finance Dashboard") #Header at Top of Page
st.markdown("Expense Tracker") # Smaller Supporeting Text
banner = getattr(st, banner_type) #Get Attribute Banner Type to display if (get attr object,name) 
banner(
    f"Insight : \n\n"
    f"Top Spending this Month : **{top_expense_category}** "
    f"at Rp {top_expense_amount:,.0f} "
    f"accounting for **{top_expense_portion}**% of Total Expenses"
)
st.divider() #Line Separator


#Metrics
col1,col3, col4 = st.columns(3) #Split page into 3 columns

col1.metric("Total Spent", f"Rp {total_expense:,.0f}") #.metric(label, value) 
#col2.metric("Avg Monthly Spend", f"Rp {monthly_avg:,.0f}") -- not relevant for now
col3.metric("Biggest Category", top_category)
col4.markdown(f""" 
<div>
    <p style="font-size:14px; color:gray; margin:0">
        Financial Health Score
    </p>
    <p style="font-size:32px; font-weight:bold; 
              color:{health_status_color}; margin:0">
        {health_score}%
    </p>
    <p style="font-size:14px; color:{health_status_color}; margin:0">
        {health_status}
    </p>
</div>
""", unsafe_allow_html=True)

st.divider()

#Chart 1
st.subheader("Expense per Category")

#Not using Bar Chart for now, Pie is more helpful
#chart1 = px.bar( 
   # x = category_totals.index,
   # y = category_totals.values,
    #labels={"x" :"Category", "y" :"Amount"},
    #color = category_totals.values,
   # color_continuous_scale="reds"
#)

chart1 = px.pie(
    names = category_totals.index,
    values = category_totals.values,
    title = "Expenses Breakdown per Category",
    hole = 0.4
)

chart1.update_traces(
    hovertemplate = "Category : %{label}<br>Amount : Rp%{value:,.0f}"
)
st.plotly_chart(chart1, use_container_width=True) #display ploty chart, stretch to page full width

#Chart 2 - DoD spending
chart_daily = px.line(
    daily_amounts,
    x ="Date",
    y = "Amount",
    title = "Daily Spendings",
    labels = {"Daily Total" : "Amount (Rp)", "Date":"Date"},
    markers = True
)

chart_daily.update_yaxes(tickprefix="Rp", tickformat =",.0f")
chart_daily.update_traces(
    hovertemplate ="Date : %{x}<br>Amount : Rp %{y:,.0f}"
)
st.plotly_chart(chart_daily, use_container_width=True)

#Chart 2
st.subheader("MoM Trend")

chart2 = px.line(
    monthly_total,
    x = "Month",
    y = "Total Calculated",
    labels={"Total_Calculated": "Amount (Rp)", "Month": "Month"},
    markers=True,
    category_orders={
        "Month" : df_filtered.sort_values("Month_Sort")["Month"].unique().tolist()
    }
)

chart2.update_xaxes(type="category")
chart2.update_yaxes(tickprefix="Rp ", tickformat=",.0f")
st.plotly_chart(chart2, use_container_width=True)



