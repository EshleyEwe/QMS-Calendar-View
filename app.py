import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_calendar import calendar

st.set_page_config(page_title="Delay Tracker Ultimate", layout="wide")
st.title("🚀 Delay Tracker Ultimate (Clean Display Version)")

file = st.file_uploader("📂 Upload Excel file", type=["xlsx"])

if file:
    df = pd.read_excel(file)
    df.columns = df.columns.str.strip().str.title()
    df.rename(columns={"ID": "Id"}, inplace=True)

    required = ["Status","Created Date","End Date","Dev Date"]
    missing = [c for c in required if c not in df.columns]

    if missing:
        st.error(f"Missing columns: {missing}")
        st.stop()

    for c in required:
        df[c] = pd.to_datetime(df[c], errors="coerce")

    today = pd.to_datetime(datetime.today().date())

    def get_status(r):
        s=r.get("Status")
        c=r.get("Created Date")
        e=r.get("End Date")
        d=r.get("Dev Date")

        if s=="Develop":
            if pd.isna(e) and pd.notna(c):
                return "Issue" if c+pd.Timedelta(days=14)<today else ""
        if s=="Develop" and pd.notna(e) and today>e:
            return "Overdue"
        if s=="Develop" and pd.notna(d) and today>d:
            return "Late"
        if s in ["Testing","Verify"] and pd.notna(d) and d>=today:
            return "On Time"
        return "On Track"

    df["Delay Status"]=df.apply(get_status,axis=1).fillna("")

    def calc_days(r):
        if r["Delay Status"]=="Overdue" and pd.notna(r["End Date"]):
            return (today-r["End Date"]).days
        if r["Delay Status"]=="Late" and pd.notna(r["Dev Date"]):
            return (today-r["Dev Date"]).days
        if pd.notna(r["Dev Date"]):
            return (r["Dev Date"]-today).days
        return None

    df["Days"]=df.apply(calc_days,axis=1)

    tab1,tab2=st.tabs(["📊 Dashboard","📅 Calendar"])

    with tab1:
        st.subheader("📊 Dashboard")

        display_df = df.copy().fillna("")

        for col in ["Created Date","End Date","Dev Date"]:
            if col in display_df.columns:
                display_df[col] = display_df[col].apply(
                    lambda x: x.strftime("%Y-%m-%d") if isinstance(x, pd.Timestamp) else ""
                )

        cols = ["Id","Status","Delay Status","Tester","Days","Dev Date","End Date","Created Date"]
        cols = [c for c in cols if c in display_df.columns]
        display_df = display_df[cols]

        st.dataframe(display_df, use_container_width=True)

    with tab2:
        st.subheader("📅 Calendar")

        events=[]
        for _,r in df.iterrows():
            d=None
            if pd.notna(r["Dev Date"]):
                d=r["Dev Date"]
            elif pd.notna(r["End Date"]):
                d=r["End Date"]
            elif pd.notna(r["Created Date"]):
                d=r["Created Date"]

            if d is not None:
                events.append({
                    "title": f"{r.get('Id','No Id')} | {r.get('Status')} | {r.get('Delay Status')}",
                    "start": d.strftime("%Y-%m-%d"),
                    "extendedProps": {k:str(v) if pd.notna(v) else "" for k,v in r.to_dict().items()}
                })

        if not events:
            st.warning("No calendar data")
        else:
            cal=calendar(events=events, options={"initialView":"dayGridMonth","height":700})

            if cal and "eventClick" in cal:
                e=cal["eventClick"]["event"]
                with st.expander("🔍 Full Details", True):
                    details_df = pd.DataFrame(e["extendedProps"].items(), columns=["Field","Value"])
                    st.dataframe(details_df, use_container_width=True)
