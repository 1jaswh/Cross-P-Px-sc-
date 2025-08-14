import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Market News", page_icon="📰", layout="wide")
st.title("📰 Latest Market News")

keyword = st.text_input("Filter by keyword (optional):", "")

if keyword:
    res = requests.get(f"http://localhost:8000/news?keyword={keyword}")
else:
    res = requests.get("http://localhost:8000/news")

if res.status_code != 200:
    st.error("Failed to fetch news.")
else:
    articles = res.json()
    if not articles:
        st.info("No news found for your search.")
    else:
        for article in articles:
            st.subheader(article["title"])
            st.write(article["summary"])
            st.markdown(f"[Read more]({article['url']})")
            st.caption(article["publishedAt"])
