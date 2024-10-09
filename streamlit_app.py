import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
from datetime import datetime, timedelta
import plotly.graph_objs as go

# Funktion zum Extrahieren von Tarifinformationen
def get_tarif(tarif, options):
    tarifname = tarif.find(class_="logo__TariffName-sc-1jenrlw-3").get_text()

    anbietername = tarif.find(class_="badgeLabelsWithIcon__BadgeLabel-sc-18wjrn2-2").get('data-tooltip-id')
    anbietername = re.search(r'BadgeLabelWithIcon-([\w\s/]+)-', anbietername).group(1) if anbietername else 'Unbekannt'

    beitrag = tarif.find_all(class_="price__PriceAmount-sc-19hw2m6-1")
    beitrag = [b.get_text() for b in beitrag] if beitrag else ['Keine Angabe']

    v = tarif.find_all(class_="badgeLabelsWithIcon__Title-sc-18wjrn2-3")
    v_texts = [v_elem.get_text() for v_elem in v]

    pannenhilfe = next((s.replace("Pannenhilfe ", "") for s in v_texts if "Pannenhilfe" in s), 'Nein')
    ersatzwagen = next((s.replace("Ersatzwagen ", "") for s in v_texts if "Ersatzwagen" in s), 'Nein')
    abschleppen = 'Ja' if any("Abschleppen des Fahrzeugs" in s for s in v_texts) else 'Nein'
    krankenruecktransport = next((s for s in v_texts if "Krankenrücktransport" in s), 'Nein')

    rabatt_elem = tarif.find(class_="price__CrossedOutPercentage-sc-19hw2m6-5")
    rabatt = rabatt_elem.get_text().replace("-", "") if rabatt_elem else 'keine'

    zahlungsfrequenz = tarif.find_all(class_="price__Period-sc-19hw2m6-2")
    zahlungsfrequenz = [z.get_text() for z in zahlungsfrequenz] if zahlungsfrequenz else ['Keine Angabe']

    rest = tarif.find_all(class_="badgeLabels__BadgeLabelWrapper-sc-uavc85-1")
    rest_texts = ";".join([r.get_text() for r in rest]) if rest else 'keine'

    current_date = datetime.now().strftime("%d-%m-%Y")

    return {
        'Anbietername': anbietername,
        'Abrufdatum': current_date,
        'Region': options['region'],
        'Person': options['person'],
        'Tarifname': tarifname,
        'Beitrag': beitrag,
        'Zahlungsfrequenz': zahlungsfrequenz,
        'UmweltRabatt': options['umweltrabatt'],
        'Alter': int(options['alter']),
        'Reduzierung': rabatt,
        'Pannenhilfe': pannenhilfe,
        'Ersatzwagen': ersatzwagen,
        'Abschleppen': abschleppen,
        'Krankenruecktransport': krankenruecktransport,
        'AndereInformationen': rest_texts,
        'PLZ': options['plz'],
        'AbrufUrl': options['url']
    }

def get_all_tarifs_by_url(options):
    response = requests.get(options['url'])
    soup = BeautifulSoup(response.content, 'html.parser')
    tarife = soup.select(".desktop__ProviderContainer-sc-1i3s93n-1")
    tarif_list = [get_tarif(tarif, options) for tarif in tarife]
    return tarif_list

def generate_url(region, g_person="Single", fa="nein", beruf="Employee", umwelt_rabatt="nein", plz="40210", alter="30"):
    current_date = (datetime.now() + timedelta(days=1)).strftime("%d-%m-%Y")
    return f"https://kfz-schutzbrief.check24.de/c24-sb-checkin/results?insuredScope={region}&product=SB&insuranceStartDate={current_date}&driverLicenceLessThanOneYear={'true' if fa == 'ja' else 'false'}&employmentStatus={beruf}&environmentalDiscount={'true' if umwelt_rabatt == 'ja' else 'false'}&familyStatus={g_person}&postalCode={plz}&severelyDisabled=false&age={alter}"

# Streamlit App
st.title("KFZ Schutzbrief Tarife vergleichen")

