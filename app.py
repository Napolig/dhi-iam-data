import streamlit as st
from supabase import create_client
import tomllib
import pandas as pd

st.set_page_config(page_title="DHI Pilot Portal", layout="wide")
st.title("DHI Pilot Portal")
st.markdown("""
### Upload your data

- Upload a CSV file using the agreed template
- The file must contain only one mechanism
- Existing data for that mechanism will be replaced

""")

template_df = pd.DataFrame({
    "mechanism_id": ["IPAM"],
    "case_id": ["2024/01"],
    "country": ["Serbia"],
    "year": [2024],
    "function_activated": ["Compliance"],
    "issue_category": ["Environmental"]
})

csv = template_df.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download template CSV",
    data=csv,
    file_name="template.csv",
    mime="text/csv",
)

# Load Secrets
with open("secrets.toml", "rb") as f:
    secrets = tomllib.load(f)

SUPABASE_URL = secrets["SUPABASE_URL"]
SUPABASE_KEY = secrets["SUPABASE_SECRET_KEY"]

# Create client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Mechanism selector for pilot
mechanism_selected = st.selectbox(
    "Select mechanism for this upload",
    ["IPAM", "CAO"]
)

uploaded_file = st.file_uploader("Upload CSV file", type="csv")

if uploaded_file is not None:
    try:
        # Read CSV
        # Legge il file così com'è, senza forzare header o nomi colonne
        df = pd.read_csv(uploaded_file)

        # Mostra l'anteprima del dataframe
        st.write("### Preview of uploaded file")
        st.dataframe(df, use_container_width=True)

        # Required columns
        required_columns = [
            "mechanism_id",
            "case_id",
            "country",
            "year",
            "function_activated",
            "issue_category",
        ]

        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            st.error(f"Missing required columns: {', '.join(missing_columns)}")
            st.stop()

        # Check mechanism_id consistency
        unique_mechanisms = df["mechanism_id"].dropna().unique().tolist()

        if len(unique_mechanisms) != 1:
            st.error("The file must contain only one mechanism_id.")
            st.stop()

        file_mechanism = unique_mechanisms[0]

        if file_mechanism != mechanism_selected:
            st.error(
                f"Mechanism mismatch: you selected '{mechanism_selected}' "
                f"but the file contains '{file_mechanism}'."
            )
            st.stop()

        # Optional: remove completely empty rows
        df = df.dropna(how="all")

        # Convert NaN to None for database compatibility
        records = df.where(pd.notnull(df), None).to_dict(orient="records")

        if st.button("Replace data in database"):
            # Delete old rows for this mechanism
            delete_response = (
                supabase.table("cases_master")
                .delete()
                .eq("mechanism_id", mechanism_selected)
                .execute()
            )
            st.write(f"Rows to upload: {len(df)}")
            st.write(f"Mechanism: {file_mechanism}")



            # Insert new rows
            insert_response = (
                supabase.table("cases_master")
                .insert(records)
                .execute()
            )

            st.success(
                f"Upload complete. Replaced data for {mechanism_selected} "
                f"with {len(records)} rows."
            )

            st.write("### Insert response")
            st.write(insert_response)

    except Exception as e:
        st.error(f"Error while processing file: {e}")

# Show current database content
st.write("## Current content of cases_master")

try:
    response = supabase.table("cases_master").select("*").execute()
    rows = response.data

    if rows:
        db_df = pd.DataFrame(rows)
        st.dataframe(db_df, use_container_width=True)
    else:
        st.info("No rows currently found in cases_master.")

except Exception as e:
    st.error(f"Could not read cases_master: {e}")