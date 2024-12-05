import pandas as pd
import streamlit as st
from io import BytesIO

# Mapping für Benutzernamen-Kürzel
user_mapping = {
    "Markus Camastral": "mc",
    "Simone Frei": "sf",
    "Nina Leidenberger": "nl",
    "Yasmina Bounaja": "yb",
    "Urs Steinegger": "us",
    "Simonetta Selva": "ss"
}

# Funktion für die Transformation
def transform_data(uploaded_file):
    # Datei lesen
    data = pd.read_csv(uploaded_file, delimiter=';')
    
    # Nur nicht abgeschlossene Einträge filtern
    data = data[data['Abgeschlossen'] == 'Nein']
    
    # Kombinieren der Arbeitsbeschreibungen
    data['Bemerkung'] = data['Bemerkung'].fillna('')  # Fehlende Beschreibungen mit leerem String auffüllen
    grouped_data = (
        data.groupby(['Datum', 'Benutzer'], as_index=False)
        .agg({
            'Bemerkung': lambda x: ', '.join(x),  # Kombinieren der Arbeitsbeschreibungen
            'Stunden': 'sum',  # Summieren der Stunden
            'Leistung': lambda x: ', '.join(x.unique())  # Leistung kombiniert
        })
    )
    
    # Pivot-Tabelle erstellen, um Arbeitstarif und Fahrtarif zu trennen
    pivoted_data = data.pivot_table(
        index=['Datum', 'Benutzer'],
        columns='Leistung',
        values='Stunden',
        aggfunc='sum',
        fill_value=0
    ).reset_index()

    # Fehlende Spalten (Arbeitstarif, Fahrtarif) sicherstellen
    for required_column in ['Arbeitstarif', 'Fahrtarif']:
        if required_column not in pivoted_data.columns:
            pivoted_data[required_column] = 0

    # Kombinierte Arbeitsbeschreibungen anhängen
    final_data = pd.merge(
        pivoted_data,
        grouped_data[['Datum', 'Benutzer', 'Bemerkung']],
        on=['Datum', 'Benutzer'],
        how='left'
    )

    # Spalten umbenennen
    final_data.rename(
        columns={'Benutzer': 'Bearb.', 'Bemerkung': 'Arbeitsbeschrieb'}, inplace=True
    )

    # Benutzerkürzel anwenden
    final_data['Bearb.'] = final_data['Bearb.'].replace(user_mapping)

    # Spaltenreihenfolge anpassen
    final_data = final_data[['Bearb.', 'Datum', 'Arbeitsbeschrieb', 'Arbeitstarif', 'Fahrtarif']]
    return final_data

# Streamlit App
st.title("Excel-Transformation")
st.write("Lade eine Excel- oder CSV-Datei hoch, um sie zu transformieren.")

# Datei hochladen
uploaded_file = st.file_uploader("Wähle eine Datei aus", type=["csv", "xlsx"])

if uploaded_file:
    try:
        # Transformation durchführen
        transformed_data = transform_data(uploaded_file)
        
        # Zeige eine Vorschau
        st.write("Transformation abgeschlossen. Vorschau der Ergebnisse:")
        st.dataframe(transformed_data)
        
        # Ermögliche den Download der transformierten Datei
        output = BytesIO()
        transformed_data.to_csv(output, index=False, sep=';', encoding='utf-8-sig')
        st.download_button(
            label="Download der transformierten Datei",
            data=output.getvalue(),
            file_name="Transformed_Data.csv",
            mime="text/csv"
        )
    except Exception as e:
        st.error(f"Ein Fehler ist aufgetreten: {e}")
