import streamlit as st
import pandas as pd
import altair as alt
from supabase import create_client



# ===============================
# PAGE CONFIG
# ===============================
st.set_page_config(page_title="DHI Dashboard", layout="wide")


# ===============================
# SUPABASE CLIENT
# ===============================
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_SECRET_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# ===============================
# PAGE TITLE
# ===============================
st.title("DHI Dashboard")
st.caption("Visual overview from the current DHI database.")


# ===============================
# LOAD DATA
# ===============================

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Please log in from the main page to access the dashboard.")
    st.stop()

try:
    response = supabase.table("cases_master").select("*").execute()
    rows = response.data

    if not rows:
        st.info("No data available yet.")
        st.stop()

    df = pd.DataFrame(rows)

except Exception as e:
    st.error(f"Could not load data: {e}")
    st.stop()


# ===============================
# SUMMARY METRICS
# ===============================
col1, col2, col3 = st.columns(3)

col1.metric("Total cases", len(df))
col2.metric("Mechanisms", df["ownermechanism"].nunique())
col3.metric("Countries", df["country"].nunique())


# ===============================
# BASIC CHARTS
# ===============================

col_country, col_sector = st.columns(2)

with col_country:
    st.write("## Cases by country")

    country_df = (
        df["country"]
        .value_counts()
        .reset_index()
    )
    country_df.columns = ["country", "cases"]

    country_chart = (
        alt.Chart(country_df)
        .mark_bar(color="#003A70")
        .encode(
            x="cases:Q",
            y=alt.Y(
                "country:N",
                sort="-x",
                axis=alt.Axis(labelLimit=250)
                    ),
            tooltip=["country", "cases"]
        )
    )

    st.altair_chart(country_chart, use_container_width=True)


with col_sector:
    st.write("## Cases by sector")

    sector_df = (
        df["sector"]
        .value_counts()
        .reset_index()
    )
    sector_df.columns = ["sector", "cases"]

    sector_chart = (
        alt.Chart(sector_df)
        .mark_bar(color="#003A70")
        .encode(
            x="cases:Q",
            y=alt.Y(
                "sector:N",
                sort="-x",
                axis=alt.Axis(labelLimit=250)
            ),
            tooltip=["sector", "cases"]
        )
    )

    st.altair_chart(sector_chart, use_container_width=True)

col_year, col_env = st.columns(2)

with col_year:
    st.write("## Cases by year")

    df["year"] = pd.to_datetime(
        df["receptiondate"],
        errors="coerce"
    ).dt.year

    year_df = (
        df["year"]
        .value_counts()
        .sort_index()
        .reset_index()
    )

    year_df.columns = ["year", "cases"]

    year_chart = (
        alt.Chart(year_df)
        .mark_bar(color="#003A70")
        .encode(
            x="year:O",
            y="cases:Q",
            tooltip=["year", "cases"]
        )
    )

    st.altair_chart(year_chart, use_container_width=True)

with col_env:
    st.write("## Environmental categories")

    env_df = (
        df["environmentalcategory"]
        .value_counts()
        .reset_index()
    )

    env_df.columns = ["category", "cases"]

    env_chart = (
        alt.Chart(env_df)
        .mark_arc()
        .encode(
            theta="cases:Q",
            color=alt.Color("category:N"),
            tooltip=["category", "cases"]
        )
    )


    st.altair_chart(env_chart, use_container_width=True)

st.write("## Impact categories")

impact_columns = [
    "impactsocial",
    "impactcultural",
    "impactlivelihoods",
    "impactequity",
    "impacthealth",
    "impactlabour",
    "impactenvironmental",
    "impactproperty",
    "impactviolence",
    "impactstakeholderengagement",
    "impactunclassified"
]

impact_labels = {
    "impactsocial": "Social",
    "impactcultural": "Cultural",
    "impactlivelihoods": "Livelihoods",
    "impactequity": "Equity",
    "impacthealth": "Health",
    "impactlabour": "Labour",
    "impactenvironmental": "Environmental",
    "impactproperty": "Property",
    "impactviolence": "Violence",
    "impactstakeholderengagement": "Stakeholder engagement",
    "impactunclassified": "Unclassified",
}

impact_counts = {}

for col, label in impact_labels.items():
    impact_counts[label] = (
        df[col].fillna(0).astype(int).sum()
    )

impact_df = pd.DataFrame({
    "Impact": impact_counts.keys(),
    "Cases": impact_counts.values()
})

impact_chart = (
    alt.Chart(impact_df)
    .mark_bar(color="#003A70")
    .encode(
        x="Cases:Q",
        y=alt.Y("Impact:N", sort="-x"),
        tooltip=["Impact", "Cases"]
    )
)

st.altair_chart(impact_chart, use_container_width=True)