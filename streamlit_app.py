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

    # Nehme den ersten Beitrag und konvertiere ihn in einen Float
    beitrag = float(re.sub(r'[^\d.]', '', beitrag[0])) if beitrag and isinstance(beitrag, list) else 0

    # Weitere Tarifdetails
    v = tarif.find_all(class_="badgeLabelsWithIcon__Title-sc-18wjrn2-3")
    v_texts = [v_elem.get_text() for v_elem in v]
    
    rabatt_elem = tarif.find(class_="price__CrossedOutPercentage-sc-19hw2m6-5")
    rabatt = rabatt_elem.get_text().replace("-", "") if rabatt_elem else 'keine'

    pannenhilfe = next((s.replace("Pannenhilfe ", "") for s in v_texts if "Pannenhilfe" in s), 'Nein')
    ersatzwagen = next((s.replace("Ersatzwagen ", "") for s in v_texts if "Ersatzwagen" in s), 'Nein')
    abschleppen = 'Ja' if any("Abschleppen des Fahrzeugs" in s for s in v_texts) else 'Nein'
    krankenruecktransport = next((s for s in v_texts if "Krankenrücktransport" in s), 'Nein')

    current_date = datetime.now().strftime("%d-%m-%Y")

    return {
        'Anbietername': anbietername,
        'Abrufdatum': current_date,
        'Region': options['region'],
        'Person': options['person'],
        'Tarifname': tarifname,
        'Beitrag': beitrag,  # Beitrag wird jetzt als Float gespeichert
        'Rabatt': rabatt,
        'Pannenhilfe': pannenhilfe,
        'Ersatzwagen': ersatzwagen,
        'Abschleppen': abschleppen,
        'Krankenruecktransport': krankenruecktransport,
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
        # Entfernen von doppelten Zeilen
        df_tarifs = df_tarifs.drop_duplicates()

        # Tabelle nach Beitrag aufsteigend sortieren
        df_tarifs_sorted = df_tarifs.sort_values(by='Beitrag', ascending=True)

        # Beitrag formatieren (z.B. 8190 -> 81,90 €)
        df_tarifs_sorted['Beitrag'] = df_tarifs_sorted['Beitrag'].apply(lambda x: f"{x/100:.2f} €")

        # Tabelle anzeigen
        st.write("Tariftabelle (aufsteigend nach Beitrag sortiert):")
        st.dataframe(df_tarifs_sorted)

        # Balkendiagramm erstellen
        bar_fig = go.Figure()

        # Daten für das Balkendiagramm in der Reihenfolge der sortierten Tabelle hinzufügen
        for i, row in df_tarifs_sorted.iterrows():
            bar_fig.add_trace(go.Bar(
                x=[row['Tarifname']],
                y=[row['Beitrag']],
                name=row['Anbietername'],
                text=row['Beitrag'],  # Betrag als Text anzeigen
                textposition='outside',  # Text außerhalb des Balkens
                marker=dict(color='blue')  # Alle Balken in Blau
            ))

        bar_fig.update_layout(
            title='Balkendiagramm: Tarife vergleichen',
            xaxis_title='Tarifname',
            yaxis_title='Beitrag in Euro',
            xaxis_tickangle=-45,
            width=800,  # Breite des Diagramms
            height=600  # Höhe des Diagramms
        )

        # Anzeigen des Balkendiagramms
        st.plotly_chart(bar_fig)

# Horizontales Balkendiagramm
bar_fig = go.Figure()

# Daten für das Balkendiagramm in der Reihenfolge der sortierten Tabelle hinzufügen
for i, row in df_tarifs_sorted.iterrows():
    bar_fig.add_trace(go.Bar(
        x=[float(row['Beitrag'].replace(' €', '').replace(',', '.'))],  # Beitrag in der richtigen Reihenfolge
        y=[row['Tarifname']],
        name=row['Anbietername'],
        text=row['Beitrag'],  # Beitrag als Text anzeigen
        textposition='outside',  # Text außerhalb des Balkens
        orientation='h',  # Horizontale Ausrichtung
        marker=dict(color='blue')  # Alle Balken in Blau
    ))

bar_fig.update_layout(
    title='Horizontales Balkendiagramm: Tarife vergleichen',
    xaxis_title='Beitrag in Euro',
    yaxis_title='Tarifname',
    width=800,  # Breite des Diagramms
    height=600  # Höhe des Diagramms
)

# Diagramm anzeigen
st.plotly_chart(bar_fig)

else:
        st.write("Keine Tarife gefunden.")
