import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

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

    rest
