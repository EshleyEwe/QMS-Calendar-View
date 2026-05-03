import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_calendar import calendar

st.set_page_config(page_title="Delay Tracker", layout="wide")

st.title("📊 Delay & Smart Calendar Tracker")

uploaded_file = st.file_uploader("📂 Upload Excel file", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df.columns = df.columns.str.strip()

    df.rename(columns={"ID": "Id"}, inplace=True)

    required_cols = ["Status", "Created Date", "End Date", "Dev Date"]
    missing = [col for col in required_cols if col not in df.columns]

    if missing:
        st.error(f"Missing required columns: {missing}")
    else:
        for col in required_cols:
            if "Date" in col:
                df[col] = pd.to_datetime(df[col], errors='coerce')

        today = pd.to_datetime(datetime.today().date())

        def get_status(row):
            status = row.get("Status")
            created = row.get("Created Date")
            end = row.get("End Date")
            dev = row.get("Dev Date")

            if status == "Develop":
                if pd.isna(end) and pd.notna(created):
                    if created + pd.Timedelta(days=14) < today:
                        return "Issue"
                    else:
                        return ""

            if status == "Develop" and pd.notna(end):
                if today > end:
                    return "Overdue"

            if status == "Develop" and pd.notna(dev):
                if today > dev:
                    return "Late"

            if status in ["Testing", "Verify"] and pd.notna(dev):
                if dev >= today:
                    return "On Time"

            return "On Track"

        df["Delay Status"] = df.apply(get_status, axis=1)

        df["Days"] = df.apply(lambda r: (today - r["End Date"]).days if r["Delay Status"]=="Overdue" and pd.notna(r["End Date"]) else
                                         (today - r["Dev Date"]).days if r["Delay Status"]=="Late" and pd.notna(r["Dev Date"]) else
                                         (r["Dev Date"] - today).days if pd.notna(r["Dev Date"]) else None, axis=1)

        tab1, tab2 = st.tabs(["📊 Dashboard", "📅 Calendar"])

        with tab1:
            st.subheader("📊 Key Metrics (Click to filter)")

            overdue_df = df[df["Delay Status"]=="Overdue"]
            late_df = df[df["Delay Status"]=="Late"]
            issue_df = df[df["Delay Status"]=="Issue"]
            ontime_df = df[df["Delay Status"]=="On Time"]
            ontrack_df = df[df["Delay Status"]=="On Track"]

            c1,c2,c3,c4 = st.columns(4)
            c1.metric("Total", len(df))
            c2.metric("Overdue ❌", len(overdue_df))
            c3.metric("Late ⚠️", len(late_df))
            c4.metric("Issue 🔵", len(issue_df))

            c5,c6,c7 = st.columns(3)
            c5.metric("On Time ✅", len(ontime_df))
            c6.metric("On Track", len(ontrack_df))
            c7.metric("Blank", (df["Delay Status"]=="").sum())

            st.subheader("🎯 Quick Filter")
            b1,b2,b3,b4,b5,b6 = st.columns(6)

            selected_df = df
            label = "All Data"

            if b1.button("Total"):
                selected_df = df
                label = "All Data"
            if b2.button("Overdue"):
                selected_df = overdue_df
                label = "Overdue"
            if b3.button("Late"):
                selected_df = late_df
                label = "Late"
            if b4.button("Issue"):
                selected_df = issue_df
                label = "Issue"
            if b5.button("On Time"):
                selected_df = ontime_df
                label = "On Time"
            if b6.button("On Track"):
                selected_df = ontrack_df
                label = "On Track"

            st.subheader(f"📋 Showing: {label}")

            if "Tester" in df.columns:
                tester_filter = st.multiselect("Filter Tester", df["Tester"].dropna().unique(), default=df["Tester"].dropna().unique())
                selected_df = selected_df[selected_df["Tester"].isin(tester_filter)]

            st.dataframe(selected_df, use_container_width=True)

        with tab2:
            st.subheader("📅 Calendar")

            events=[]
            for _,row in df.iterrows():
                if pd.notna(row.get("Dev Date")):
                    events.append({
                        "title": f"{row.get('Id','No Id')} | {row.get('Status')}",
                        "start": row["Dev Date"].strftime("%Y-%m-%d"),
                        "extendedProps": {k:str(v) for k,v in row.to_dict().items()}
                    })

            calendar(events=events, options={"initialView":"dayGridMonth"})
