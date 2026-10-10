import streamlit as st
import plotly.express as px
import pandas as pd
import sys
import os

APP_DIR = r"C:\Users\Emerson Anwar\Desktop\Projects\App"
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)
from Utils import load_data, expense_cols, budgets, get_sidebar_single, round_to_50, color_value, get_scaled_data

st.set_page_config(
    page_title="Budget Analysis",
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

#-------------------------Calculations-----------------------------------------------------

#Set Filter Months
df_filtered, month_filter,active_budget = get_sidebar_single(df)

#Calculator
months_count = df_filtered["Month"].nunique() #count unique months
actual_avg = (df_filtered[expense_cols].sum() / months_count).round(0)

total_budget = sum(active_budget.values()) #sum all the values in budgets
total_actual = actual_avg.sum()
total_difference = total_budget - total_actual

#Get Table via pandas dataframe -- column name : values from the column
budget_df = pd.DataFrame({ 
    "Category" : expense_cols,
    "Budget" : [active_budget[col] for col in expense_cols], #for each column in expense columns, get value from budgets 
    "Actual" : [actual_avg[col] for col in expense_cols]

})

#Difference Table
budget_df["Difference"] = budget_df["Budget"] - budget_df["Actual"]
budget_df["Status"] = budget_df["Difference"].apply(
    lambda x : "Under Budget" if x >= 0 else "Over Budget"
)
#lambda = phyton's built in keyword, structure is : lambda input [input] : What to return
#this can be used for 1 time use function, used inside another function

budget_df["Usage %"] = (
    ((budget_df["Actual"] / budget_df ["Budget"]) * 100).replace([float("inf"), float("nan")],0) #Replace infinity with 0
    .round(1)
    .astype(str) +"%" #convert to string, to add % to it
)

budget_df["Recommended"] = budget_df["Actual"].apply(
    lambda x : round_to_50(x)
)

budget_df["Change"] =(
     budget_df["Recommended"] - budget_df["Budget"]
    )

budget_df["Change%"] =(
    ((budget_df["Change"]/budget_df["Budget"])*100)
    .round(1)
)




#Build Health Score
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

summary_df = budget_df[[
    "Category",
    "Budget",
    "Actual",
    "Difference",
    "Status",
    "Usage %"
]].copy()

for col in ["Budget", "Actual","Difference"]:
    summary_df[col] = summary_df[col].apply(lambda x : f"Rp{x:,.0f}")


#------------------------------UI------------------------------------------

#Call Sidebar and df_filtered


st.title("Budget Analysis")
st.markdown("To use for Analyzing Monthly Budgets")
st.divider()

#Metrics
col1, col3, col4 = st.columns(3)

col1.metric(
    "Monthly Budget",
    f"Rp{total_budget:,.0f}"
)

#Scrapping this for now as it's irrelevant
#col2.metric(
    #"Avg Monthly Actual",
    #f"Rp{total_actual:,.0f}"
#)

col3.metric(
    "Monthly Difference",
    f"Rp {total_difference:,.0f}",
    delta=int(total_difference), #add indicator under metric, Under if below 0, Over if above 0
    delta_color="normal"
)

#Using markdown to add CSS stylings to the component
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

# Sect 2 Each Category's Budget vs Actual Comparison
st.subheader("Budgets vs Actual per Category")


chart_budget = px.bar(
    budget_df,
    x = "Category",
    y=["Budget","Actual"],
    title = "Budget vs Actual per Category",
    labels = {"value":"Amount(Rp)", "variable" :"Type"},
    barmode="group", #bar sits side by side, there's also "stack" to stack the bar
    color_discrete_map={
        "Budget": "#636EFA",
        "Actual": "#EF553B"
    })

chart_budget.update_yaxes(tickprefix="Rp ", tickformat=",.0f")
chart_budget.update_traces(
    hovertemplate="Category: %{x}<br>Amount: Rp %{y:,.0f}"
)
st.plotly_chart(chart_budget, use_container_width=True)

st.divider()

#Sect 3 - Summary Table
st.subheader("Category Breakdown")

def style_status(val):
    if "Under" in str(val):
        return (
            "background-color: #d4edda;"  # light green background
            "color: #155724;"              # dark green text
            "border-radius: 8px;"          # rounded corners = pill
            "padding: 2px 8px;"            # spacing inside pill
        )
    elif "Over" in str(val):
        return (
            "background-color: #f8d7da;"  # light red background
            "color: #721c24;"             # dark red text
            "border-radius: 8px;"
            "padding: 2px 8px;"
        )
    return ""

def style_table(df):
    return df.style \
        .map(lambda v: color_value(v, "positive"), subset=["Difference"]) \
        .map(lambda v: color_value(v, "negative"), subset=["Usage %"]) \
        .map(style_status, subset = ["Status"])

#df.style = activate pandas styling engine
#.map applies function to every cell, subset - applies to specific column
#\ for line continuation


#Use this Try-Except for rizky situation - converting types that might fail, reading files that may ot exist, for user input cases later
#Use this when u cannot predict the result

st.dataframe(
    style_table(summary_df),
    use_container_width=True,
    hide_index=True
    
)

#------------ RECOMMENDED BUDGET TABLE ---------------------------------
st.divider()
st.subheader("Recommended Budgets")
st.caption("Based on Current Month Budget")

recom_budget_df = budget_df[[
    "Category",
    "Budget",
    "Recommended",
    "Change",
    "Change%"
        ]].copy() #Copy to prevent changes to column we're getting from 

#Budgeting Calcs
total_prev_budget = recom_budget_df["Budget"].sum()
total_recom_budget = recom_budget_df["Recommended"].sum()
total_budget_diff = recom_budget_df["Change"].sum()
total_budget_diff_pct = (
    ((total_budget_diff/total_prev_budget)*100)
    .round(1)
)

for col in ["Budget","Recommended","Change"]:
    recom_budget_df[col] = recom_budget_df[col].apply(lambda x : f"Rp{x:,.0f}")

recom_budget_df ["Change%"] = recom_budget_df["Change%"].apply(
    lambda x : f"+{x:.1f}%" if x > 0 else f"{x:.1f}%"    #Shows + if positive and auto-show - if negative
)

def style_rec_table(df):
    return df.style \
        .map(
            lambda v: color_value(v, "decrease"),
            subset=["Change"]
        ) \
        .map(
            lambda v: color_value(v, "decrease"),
            subset=["Change%"]
        )

st.dataframe(
    style_rec_table(recom_budget_df),
    use_container_width=True,
    hide_index=True
)



recom_col1, recom_col2, recom_col3 = st.columns(3)

recom_col1.metric(
    "Current Budget",
    f"Rp{total_prev_budget:,.0f}"
)

recom_col2.metric(
    "Recommended Budget",
    f"Rp{total_recom_budget:,.0f}"
)

recom_col3.metric(
    "Changes",
    f"Rp{total_budget_diff:,.0f}",
    delta=f"{total_budget_diff_pct:+.1f}%",
    delta_color="inverse"
)

#------------------------RECOM BASED ON HISTORICAL AVG-----------------------------------

#CALCS
avg_month_spend = df.groupby("Month")[expense_cols].sum().mean().round(0)
avg_historical_recom = avg_month_spend.apply(
    lambda x: round_to_50(x)
)


avg_budget_df = pd.DataFrame({
    "Category" : expense_cols,
    "Current Budget" : [active_budget[col] for col in expense_cols],
    "Average Spend": [avg_month_spend[col] for  col in expense_cols],
    "Recommended" :[avg_historical_recom[col] for col in expense_cols] ,
}
)


avg_budget_df["Change"] = (
    avg_budget_df["Recommended"] - avg_budget_df["Current Budget"]
)

avg_budget_df["Change%"] = (
    (avg_budget_df["Change"]/avg_budget_df["Current Budget"]*100).round(1)
)

avg_display_df = avg_budget_df.copy()
for col in ["Current Budget", "Average Spend", "Recommended","Change"]:
    avg_display_df[col] = avg_display_df[col].apply(
        lambda x : f"Rp{x:,.0f}"
        )

avg_display_df["Change%"] = avg_display_df["Change%"].apply(
    lambda x : f"+{x:.1f}%" if x > 0 else f"{x:.1f}%"    #Shows + if positive and auto-show - if negative
)

total_prev_budget_avg = avg_budget_df["Current Budget"].sum()
total_recom_budget_avg = avg_budget_df["Recommended"].sum()
total_budget_diff_avg = avg_budget_df["Change"].sum()
total_budget_diff_pct_avg = (
    ((total_budget_diff_avg/total_prev_budget_avg)*100)
    .round(1)
)

#UI
st.caption("Based on Historical Average")
st.dataframe(
    style_rec_table(avg_display_df),
    use_container_width=True,
    hide_index=True
)

avg_col1, avg_col2, avg_col3 = st.columns(3)

avg_col1 = avg_col1.metric("Current Budget", f"Rp {total_prev_budget_avg:,.0f}")
avg_col2 = avg_col2.metric("Recommended Budget", f"Rp {total_recom_budget_avg:,.0f}")
avg_col3 = avg_col3.metric(
    "Changes",
    f"Rp {total_budget_diff_avg:,.0f}",
    delta=f"{total_budget_diff_pct_avg:+.1f}%",
    delta_color="inverse"
)

