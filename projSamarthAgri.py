#!/usr/bin/env python
# -*- coding: utf-8 -*-


import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="My Dashboard", layout="wide", initial_sidebar_state="expanded")

@st.cache_data
def load_data():
    return pd.read_csv('Agriculture.csv', encoding='utf-8')

df = load_data()

def top_crops(agri_df, state, N_years, M):
    if 'Year' not in agri_df.columns:
        agri_df['Year'] = agri_df['Arrival_Date'].str[-4:].astype(int)
    if 'Production' not in agri_df.columns:
        agri_df['Production'] = agri_df['Modal_x0020_Price']
    recent_years = sorted(agri_df['Year'].unique())[-N_years:]
    filtered = agri_df[(agri_df['State'] == state) & (agri_df['Year'].isin(recent_years))]
    top = filtered.groupby('Commodity')['Production'].sum().sort_values(ascending=False).head(M)
    return top

def district_highest_crop(agri_df, state, crop):
    if 'Year' not in agri_df.columns:
        agri_df['Year'] = agri_df['Arrival_Date'].str[-4:].astype(int)
    if 'Production' not in agri_df.columns:
        agri_df['Production'] = agri_df['Modal_x0020_Price']
    year = agri_df['Year'].max()
    subset = agri_df[(agri_df['State']==state) & (agri_df['Commodity']==crop) & (agri_df['Year']==year)]
    crop_by_dist = subset.groupby('District')['Production'].sum()
    if not crop_by_dist.empty:
        top_district = crop_by_dist.idxmax()
        top_value = crop_by_dist.max()
        return top_district, top_value, year
    else:
        return None, None, year


def answer_question(question):
    q = question.lower()
    if "modal price" in q:
        for crop in df['Commodity'].unique():
            if crop.lower() in q:
                for state in df['State'].unique():
                    if state.lower() in q:
                        subdf = df[(df['Commodity']==crop) & (df['State']==state)]
                        if not subdf.empty:
                            latest = subdf[subdf['Arrival_Date'] == subdf['Arrival_Date'].max()]
                            modal = latest.iloc[0]['Modal_x0020_Price']
                            return f"Modal price for {crop} in {state} (on {latest.iloc[0]['Arrival_Date']}): {modal}"
    
    if "crops in" in q or "commodities in" in q:
        for state in df['State'].unique():
            if state.lower() in q:
                crops = df[df['State']==state]['Commodity'].unique()
                return f"Crops/commodities in {state}: {', '.join(crops)}"
    
    m = re.search(r'top (\d+) crops in (\w+) in last (\d+) years', q)
    if m:
        M = int(m.group(1))
        state = m.group(2).title()
        N = int(m.group(3))
        results = top_crops(df, state, N, M)
        return f"Top {M} crops in {state} (last {N} years):\n" + "\n".join([f"{i+1}. {name}: {value}" for i, (name, value) in enumerate(results.items())])
    
    m = re.search(r'district with highest production of ([\w ]+) in ([\w ]+)', q)
    if m:
        crop = m.group(1).title()
        state = m.group(2).title()
        dist, val, yr = district_highest_crop(df, state, crop)
        if dist:
            return f"District with highest production of {crop} in {state} (year {yr}): {dist} ({val})"
        else:
            return "No data found for that query."
    
    if "price" in q and "district" in q:
        for crop in df['Commodity'].unique():
            if crop.lower() in q:
                for district in df['District'].unique():
                    if district.lower() in q:
                        subdf = df[(df['Commodity']==crop) & (df['District']==district)]
                        if not subdf.empty:
                            rows = subdf[['Market','Min_x0020_Price','Max_x0020_Price','Modal_x0020_Price']]
                            answer = "\n".join(
                                [f"Market: {r.Market}, Min: {r.Min_x0020_Price}, Max: {r.Max_x0020_Price}, Modal: {r.Modal_x0020_Price}"
                                 for r in rows.itertuples()])
                            return f"Prices for {crop} in {district}:\n" + answer
    return "Sorry, I couldn't answer that question yet."


st.sidebar.header("Controls")
option = st.sidebar.selectbox("Choose category:", df["Commodity"].unique() if "Commodity" in df.columns else ["A", "B", "C"])

st.title("Dashboard: ")
st.write("Visualize and interact with your data here.")

if "Commodity" in df.columns and "Modal_x0020_Price" in df.columns:
    filtered = df[df["Commodity"] == option]
    data = filtered[["Arrival_Date", "Modal_x0020_Price"]].set_index("Arrival_Date")
else:
    st.warning("Data columns missing for dashboard demo.")
    data = pd.DataFrame({"Demo": [123, 450, 800]}, index=["2021-01-01", "2021-02-01", "2021-03-01"])

col1, col2 = st.columns([2, 1])
with col1:
    st.subheader(f"{option} Price Trend")
    st.line_chart(data)
with col2:
    if not data.empty:
        st.metric(label="Current Value", value=data.iloc[-1, 0])

st.subheader("Raw Data Table")
st.dataframe(data)


st.title("Agriculture Data Q&A Chatbot")
st.write("Ask questions like: 'modal price for Tomato in Andhra Pradesh', 'crops in Maharashtra', 'top 5 crops in Punjab in last 3 years', or 'district with highest production of Tomato in Andhra Pradesh'.")

question = st.text_input("Type your question:")

if question:
    answer = answer_question(question)
    st.markdown(f"**Answer:** {answer}")

st.write("##### Example questions:")
st.code("modal price for Tomato in Andhra Pradesh")
st.code("crops in Maharashtra")
st.code("top 5 crops in Punjab in last 3 years")
st.code("district with highest production of Tomato in Andhra Pradesh")
st.code("price of Maize in Guntur district")

if st.checkbox("Show raw data sample for Q&A"):
    st.write(df.head(10))
