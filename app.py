import streamlit as st
from supabase import create_client
import pandas as pd


# =========================================================
# 1. PAGE CONFIG
# This must stay near the top of the file.
# =========================================================
st.set_page_config(page_title="DHI Pilot Portal", layout="wide")


# =========================================================
# 2. LOAD SECRETS
# Reads Supabase URL and secret key from local secrets.toml
# =========================================================

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_SECRET_KEY"]


# =========================================================
# 3. CREATE SUPABASE CLIENT
# This client is used both for authentication and database calls
# =========================================================
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# =========================================================
# 4. SESSION STATE
# These values stay in memory while the Streamlit session is open
# =========================================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user_email" not in st.session_state:
    st.session_state.user_email = None

if "user_id" not in st.session_state:
    st.session_state.user_id = None

if "ownerMechanism" not in st.session_state:
    st.session_state.ownerMechanism = None

if "user_role" not in st.session_state:
    st.session_state.user_role = None


# =========================================================
# 5. HELPER FUNCTIONS
# =========================================================
def login_user(email, password):
    """
    Sends email + password to Supabase Auth.
    If credentials are correct, Supabase returns an authenticated user.
    """
    response = supabase.auth.sign_in_with_password(
        {
            "email": email,
            "password": password,
        }
    )
    return response


def load_profile(user_id):
    """
    Reads the matching row from public.profiles.
    This is where we store the business information of the user:
    - ownerMechanism
    - role
    - approved
    """
    response = (
        supabase.table("profiles")
        .select("*")
        .eq("id", user_id)
        .execute()
    )

    if response.data:
        return response.data[0]

    return None


def logout():
    """
    Clears local session data.
    """
    st.session_state.logged_in = False
    st.session_state.user_email = None
    st.session_state.user_id = None
    st.session_state.ownerMechanism = None
    st.session_state.user_role = None


# =========================================================
# 6. APP HEADER
# UI starts only after Supabase is ready
# =========================================================
st.title("DHI IAM Datahub")


# =========================================================
# 7. LOGIN SECTION
# If the user is not logged in, show only the login form
# and stop the app there.
# =========================================================
if not st.session_state.logged_in:
    st.subheader("Login")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        try:
            auth_response = login_user(email, password)

            # Supabase returns the authenticated user here
            user = auth_response.user

            if user is None:
                st.error("Login failed.")
                st.stop()

            # Load user's profile from public.profiles
            profile = load_profile(user.id)

            if profile is None:
                st.error("No profile found for this user.")
                st.stop()

            if profile["approved"] is not True:
                st.error("This user is not approved.")
                st.stop()

            # Save important values into session state
            st.session_state.logged_in = True
            st.session_state.user_email = profile["email"]
            st.session_state.user_id = user.id
            st.session_state.ownerMechanism = profile["ownermechanism"]
            st.session_state.user_role = profile["role"]

            st.success("Login successful.")
            st.rerun()

        except Exception as e:
            st.error(f"Login error: {e}")

    # Stop the rest of the app if not logged in
    st.stop()


# =========================================================
# 8. USER INFO
# Once logged in, show who the user is
# =========================================================
st.success(f"Logged in as {st.session_state.user_email}")
st.write(f"Owner mechanism: {st.session_state.ownerMechanism}")
st.write(f"Role: {st.session_state.user_role}")

if st.button("Logout"):
    logout()
    st.rerun()

# =========================================================
# DOWNLOADS SECTION
# =========================================================
st.markdown("## Downloads")

# ---------------------------------------------------------
# 1. DHI Cases Master (filtered download)
# ---------------------------------------------------------
st.markdown("### DHI Cases Master")

