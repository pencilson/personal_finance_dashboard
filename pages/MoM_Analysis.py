import streamlit as st
import plotly.express as px
import pandas as pd
import sys
import os

APP_DIR = r"C:\Users\Emerson Anwar\Desktop\Projects\App"
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)
from Utils import load_data, expense_cols, budgets, privacy_toggle, round_to_50, color_value, scale_data

st.set_page_config(page_title="Month to Month Analysis", layout="wide")

@st.cache_data
def get_data():
    return load_data()

df, is_demo = get_data()

if is_demo:
    st.sidebar.warning("Demo - DATA IS NOT REAL")

if privacy_toggle():
    df, factor = scale_data(df)



#----------CALCS--------------
monthly_category = (
    df.groupby(["Month_Sort","Month"])[expense_cols] #Group expense cols by 2 column, Month Sort & month
    .sum()
    .reset_index()
    .sort_values("Month_Sort")
)

monthly_category["Total"] = monthly_category[expense_cols].sum(axis=1)
monthly_category["Change"] = monthly_category["Total"].diff() # diff function, this row minus previous row
monthly_category["Change %"] =(monthly_category["Total"].pct_change()*100).round(1)

latest = monthly_category.iloc[-1]
previous = monthly_category.iloc[-2]

category_difference = latest[expense_cols] - previous[expense_cols]
biggest_increase = category_difference.idxmax()
biggest_decrease = category_difference.idxmin()

#--------------UI----------------
st.title("Month to Month Analysis")

col1, col2, col3 = st.columns(3)

col1.metric(
    f"{latest['Month']} Total",
    f"Rp {latest['Total']:,.0f}",
    f"{latest['Change %']}% vs {previous['Month']}",
    delta_color="inverse"
)

col2.metric(
    "Biggest Increase",
    biggest_increase,
    f"Rp{category_difference[biggest_increase]:,.0f}",
    delta_color="inverse"
)

col3.metric(
    "Biggest Decrease",
    biggest_decrease,
    f"Rp{category_difference[biggest_decrease]:,.0f}",
    delta_color="inverse"
)

#---------------CHARTS--------------------
st.subheader("MoM Expense Trend")
fig_total = px.line(
    monthly_category,
    x ="Month",
    y = "Total",
    markers=True
    )

fig_total.update_xaxes(type="category")
fig_total.update_yaxes(tickprefix="Rp ", tickformat=",.0f")
st.plotly_chart(fig_total, use_container_width=True)

st.subheader("MoM Category Trend")
melted = monthly_category.melt(
    id_vars=["Month_Sort", "Month"], #Identifier to change format from wide to long
    value_vars=expense_cols, #Expense Columns to be collapsed into rows
    var_name="Category", #Expense Cols to be changed to Category
    value_name="Amount",  #Column Values to be changed to Amount
)

fig_cat = px.line(melted, x="Month", y="Amount", color="Category", markers=True)
fig_cat.update_xaxes(type="category")
fig_cat.update_yaxes(tickprefix="Rp ", tickformat=",.0f")

st.plotly_chart(fig_cat, use_container_width=True)

st.subheader("Monthly Summary")

st.dataframe(
    monthly_category[["Month","Total","Change","Change %"]],
    use_container_width=True,
    hide_index=True,
    column_config={
        "Total": st.column_config.NumberColumn("Total", format="Rp %,d"),
        "Change": st.column_config.NumberColumn("Change", format="Rp %,d"),
        "Change %": st.column_config.NumberColumn("Change %", format="%.1f%%"),
    }
)