# Input-Felder für die Benutzereingabe
region = st.selectbox("Wähle eine Region:", ["Germany", "Europe", "World"])
person = st.selectbox("Wähle eine Personengruppe:", ["Single", "Pair", "Family"])
plz = st.text_input("Postleitzahl:", "40210")
umweltrabatt = st.selectbox("Umweltrabatt:", ["ja", "nein"])
alter = st.slider("Alter:", 18, 31)

# Button zum Abrufen der Daten
if st.button("Tarife abrufen"):
    url = generate_url(region, g_person=person, umwelt_rabatt=umweltrabatt, plz=plz, alter=alter)
    options = {
        'region': region,
        'person': person,
        'plz': plz,
        'url': url,
        'umweltrabatt': umweltrabatt,
        'alter': alter
    }
    tarifs = get_all_tarifs_by_url(options)
    df_tarifs = pd.DataFrame(tarifs)

    # Ergebnisse anzeigen
    st.write(f"Anzahl der gefundenen Tarife: {len(df_tarifs)}")

    if not df_tarifs.empty:
        # Beitrag in Euro umwandeln
        df_tarifs['Beitrag'] = df_tarifs['Beitrag'].apply(lambda x: float(re.sub(r'[^\d.]', '', x[0])) if isinstance(x, list) and x else 0)

        # Filtern der doppelten Anbieterwerte nur für ACV Komfort und ACE Comfort+
        df_acv_komfort = df_tarifs[df_tarifs['Anbietername'] == 'ACV Komfort']
        df_ace_comfort_plus = df_tarifs[df_tarifs['Anbietername'] == 'ACE Comfort+']
        
        # Alle anderen Anbieter beibehalten
        df_rest = df_tarifs[~df_tarifs['Anbietername'].isin(['ACV Komfort', 'ACE Comfort+'])]

        # Doppelte herausfiltern, wobei der Tarif mit dem niedrigsten Beitrag genommen wird
        df_acv_komfort = df_acv_komfort.sort_values(by='Beitrag').drop_duplicates(subset='Tarifname', keep='first')
        df_ace_comfort_plus = df_ace_comfort_plus.sort_values(by='Beitrag').drop_duplicates(subset='Tarifname', keep='first')

        # Kombinieren der DataFrames
        df_tarifs_filtered = pd.concat([df_rest, df_acv_komfort, df_ace_comfort_plus])

        # Sortiere nach Beitrag (Höhe)
        df_tarifs_filtered = df_tarifs_filtered.sort_values(by='Beitrag', ascending=True)

        # Farben für die Anbieter definieren
        unique_anbieter = df_tarifs_filtered['Anbietername'].unique()
        colors = ['blue', 'green', 'orange', 'red', 'purple', 'cyan', 'magenta', 'yellow', 'brown', 'pink']
        color_mapping = {anbieter: colors[i % len(colors)] for i, anbieter in enumerate(unique_anbieter)}
        
        # Balkendiagramm erstellen
        bar_fig = go.Figure()
        for i, row in df_tarifs_filtered.iterrows():
            bar_fig.add_trace(go.Bar(
                x=[row['Tarifname']],
                y=[row['Beitrag']],
                name=row['Anbietername'],
                marker_color=color_mapping[row['Anbietername']],  # Eindeutige Farbe pro Anbieter
                width=0.6  # Dicke der Balken
            ))
        bar_fig.update_layout(title='Balkendiagramm: Tarife vergleichen',
                              xaxis_title='Tarifname',
                              yaxis_title='Beitrag in Euro',
                              xaxis_tickangle=-45,
                              width=1200,  # Breite des Diagramms erhöhen
                              height=600)  # Höhe des Diagramms erhöhen
        bar_fig.update_traces(texttemplate='%{y:.2f} €', textposition='outside')  # Betrag an der Spitze der Balken anzeigen

        st.plotly_chart(bar_fig)

        # Liniendiagramm erstellen
        line_fig = go.Figure()
        for i, row in df_tarifs_filtered.iterrows():
            line_fig.add_trace(go.Scatter(
                x=[row['Tarifname']],
                y=[row['Beitrag']],
                mode='lines+markers',
                name=row['Anbietername'],
                line=dict(shape='linear', color=color_mapping[row['Anbietername']]),  #
