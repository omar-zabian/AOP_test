
import streamlit as st
import pandas as pd
import os
import uuid
from datetime import datetime

def load_data():
    enriched_path = os.path.join('out', 'artworks_enriched.csv')
    summary_path = os.path.join('out', 'summary_by_artist.csv')
    financial_path = os.path.join('artwork_financial.csv')
    df_enriched = pd.read_csv(enriched_path)
    df_summary = pd.read_csv(summary_path)
    df_financial = pd.read_csv(financial_path)
    return df_enriched, df_summary, df_financial

def add_financial_event(artwork_id, event_type, event_date, currency, price_amount, buyer_name, seller_name, sale_location, source, notes):
    new_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    new_row = {
        'id': new_id,
        'artwork_id': artwork_id,
        'event_type': event_type,
        'event_date': event_date,
        'currency': currency,
        'price_amount': price_amount,
        'price_estimate_min': '',
        'price_estimate_max': '',
        'buyer_name': buyer_name,
        'seller_name': seller_name,
        'sale_location': sale_location,
        'source': source,
        'notes': notes,
        'created_at': now,
        'updated_at': now
    }
    df = pd.read_csv('artwork_financial.csv')
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv('artwork_financial.csv', index=False)
    return new_row

def sidebar_filters(df):
    st.sidebar.header("Filters")
    artists = df['name'].unique()
    mediums = df['medium'].dropna().unique()
    years = df['creation_year_start'].dropna().astype(int)
    min_year, max_year = years.min(), years.max()
    selected_artists = st.sidebar.multiselect("Artist", artists, default=list(artists))
    selected_mediums = st.sidebar.multiselect("Medium", mediums, default=list(mediums))
    year_range = st.sidebar.slider("Creation Year Range", min_year, max_year, (min_year, max_year))
    search_text = st.sidebar.text_input("Search Title")
    return selected_artists, selected_mediums, year_range, search_text

def filter_data(df, selected_artists, selected_mediums, year_range, search_text):
    filtered = df[df['name'].isin(selected_artists)]
    filtered = filtered[filtered['medium'].isin(selected_mediums)]
    filtered = filtered[(filtered['creation_year_start'].astype(float) >= year_range[0]) & (filtered['creation_year_start'].astype(float) <= year_range[1])]
    if search_text:
        filtered = filtered[filtered['title'].str.contains(search_text, case=False, na=False)]
    return filtered

def kpi_cards(df, df_financial):
    artworks_count = len(df)
    artists_count = df['artist_id'].nunique()
    artworks_with_images = df['storage_key'].notna().sum() if 'storage_key' in df.columns else 0
    # Last valuation per artwork
    last_valuations = df_financial.sort_values('event_date').groupby('artwork_id')['price_amount'].last().astype(float)
    sum_last_valuations = last_valuations.sum()
    st.markdown(f"### KPIs")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Artworks", artworks_count)
    col2.metric("Artists", artists_count)
    col3.metric("Artworks w/ Images", artworks_with_images)
    col4.metric("Sum Last Valuations", f"${sum_last_valuations:,.0f}")

def gallery_cards(df, df_financial):
    st.markdown("### Gallery")
    for idx, row in df.iterrows():
        st.markdown("---")
        cols = st.columns([1,2])
        with cols[0]:
            if 'storage_key' in row and pd.notna(row['storage_key']):
                st.image(row['storage_key'], width=200)
        with cols[1]:
            st.subheader(row['title'])
            st.write(f"**Artist:** {row['name']}")
            st.write(f"**Year:** {row['creation_year_start']}")
            st.write(f"**Medium:** {row['medium']}")
            st.write(f"**Location:** {row['location_text']}")
            st.write(f"**Rights:** {row['rights']}")
            st.write(f"**Attributes:** {row['attributes_json']}")
            # Last financial event
            fin = df_financial[df_financial['artwork_id'] == row['artwork_id']]
            if not fin.empty:
                last_event = fin.sort_values('event_date').iloc[-1]
                st.write(f"**Last Event:** {last_event['event_type']} on {last_event['event_date']}")
                st.write(f"**Last Price:** {last_event['price_amount']} {last_event['currency']}")
            # Expandable table for financial history
            with st.expander("Financial History"):
                st.dataframe(fin)

def financial_event_form(df):
    st.sidebar.header("Add Financial Event")
    artwork_ids = df['artwork_id'].unique()
    selected_artwork = st.sidebar.selectbox("Artwork", artwork_ids)
    event_type = st.sidebar.text_input("Event Type")
    event_date = st.sidebar.date_input("Event Date", value=datetime.utcnow()).isoformat()
    currency = st.sidebar.text_input("Currency", value="USD")
    price_amount = st.sidebar.number_input("Price Amount", min_value=0.0, value=0.0)
    buyer_name = st.sidebar.text_input("Buyer Name")
    seller_name = st.sidebar.text_input("Seller Name")
    sale_location = st.sidebar.text_input("Sale Location")
    source = st.sidebar.text_input("Source")
    notes = st.sidebar.text_area("Notes")
    if st.sidebar.button("Add Event"):
        new_row = add_financial_event(selected_artwork, event_type, event_date, currency, price_amount, buyer_name, seller_name, sale_location, source, notes)
        st.sidebar.success(f"Added event for artwork {selected_artwork}")

def main():
    st.set_page_config(page_title="Art Data Explorer", layout="wide")
    df_enriched, df_summary, df_financial = load_data()
    tabs = st.tabs(["Dashboard", "Gallery", "Summary Table"])
    # Sidebar filters
    selected_artists, selected_mediums, year_range, search_text = sidebar_filters(df_enriched)
    financial_event_form(df_enriched)
    # Filtered data
    filtered = filter_data(df_enriched, selected_artists, selected_mediums, year_range, search_text)
    with tabs[0]:
        kpi_cards(filtered, df_financial)
    with tabs[1]:
        gallery_cards(filtered, df_financial)
    with tabs[2]:
        st.header("Summary Table")
        st.dataframe(df_summary)

if __name__ == "__main__":
    main()