try:
    export_response = supabase.table("cases_master").select("*").execute()
    export_rows = export_response.data

    if export_rows:
        export_df = pd.DataFrame(export_rows)

        # Let users choose what they want to download
        download_mode = st.radio(
            "Choose what to download",
            ["All mechanisms", "Only my mechanism", "Selected mechanisms"],
            horizontal=True,
        )

        filtered_df = export_df.copy()

        if download_mode == "Only my mechanism":
            filtered_df = filtered_df[
                filtered_df["ownermechanism"] == st.session_state.ownerMechanism
            ]

        elif download_mode == "Selected mechanisms":
            available_mechanisms = sorted(
                export_df["ownermechanism"].dropna().unique().tolist()
            )

            selected_mechanisms = st.multiselect(
                "Select one or more mechanisms",
                options=available_mechanisms,
            )

            if selected_mechanisms:
                filtered_df = filtered_df[
                    filtered_df["ownermechanism"].isin(selected_mechanisms)
                ]
            else:
                st.warning("Please select at least one mechanism.")
                filtered_df = None

        

        if filtered_df is not None:
            
            # Rename columns for users so the exported file follows the agreed standard
            filtered_df = filtered_df.rename(
                columns={
                    "id": "id",
                    "ownermechanism": "ownerMechanism",
                    "casename": "caseName",
                    "country": "country",
                    "typeofrequester": "typeOfRequester",
                    "representation": "representation",
                    "confidentiality": "confidentiality",
                    "caseurl": "caseURL",
                    "projectname": "projectName",
                    "sector": "sector",
                    "approvaldate": "approvalDate",
                    "typeofinvestment": "typeOfInvestment",
                    "environmentalcategory": "environmentalCategory",
                    "typeoflending": "typeOfLending",
                    "otherlenders": "otherLenders",
                    "projectstatus": "projectStatus",
                    "projectcountry": "projectCountry",
                    "clientname": "clientName",
                    "receptiondate": "receptionDate",
                    "eligibilitydate": "eligibilityDate",
                    "impactsocial": "impactSocial",
                    "impactcultural": "impactCultural",
                    "impactlivelihoods": "impactLivelihoods",
                    "impactequity": "impactEquity",
                    "impacthealth": "impactHealth",
                    "impactlabour": "impactLabour",
                    "impactenvironmental": "impactEnvironmental",
                    "impactproperty": "impactProperty",
                    "impactviolence": "impactViolence",
                    "impactstakeholderengagement": "impactStakeholderEngagement",
                    "impactunclassified": "impactUnclassified",
                }
            )
            
            st.write(f"Rows available for download: {len(filtered_df)}")

            export_csv = filtered_df.to_csv(index=False).encode("utf-8")

            st.download_button(
                label="Download DHI Cases Master",
                data=export_csv,
                file_name="DHI_Cases_Master.csv",
                mime="text/csv",
            )


    else:
        st.info("No data currently available for DHI Cases Master download.")

except Exception as e:
    st.error(f"Could not prepare DHI Cases Master download: {e}")


# ---------------------------------------------------------
# 2. Download empty template
# ---------------------------------------------------------
empty_template_df = pd.DataFrame(columns=[
    "id",
    "ownerMechanism",
    "caseName",
    "country",
    "typeOfRequester",
    "representation",
    "confidentiality",
    "caseURL",
    "projectName",
    "sector",
    "approvalDate",
    "typeOfInvestment",
    "environmentalCategory",
    "typeOfLending",
    "otherLenders",
    "projectStatus",
    "projectCountry",
    "clientName",
    "receptionDate",
    "eligibilityDate",
    "impactSocial",
    "impactCultural",
    "impactLivelihoods",
    "impactEquity",
    "impactHealth",
    "impactLabour",
    "impactEnvironmental",
    "impactProperty",
    "impactViolence",
    "impactStakeholderEngagement",
    "impactUnclassified",
])

empty_template_csv = empty_template_df.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download empty template",
    data=empty_template_csv,
    file_name="template_empty.csv",
    mime="text/csv",
)


# ---------------------------------------------------------
# 3. Glossary placeholder
# ---------------------------------------------------------
glossary_path = "assets/downloads/glossary.pdf"

try:
    with open(glossary_path, "rb") as f:
        st.download_button(
            label="Download Glossary",
            data=f,
            file_name="glossary.pdf",
            mime="application/pdf",
        )
except FileNotFoundError:
    st.info("Glossary not uploaded yet.")


# ---------------------------------------------------------
# 4. Concept Note placeholder
# ---------------------------------------------------------
concept_note_path = "assets/downloads/concept_note.pdf"

try:
    with open(concept_note_path, "rb") as f:
        st.download_button(
            label="Download Concept Note",
            data=f,
            file_name="concept_note.pdf",
            mime="application/pdf",
        )
except FileNotFoundError:
    st.info("Concept Note not uploaded yet.")


# =========================================================
# 10. EXPECTED SCHEMA
# This is the official list of columns that the upload must contain
# =========================================================
EXPECTED_COLUMNS = [
    "id",
    "ownermechanism",
    "casename",
    "country",
    "typeofrequester",
    "representation",
    "confidentiality",
    "caseurl",
    "projectname",
    "sector",
    "approvaldate",
    "typeofinvestment",
    "environmentalcategory",
    "typeoflending",
    "otherlenders",
    "projectstatus",
    "projectcountry",
    "clientname",
    "receptiondate",
    "eligibilitydate",
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
    "impactunclassified",
]



# =========================================================
# 11. FILE UPLOAD
# =========================================================
# =========================================================
# UPLOAD MODE
# User chooses whether to append new rows or replace all
# =========================================================
upload_mode = st.radio(
    "Choose upload mode",
    ["Append new rows", "Replace all my mechanism data"],
    horizontal=True,
)


