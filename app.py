import streamlit as st
import geopandas as gpd
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium.features import GeoJsonTooltip
import plotly.express as px

# Load GeoDataFrame
@st.cache_data
def load_geodata():
    gdf = gpd.read_file("./data/btw21_geometrie_wahlkreise_geo_shp/Geometrie_Wahlkreise_20DBT_geo.shp")  # Change to your file
    return gdf

# Load spreadsheet data
@st.cache_data
def load_spreadsheet():
    file_path = './data/kerg2025_filtered.csv'
    # Read the CSV file, using the first three rows as header
    df = pd.read_csv(file_path, sep=';', header=[0, 1, 2])

    # Create a new single level column index by concatenating the multi-level columns with "_"
    df.columns = ['_'.join(col).strip() for col in df.columns]
    df.rename(columns={'WKR_NR_Unnamed: 0_level_1_Unnamed: 0_level_2': 'WKR_NR'},
              inplace=True)  # Set 'Nr' column as the index
    df['WKR_NR'] = df['WKR_NR'].fillna(0).astype(int)
    df = df.drop_duplicates(['WKR_NR'], keep='first')
    return df


@st.cache_data
def load_voting_data() -> (pd.DataFrame, list):
    file_path = './data/kerg2025.csv'
    # Read the CSV file, using the first three rows as header
    df = pd.read_csv(file_path, sep=';')
    # Get unique values from the "Category" column
    wahlkreise = list(df['Gebietsname'].unique())

    return df, wahlkreise


# Merge the data
def merge_data(gdf, df):
    merged_gdf = gdf.merge(df, on="WKR_NR", how="left")  # Merge on the common column
    return merged_gdf


def generate_best_performer(row, columns):
    # Define the color mapping based on the party
    color_mapping = {
        "CDU": "#000000",  # Black for CDU
        "SPD": "#FF0000",  # Red for SPD
        "AFD": "#0000FF",  # Blue for AFD
        "FDP": "#FFFF00",  # Yellow for FDP
        "CSU": "#808080",  # Grey for CSU
        "DIELINKE": "#800080",  # Purple for DIELINKE
        "B90/GRÜNE": "#008000",  # Green for B90/GRÜNE
    }
    row_filled = row[columns].fillna(-1).infer_objects(copy=False)
    max_col = row_filled.idxmax()  # Get the column with the highest value
    # If max_col is -1 (indicating all values were NaN), handle accordingly
    if row_filled[max_col] == -1:
        return "#FFFFFF"  # Return a default color (e.g., white) if all values are NaN

    # Extract the party name from the column name (e.g., "CDU_Zweitstimmen_Endgültig" -> "CDU")
    party = max_col.split('_')[0]
    # Return the associated color for the party
    return color_mapping.get(party, "#FFFFFF")


tab1, tab2, tab3 = st.tabs(["Deutschlandkarte", "Grafiken", "noch "])

with tab1:
    # Load data
    gdf = load_geodata()
    df = load_spreadsheet()
    merged_gdf = merge_data(gdf, df)

    # Streamlit UI
    st.title("Interactive Map with Hover Info & Additional Data")

    # Add a sidebar header
    st.sidebar.header('Wahlkreisauswahl')

    # Dropdown 1: Choose a party
    votes = ['Erststimmen', 'Zweitstimmen']
    vote = st.sidebar.selectbox('Erst oder Zweitstimme', votes)

    # Dropdown 2: Choose a metric (e.g., Zweitstimmen or Erststimmen)
    years = ['Vorläufig', 'Vorperiode']
    year = st.sidebar.selectbox('Wahldatum', years)

    # Create Folium map
    m = folium.Map(location=[51, 10], zoom_start=6)  # Adjust location & zoom

    # Add GeoJSON layer with hover tooltips, including new spreadsheet data

    # List of parties
    parties = ['CDU', 'SPD', 'AFD', 'FDP', 'CSU', 'DIELINKE', 'B90/GRÜNE']
    # The string to prepend - for now only zweitstimme
    # string = '_Zweitstimmen_Endgültig'
    # Create the list with each party prepended to the string
    select_cols = [party + '_' + vote + '_' + year for party in parties]
    keep_cols = ['WKR_NR', 'WKR_NAME', 'LAND_NR', 'LAND_NAME', 'geometry'] + select_cols
    merged_gdf = merged_gdf[keep_cols]

    tooltip_fields = ["WKR_NAME"] + select_cols  # + list(df.columns.drop("WKR_NR"))  # Exclude join key

    merged_gdf['Best_Performer_Color'] = merged_gdf.apply(lambda row: generate_best_performer(row, select_cols), axis=1)

    geojson = folium.GeoJson(
        merged_gdf,
        style_function=lambda feature: {
            'fillColor': feature['properties']['Best_Performer_Color'],  # Fill color from the 'random_color' column
            'color': 'transparent',  # Border color (set to transparent since we are filling the area)
            'weight': 1,  # Thickness of the border (optional, since it's transparent)
            'opacity': 1,  # Opacity of the fill color
            'fillOpacity': 0.7  # Opacity of the fill color
        },
        tooltip=GeoJsonTooltip(fields=tooltip_fields, aliases=tooltip_fields, sticky=True)
    )

    geojson.add_to(m)

    # Display map in Streamlit
    st_folium(m, width=700, height=500)


