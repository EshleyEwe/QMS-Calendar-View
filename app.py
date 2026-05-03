import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_calendar import calendar

st.set_page_config(page_title="Delay Tracker Ultimate", layout="wide")
st.title("🚀 Delay Tracker Ultimate (Dashboard + Smart Calendar)")

file = st.file_uploader("📂 Upload Excel file", type=["xlsx"])

if file:
    df = pd.read_excel(file)
    df.columns = df.columns.str.strip().str.title()

    df.rename(columns={"Id": "Id", "ID": "Id"}, inplace=True)

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
                if c+pd.Timedelta(days=14)<today:
                    return "Issue"
                else:
                    return ""

        if s=="Develop" and pd.notna(e):
            if today>e:
                return "Overdue"

        if s=="Develop" and pd.notna(d):
            if today>d:
                return "Late"

        if s in ["Testing","Verify"] and pd.notna(d):
            if d>=today:
                return "On Time"

        return "On Track"

    df["Delay Status"]=df.apply(get_status,axis=1)

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

    # DASHBOARD
    with tab1:
        st.subheader("📊 KPI (Click to filter)")

        overdue=df[df["Delay Status"]=="Overdue"]
        late=df[df["Delay Status"]=="Late"]
        issue=df[df["Delay Status"]=="Issue"]
        ontime=df[df["Delay Status"]=="On Time"]
        ontrack=df[df["Delay Status"]=="On Track"]

        c1,c2,c3,c4=st.columns(4)
        c1.metric("Total",len(df))
        c2.metric("Overdue",len(overdue))
        c3.metric("Late",len(late))
        c4.metric("Issue",len(issue))

        c5,c6,c7=st.columns(3)
        c5.metric("On Time",len(ontime))
        c6.metric("On Track",len(ontrack))
        c7.metric("Blank",(df["Delay Status"]=="").sum())

        st.subheader("🎯 Quick Filter")
        b1,b2,b3,b4,b5,b6=st.columns(6)

        selected=df
        label="All"

        if b1.button("Total"): selected,label=df,"All"
        if b2.button("Overdue"): selected,label=overdue,"Overdue"
        if b3.button("Late"): selected,label=late,"Late"
        if b4.button("Issue"): selected,label=issue,"Issue"
        if b5.button("On Time"): selected,label=ontime,"On Time"
        if b6.button("On Track"): selected,label=ontrack,"On Track"

        if "Tester" in df.columns:
            tester=st.multiselect("Filter Tester",
                                 df["Tester"].dropna().unique(),
                                 default=df["Tester"].dropna().unique())
            selected=selected[selected["Tester"].isin(tester)]

        st.subheader(f"📋 Showing: {label}")
        st.dataframe(selected, use_container_width=True)

    # CALENDAR
    with tab2:
        st.subheader("📅 Smart Calendar (Never Empty)")

        date_mode=st.selectbox("Date Source",
                              ["Auto","Dev Date","End Date","Created Date"])

        events=[]
        for _,r in df.iterrows():
            d=None

            if date_mode=="Dev Date" and pd.notna(r["Dev Date"]):
                d=r["Dev Date"]
            elif date_mode=="End Date" and pd.notna(r["End Date"]):
                d=r["End Date"]
            elif date_mode=="Created Date" and pd.notna(r["Created Date"]):
                d=r["Created Date"]
            elif date_mode=="Auto":
                if pd.notna(r["Dev Date"]):
                    d=r["Dev Date"]
                elif pd.notna(r["End Date"]):
                    d=r["End Date"]
                elif pd.notna(r["Created Date"]):
                    d=r["Created Date"]

            if d is not None:
                events.append({
                    "title": f"{r.get('Id','No Id')} | {r.get('Status')}",
                    "start": d.strftime("%Y-%m-%d"),
                    "extendedProps": {k:str(v) if pd.notna(v) else "" for k,v in r.to_dict().items()}
                })

        st.write(f"Events: {len(events)}")

        if not events:
            st.warning("No calendar data - check dates")
        else:
            cal=calendar(events=events, options={"initialView":"dayGridMonth","height":700})

            if cal and "eventClick" in cal:
                e=cal["eventClick"]["event"]
                st.subheader("📌 Details")
                with st.expander("View Full Details", True):
                    df_detail=pd.DataFrame(e["extendedProps"].items(), columns=["Field","Value"])
                    st.dataframe(df_detail, use_container_width=True)