replace_confirmed = False


if upload_mode == "Replace all my mechanism data":
    st.warning(
        "Warning: this will delete all existing data currently stored for your mechanism "
        "and replace it with the uploaded file. Are you sure you want to continue?"
    )


    replace_confirmed = st.checkbox(
        "Yes, I understand."
    )

uploaded_file = st.file_uploader("Upload CSV file", type="csv")

if uploaded_file is not None:
    try:
        # Read the uploaded CSV
        df = pd.read_csv(uploaded_file)

        # Trasnform the column names in lowercase for PostgreSQL
        df.columns = df.columns.str.lower()

        # Show preview so the user can verify what is being uploaded
        st.write("### Preview of uploaded file")
        st.dataframe(df, use_container_width=True)

        # -------------------------------------------------
        # Check that the uploaded file has exactly the agreed columns
        # -------------------------------------------------
        missing_columns = [col for col in EXPECTED_COLUMNS if col not in df.columns]
        extra_columns = [col for col in df.columns if col not in EXPECTED_COLUMNS]

        if missing_columns:
            st.error(f"Missing required columns: {', '.join(missing_columns)}")
            st.stop()

        if extra_columns:
            st.error(f"Unexpected columns found: {', '.join(extra_columns)}")
            st.stop()

        # Optional stricter check: exact column order
        if list(df.columns) != EXPECTED_COLUMNS:
            st.error("The file uses the right columns, but not in the agreed order.")
            st.stop()

        # -------------------------------------------------
        # Check that the file contains only one mechanism
        # -------------------------------------------------
        unique_mechanisms = df["ownermechanism"].dropna().unique().tolist()

        if len(unique_mechanisms) != 1:
            st.error("The file must contain only one ownerMechanism.")
            st.stop()

        file_mechanism = unique_mechanisms[0]

        # -------------------------------------------------
        # Compare file mechanism with logged-in user's mechanism
        # -------------------------------------------------
        if file_mechanism != st.session_state.ownerMechanism:
            st.error(
                f"Mechanism mismatch: your account is linked to "
                f"'{st.session_state.ownerMechanism}', but the file contains '{file_mechanism}'."
            )
            st.stop()

        # -------------------------------------------------
        # Clean dataframe
        # -------------------------------------------------

        df = df.dropna(how="all")

        # Convert date columns to proper date strings if possible
        # This helps avoid bad inserts if Excel/CSV formatting is inconsistent
        date_columns = ["approvaldate", "receptiondate", "eligibilitydate"]

        for col in date_columns:
            # Convert to datetime, then to string format YYYY-MM-DD
            df[col] = pd.to_datetime(df[col], errors="coerce").dt.strftime("%Y-%m-%d")


        # Convert NaN to None for database compatibility
        # Make dataframe JSON-safe before converting to records
        df_safe = df.astype(object).where(pd.notnull(df), None)

        records = df_safe.to_dict(orient="records")


        # Show a quick upload summary
        st.write(f"Rows to upload: {len(records)}")
        st.write(f"Mechanism detected in file: {file_mechanism}")

        # -------------------------------------------------
        # Replace old data for this mechanism with new uploaded data
        # -------------------------------------------------
        if st.button("Run upload"):
            # Stop replace mode unless the user explicitly confirmed it
            if upload_mode == "Replace all my mechanism data" and not replace_confirmed:
                st.error("Please confirm that you want to replace all existing rows for your mechanism.")
                st.stop()

            # Final safety check before any database modification
            if any(any(value != value for value in row.values() if isinstance(value, float)) for row in records):
                st.error(
                    "Upload stopped: the uploaded file still contains invalid values "
                    "(for example NaN). No existing data was deleted."
                )
                st.stop() 


            if upload_mode == "Replace all my mechanism data":
                # Backup current rows for this mechanism before doing anything destructive
                backup_response = (
                    supabase.table("cases_master")
                    .select("*")
                    .eq("ownermechanism", st.session_state.ownerMechanism)
                    .execute()
                )


                backup_rows = backup_response.data if backup_response.data else []


                # Delete old rows for this mechanism
                delete_response = (
                    supabase.table("cases_master")
                    .delete()
                    .eq("ownermechanism", st.session_state.ownerMechanism)
                    .execute()
                )

                try:
                    # Insert all uploaded rows
                    insert_response = (
                        supabase.table("cases_master")
                        .insert(records)
                        .execute()
                    )


                    st.success(
                        f"Upload complete. Replaced all data for {st.session_state.ownerMechanism} "
                        f"with {len(records)} rows."
                    )


                    st.write("### Insert response")
                    st.write(insert_response)


                except Exception as e:
                    # Try to restore previous rows if the replace insert fails
                    if backup_rows:
                        supabase.table("cases_master").insert(backup_rows).execute()


                    st.error(
                        "Replace upload failed. The system attempted to restore the previous data "
                        f"for {st.session_state.ownerMechanism}. Error: {e}"
                    )
                    st.stop()


                # Insert all uploaded rows
                insert_response = (
                    supabase.table("cases_master")
                    .insert(records)
                    .execute()
                )


                st.success(
                    f"Upload complete. Replaced all data for {st.session_state.ownerMechanism} "
                    f"with {len(records)} rows."
                )


                st.write("### Insert response")
                st.write(insert_response)


            elif upload_mode == "Append new rows":
                # Load existing rows for this mechanism
                existing_response = (
                    supabase.table("cases_master")
                    .select("*")
                    .eq("ownermechanism", st.session_state.ownerMechanism)
                    .execute()
                )


                existing_rows = existing_response.data if existing_response.data else []
                existing_df = pd.DataFrame(existing_rows)


                # If there is no data yet for this mechanism, all uploaded rows are new
                if existing_df.empty:
                    new_rows_df = df.copy()
                    conflict_rows_df = pd.DataFrame()
                else:
                    existing_ids = set(existing_df["id"].astype(str).tolist())
                    uploaded_ids = df["id"].astype(str)


                    new_rows_df = df[~uploaded_ids.isin(existing_ids)].copy()
                    conflict_rows_df = df[uploaded_ids.isin(existing_ids)].copy()


                st.write(f"New rows detected: {len(new_rows_df)}")
                st.write(f"Conflicting IDs detected: {len(conflict_rows_df)}")


                if not new_rows_df.empty:
                    st.write("### New rows that can be inserted immediately")
                    st.dataframe(new_rows_df, use_container_width=True)


                if not conflict_rows_df.empty:
                    st.write("### Rows with IDs already present in the database")
                    st.dataframe(conflict_rows_df, use_container_width=True)


                if new_rows_df.empty and conflict_rows_df.empty:
                    st.info("No rows available to append.")
                
                # Insert only the rows with brand-new IDs
                if not new_rows_df.empty:
                    new_rows_safe_df = new_rows_df.astype(object).where(pd.notnull(new_rows_df), None)
                    new_records = new_rows_safe_df.to_dict(orient="records")



                    insert_new_response = (
                        supabase.table("cases_master")
                        .insert(new_records)
                        .execute()
                    )


                    st.success(f"{len(new_rows_df)} new rows were appended successfully.")


                    st.write("### Append response")
                    st.write(insert_new_response)


                # If there are conflicts, do not update them yet
                if not conflict_rows_df.empty:
                    st.warning(
                        "Some uploaded rows have IDs that already exist in the database. "
                        "They were not updated yet. Conflict review will be added next."
                    )




    except Exception as e:
        st.error(f"Error while processing file: {e}")


