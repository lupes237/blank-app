import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
from datetime import datetime, timedelta

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
    current_date = datetime.now().strftime("%d-%m-%Y")

    return {
        'Anbietername': anbietername,
        'Abrufdatum': current_date,
        'Region': options['region'],
        'Person': options['person'],
        'Tarifname': tarifname,
        'Beitrag': beitrag,  # Beitrag wird jetzt als Float gespeichert
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

        # Tabelle anzeigen
        st.write("Tariftabelle (aufsteigend nach Beitrag sortiert):")
        st.dataframe(df_tarifs_sorted)
    else:
        st.write("Keine Tarife gefunden.")
