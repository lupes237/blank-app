import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import plotly.express as px

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
    url = generate_url(region, g_person=person, umwelt_rabatt=umwelrabatt, plz=plz, alter=alter)
    options = {
        'region': region,
        'person': person,
        'plz': plz,
        'url': url,
        'umweltrabatt': umwelrabatt,
        'alter': alter
    }
    tarifs = get_all_tarifs_by_url(options)
    df_tarifs = pd.DataFrame(tarifs)

    # Ergebnisse anzeigen
    st.write(f"Anzahl der gefundenen Tarife: {len(df_tarifs)}")
    st.dataframe(df_tarifs)

    # Diagramm erstellen
    if not df_tarifs.empty:
        # Beitragsdaten bereinigen
        df_tarifs['Beitrag'] = df_tarifs['Beitrag'].apply(lambda x: float(re.sub(r'[^\d.]', '', x[0])) if isinstance(x, list) and x else 0)

        # Balkendiagramm erstellen
        st.subheader("Balkendiagramm der Tarife")
        fig = px.bar(df_tarifs, x='Tarifname', y='Beitrag', color='Anbietername', title='Beitrag nach Tarifname', labels={'Beitrag': 'Beitrag in Euro', 'Tarifname': 'Tarifname'})
        st.plotly_chart(fig)

        # Boxplot erstellen
        st.subheader("Boxplot der Beiträge")
        fig2 = px.box(df_tarifs, y='Beitrag', title='Boxplot der Beiträge', labels={'Beitrag': 'Beitrag in Euro'})
        st.plotly_chart(fig2)

        # Scatterplot erstellen
        st.subheader("Scatterplot der Beiträge")
        fig3 = px.scatter(df_tarifs, x='Alter', y='Beitrag', color='Anbietername', title='Beitrag nach Alter', labels={'Beitrag': 'Beitrag in Euro', 'Alter': 'Alter'})
        st.plotly_chart(fig3)

    # Option zum CSV-Download
    csv = df_tarifs.to_csv(index=False, sep=";")
    st.download_button(label="CSV herunterladen", data=csv, file_name="KFZ-Schutzbrief-Tarife.csv", mime="text/csv")