# =========================================================
# 12. SHOW CURRENT DATABASE CONTENT
# For now we still show the full table.
# Later we can restrict visibility by role/mechanism if needed.
# =========================================================
st.write("## Current content of cases_master")

try:
    response = supabase.table("cases_master").select("*").execute()
    rows = response.data

    if rows:
        db_df = pd.DataFrame(rows)

    # Rename columns for display only, so users see the agreed standard
        db_df = db_df.rename(
            columns={
                "id": "id",
                "ownermechanism": "ownerMechanism",
                "casename": "caseName",
                "country": "country",
                "typeofrequester": "typeOfRequester",
                "representation": "representation",
                "confidentiality": "confidentiality",
                "caseurl": "caseURL",
                "projectname": "projectName",
                "sector": "sector",
                "approvaldate": "approvalDate",
                "typeofinvestment": "typeOfInvestment",
                "environmentalcategory": "environmentalCategory",
                "typeoflending": "typeOfLending",
                "otherlenders": "otherLenders",
                "projectstatus": "projectStatus",
                "projectcountry": "projectCountry",
                "clientname": "clientName",
                "receptiondate": "receptionDate",
                "eligibilitydate": "eligibilityDate",
                "impactsocial": "impactSocial",
                "impactcultural": "impactCultural",
                "impactlivelihoods": "impactLivelihoods",
                "impactequity": "impactEquity",
                "impacthealth": "impactHealth",
                "impactlabour": "impactLabour",
                "impactenvironmental": "impactEnvironmental",
                "impactproperty": "impactProperty",
                "impactviolence": "impactViolence",
                "impactstakeholderengagement": "impactStakeholderEngagement",
                "impactunclassified": "impactUnclassified",
            }
        )

        st.dataframe(db_df, use_container_width=True)
    else:
        st.info("No rows currently found in cases_master.")


except Exception as e:
    st.error(f"Could not read cases_master: {e}")
