import streamlit as st
import pandas as pd
from thefuzz import process

# ─── PAGE CONFIG ───
st.set_page_config(page_title="BRINC DFR Optimizer", page_icon="🚁", layout="wide")
st.title("BRINC DFR · Operator Schedule Optimizer")
st.markdown("Upload CAD data · ML Processed · Generate optimal shifts")

# ─── ML COLUMN DETECTION ───
TARGET_COLUMNS = {
    'date': ['date', 'received', 'timestamp', 'time', 'datetime', 'incident date', 'dispatch time'],
    'nature': ['nature', 'type', 'incident type', 'problem', 'description', 'call type', 'nature of call'],
    'priority': ['priority', 'level', 'urgency', 'pri'],
    'x': ['x', 'longitude', 'lon', 'long', 'x_coord', 'lng'],
    'y': ['y', 'latitude', 'lat', 'y_coord'],
    'address': ['address', 'location', 'street', 'block'],
    'callnum': ['call', 'incident', 'number', 'event', 'cad number']
}

def identify_columns(df_columns):
    mapped_columns = {}
    for target, aliases in TARGET_COLUMNS.items():
        best_match, best_score = None, 0
        for actual_col in df_columns:
            for alias in aliases:
                score = process.extractOne(alias, [str(actual_col).lower()])[1]
                if score > best_score:
                    best_score = score
                    best_match = actual_col
        if best_score > 70:
            mapped_columns[target] = best_match
    return mapped_columns

# ─── UI: SIDEBAR CONTROLS ───
with st.sidebar:
    st.header("Settings")
    shift_hours = st.selectbox("Shift Length", [8, 10, 12], index=1)
    min_priority = st.selectbox("Min Priority", [1, 2, 3, 4, 99], index=1, format_func=lambda x: "All" if x == 99 else f"Priority 1-{x}")
    ops_per_shift = st.selectbox("Operators / Shift", [1, 2, 3, 4], index=1)

# ─── UI: FILE UPLOAD ───
uploaded_file = st.file_uploader("Drop your CAD calls CSV here", type=["csv"])

if uploaded_file is not None:
    with st.spinner("Processing CAD data with Machine Learning..."):
        # 1. Load Data
        df = pd.read_csv(uploaded_file)
        col_map = identify_columns(df.columns)
        
        if 'date' not in col_map:
            st.error("ML Parser could not identify a Date column. Please check your CSV.")
            st.stop()

        # 2. Clean Data (Just like we did in ss.py)
        clean_df = pd.DataFrame()
        clean_df['dateStr'] = df[col_map['date']].astype(str)
        parsed_dates = pd.to_datetime(clean_df['dateStr'], errors='coerce')
        clean_df['hour'] = parsed_dates.dt.hour
        
        if 'priority' in col_map:
            clean_df['priority'] = pd.to_numeric(df[col_map['priority']], errors='coerce').fillna(9).astype(int)
        else:
            clean_df['priority'] = 9
            
        clean_df['nature'] = df[col_map['nature']].astype(str) if 'nature' in col_map else 'UNKNOWN'
        clean_df['lat'] = pd.to_numeric(df[col_map['y']], errors='coerce') if 'y' in col_map else None
        clean_df['lon'] = pd.to_numeric(df[col_map['x']], errors='coerce') if 'x' in col_map else None
        
        clean_df = clean_df.dropna(subset=['hour'])
        
        # 3. Filter by User Settings
        if min_priority != 99:
            filtered_df = clean_df[clean_df['priority'] <= min_priority]
        else:
            filtered_df = clean_df

        st.success(f"✓ Successfully processed {len(filtered_df):,} incidents.")

        # ─── UI: KPIS ───
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Incidents", f"{len(clean_df):,}")
        col2.metric("Filtered Calls", f"{len(filtered_df):,}")
        
        p12_count = len(clean_df[clean_df['priority'] <= 2])
        col3.metric("Priority 1-2 Calls", f"{p12_count:,}")
        
        with_coords = clean_df['lat'].notna().sum()
        col4.metric("With Coordinates", f"{with_coords:,}")

        # ─── UI: CHARTS ───
        st.subheader("Call Volume by Hour")
        # Streamlit makes bar charts this easy:
        hourly_counts = filtered_df['hour'].value_counts().sort_index()
        st.bar_chart(hourly_counts)

        st.subheader("Raw Cleaned Data")
        st.dataframe(filtered_df.head(50)) # Shows the first 50 rows in a nice interactive table
