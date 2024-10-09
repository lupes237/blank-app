import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re

# Funktion zum Abrufen der Tarife
def get_tarif(tarif, options):
    tarifname = tarif.find(class_="logo__TariffName-sc-1jenrlw-3").get_text()
    anbietername = tarif.find(class_="badgeLabelsWithIcon__BadgeLabel-sc-18wjrn2-2").get('data-tooltip-id')
    anbietername = re.search(r'BadgeLabelWithIcon-([\w\s/]+)-', anbietername).group(1) if anbietername else 'Unbekannt'

    beitrag = tarif.find_all(class_="price__PriceAmount-sc-19hw2m6-1")
    beitrag = [b.get_text() for b in beitrag] if beitrag else ['Keine Angabe']

    rabatt_elem = tarif.find(class_="price__CrossedOutPercentage-sc-19hw2m6-5")
    rabatt = rabatt_elem.get_text().replace("-", "") if rabatt_elem else 'keine'

    return {
        'Anbietername': anbietername,
        'Tarifname': tarifname,
        'Beitrag': beitrag[0],
        'Rabatt': rabatt,
    }

def get_all_tarifs_by_url(options):
    response = requests.get(options['url'])
    soup = BeautifulSoup(response.content, 'html.parser')
    tarife = soup.select(".desktop__ProviderContainer-sc-1i3s93n-1")
    tarif_list = [get_tarif(tarif, options) for tarif in tarife]
    return tarif_list

def generate_url(region, g_person="Single", umweltrabatt="nein", plz="40210", alter="30"):
    return f"https://kfz-schutzbrief.check24.de/c24-sb-checkin/results?insuredScope={region}&product=SB&familyStatus={g_person}&postalCode={plz}&age={alter}"

# Streamlit App
st.title("KFZ Schutzbrief Tarife vergleichen")

# Input-Felder
region = st.selectbox("Wähle eine Region:", ["Germany", "Europe", "World"])
person = st.selectbox("Wähle eine Personengruppe:", ["Single", "Pair", "Family"])
plz = st.text_input("Postleitzahl:", "40210")
alter = st.slider("Alter:", 18, 31)

# Button zum Abrufen der Daten
if st.button("Tarife abrufen"):
    url = generate_url(region, g_person=person, umweltrabatt="nein", plz=plz, alter=alter)
    options = {
        'region': region,
        'person': person,
        'plz': plz,
        'url': url,
        'alter': alter
    }
    tarifs = get_all_tarifs_by_url(options)
    df_tarifs = pd.DataFrame(tarifs)

    # Beitrag in Euro umwandeln und sortieren
    df_tarifs['Beitrag'] = df_tarifs['Beitrag'].apply(lambda x: float(re.sub(r'[^\d.]', '', x.replace(',', '.'))))
    df_tarifs_sorted = df_tarifs.sort_values(by='Beitrag', ascending=True)

    # Duplikate entfernen
    df_tarifs_sorted = df_tarifs_sorted.drop_duplicates()

    # Tabelle anzeigen
    st.table(df_tarifs_sorted)

    # Horizontales Balkendiagramm
    import plotly.graph_objs as go
    bar_fig = go.Figure()

    # Daten für das Balkendiagramm in der Reihenfolge der Tabelle hinzufügen
    for i, row in df_tarifs_sorted.iterrows():
        bar_fig.add_trace(go.Bar(
            x=[row['Beitrag']],  # Beitrag in der richtigen Reihenfolge
            y=[row['Tarifname']],
            name=row['Anbietername'],
            text=row['Beitrag'],  # Beitrag als Text anzeigen
            textposition='outside',  # Text außerhalb des Balkens
            orientation='h',  # Horizontale Ausrichtung
            marker=dict(color='blue')  # Balkenfarbe
        ))

    bar_fig.update_layout(
        title='Balkendiagramm: Tarife vergleichen',
        xaxis_title='Beitrag in Euro',
        yaxis_title='Tarifname',
        width=800,
        height=600
    )

    # Balkendiagramm anzeigen
    st.plotly_chart(bar_fig)
