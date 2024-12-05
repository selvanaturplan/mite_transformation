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
def transform_data(uploaded_file, file_type):
    # Datei lesen (CSV oder Excel)
    if file_type == "csv":
        data = pd.read_csv(uploaded_file, delimiter=';')
    elif file_type == "xlsx":
        data = pd.read_excel(uploaded_file)

    # Nur nicht abgeschlossene Einträge filtern
    data = data[data['Abgeschlossen'] == 'Nein']

    # Pivot-Tabelle erstellen, um Arbeitstarif und Fahrtarif in separaten Spalten zu haben
    pivoted_data = data.pivot_table(
        index=['Datum', 'Benutzer'],  # Gruppieren nach Datum und Benutzer
        columns='Leistung',  # Leistung (Arbeitstarif, Fahrtarif)
        values='Stunden',  # Stunden summieren
        aggfunc='sum',
        fill_value=0
    ).reset_index()

    # Fehlende Spalten (Arbeitstarif, Fahrtarif) sicherstellen
    for required_column in ['Arbeitstarif', 'Fahrtarif']:
        if required_column not in pivoted_data.columns:
            pivoted_data[required_column] = 0

    # Kombinierte Arbeitsbeschreibungen anhängen
    grouped_data = (
        data.groupby(['Datum', 'Benutzer'], as_index=False)
        .agg({'Bemerkung': lambda x: ', '.join(x.dropna())})  # Arbeitsbeschreibungen kombinieren
    )

    final_data = pd.merge(
        pivoted_data,
        grouped_data,
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
        # Dateityp ermitteln
        file_type = "csv" if uploaded_file.name.endswith(".csv") else "xlsx"

        # Transformation durchführen
        transformed_data = transform_data(uploaded_file, file_type)
        
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