with tab2:
    # Load data
    vote_df, wahlkreise = load_voting_data()
    vote_df["Prozent"] = vote_df["Prozent"].str.replace(",", ".").astype(float)

    # Dictionary mapping parties to their hex color codes
    party_colors = {
        "CDU": "#000000",  # Black
        "SPD": "#E3000F",  # Red
        "AfD": "#009EE0",  # Blue
        "FDP": "#FFED00",  # Yellow
        "DIE LINKE": "#BE3075",  # Magenta
        "GRÜNE": "#64A12D",  # Green
        "CSU": "#008AC5",  # Light blue
        "FREIE WÄHLER": "#FF6600",
        "Die PARTEI": "#BB1E10",
        "Tierschutzpartei": "#00A650",
        "HEIMAT (2021: NPD)": "#A51D21",
        "PIRATEN": "#EE8208",
        "ÖDP": "#E65F00",
        "V-Partei³": "#009473",
        "DiB": "#D31566",
        "BP": "#FFD700",
        "Tierschutzallianz": "#B7005D",
        "MLPD": "#E2001A",
        "Verjüngungsforschung (2021: Gesundheitsforschung)": "#008000",
        "MENSCHLICHE WELT": "#7A0026",
        "DKP": "#D7141A",
        "Die Grauen": "#808080",
        "BüSo": "#1E90FF",
        "Die Humanisten": "#ED1C24",
        "Gartenpartei": "#006400",
        "du.": "#005BAC",
        "SGP": "#8B0000",
        "dieBasis": "#00A499",
        "Bündnis C": "#1B5E20",
        "BÜRGERBEWEGUNG": "#9C27B0",
        "III. Weg": "#004B49",
        "BÜNDNIS21": "#F57C00",
        "LIEBE": "#FF69B4",
        "Wir Bürger (2021: LKR)": "#002147",
        "PdF": "#008080",
        "LfK": "#4B0082",
        "SSW": "#002F6C",
        "Team Todenhöfer": "#B22222",
        "UNABHÄNGIGE": "#3F51B5",
        "Volt": "#572A8F",
        "Volksabstimmung": "#DAA520",
        "B*": "#DC143C",
        "sonstige": "#C0C0C0",  # Gray for others
        "FAMILIE": "#FF4500",
        "Graue Panther": "#708090",
        "KlimalisteBW": "#2E8B57",
        "THP": "#D2691E"
    }

    # Assign hex color to each party in the dataframe
    vote_df["hex_num"] = vote_df["Gruppenname"].map(party_colors)


    default_value = "Aalen - Heidenheim"
    default_index = list(wahlkreise).index(default_value) if default_value in wahlkreise else 0

    # Streamlit UI
    st.title("Interactive Map with Hover Info & Additional Data")

    # Add a sidebar header
    st.sidebar.header('Wahlkreisfilter')

    # Create a dropdown list in Streamlit
    selected_area = st.sidebar.selectbox("Select a Category", wahlkreise)

    # filter down for selected wahlkreis
    filtered_df = vote_df[vote_df['Gebietsname'] == selected_area].copy()
    # filter down for parties
    filtered_df = filtered_df[filtered_df['Gruppenart'] == 'Partei'].copy()
    if vote == 'Erststimmen':
        stimme = 1
    elif vote == 'Zweitstimmen':
        stimme = 2
    filtered_df = filtered_df[filtered_df['Stimme'] == stimme].copy()

    # Create Bar Chart
    fig = px.bar(
        filtered_df,
        x="Gruppenname",
        y="Prozent",
        text_auto=True,  # Show exact percentage values on bars
        hover_data=["Anzahl"],  # Tooltip showing "Anzahl"
        title=f"Ergebnis in {selected_area}",
        labels={"Gruppenname": "Partei", "Prozent": "Percentage"},
        color="hex_num",
        color_discrete_map="identity"
    )

    # Adjust layout for better visibility
    fig.update_layout(yaxis=dict(tickformat=".0f"))  # Remove decimal places from y-axis
    # Show in Streamlit
    st.plotly_chart(fig)

