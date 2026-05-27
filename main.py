import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Mon Comic Den", page_icon="📚", layout="wide")
st.title("📚 Mon Gestionnaire de Comics")
st.write("Range, trie, estime et note ta collection en quelques clics.")

# --- CONNEXION BASE DE DONNÉES ---
conn = sqlite3.connect("comics_collection.db", check_same_thread=False)
cursor = conn.cursor()

# Création ou modification de la table pour inclure toutes les colonnes nécessaires
cursor.execute('''
    CREATE TABLE IF NOT EXISTS comics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titre TEXT,
        editeur TEXT,
        tome INTEGER,
        annee_publication INTEGER,
        scenariste TEXT,
        statut TEXT,
        prix REAL,
        note INTEGER
    )
''')

# Mises à jour de sécurité de la base de données (si le fichier existait déjà)
colonnes_a_verifier = [
    ("annee_publication", "INTEGER"),
    ("prix", "REAL"),
    ("note", "INTEGER")
]

for col_name, col_type in colonnes_a_verifier:
    try:
        cursor.execute(f"ALTER TABLE comics ADD COLUMN {col_name} {col_type}")
    except sqlite3.OperationalError:
        # La colonne existe déjà, on continue
        pass
conn.commit()

# --- SÉPARATEUR VISUEL ---
st.sidebar.header("➕ Ajouter un Comic")

# --- FORMULAIRE D'AJOUT (Dans la barre latérale) ---
annee_actuelle = datetime.now().year

with st.sidebar.form(key="comic_form", clear_on_submit=True):
    titre = st.text_input("Titre de la série / du comic *")
    editeur = st.selectbox("Éditeur", ["Marvel", "DC Comics", "Image Comics", "Urban Comics", "Panini Comics", "Autre"])
    tome = st.number_input("Numéro / Tome", min_value=1, value=1, step=1)
    annee_publication = st.number_input("Année de publication", min_value=1900, max_value=annee_actuelle + 2, value=annee_actuelle, step=1)
    scenariste = st.text_input("Scénariste / Dessinateur")
    
    # Nouveaux champs : Prix et Note
    prix = st.number_input("Prix d'achat (€)", min_value=0.0, value=0.0, step=0.05, format="%.2f")
    note = st.slider("Ta Note (Étoiles)", min_value=1, max_value=5, value=3, step=1)
    
    statut = st.radio("Statut de lecture", ["À lire 🔴", "En cours 🟡", "Lu 🟢"])
    
    submit_button = st.form_submit_button(label="Ajouter à la collection")

# Action à l'ajout
if submit_button:
    if titre:
        cursor.execute(
            """INSERT INTO comics (titre, editeur, tome, annee_publication, scenariste, prix, note, statut) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (titre, editeur, tome, annee_publication, scenariste, prix, note, statut)
        )
        conn.commit()
        st.sidebar.success(f"🎉 '{titre} #{tome}' a été ajouté !")
    else:
        st.sidebar.error("Le titre est obligatoire !")

# --- AFFICHAGE DE LA COLLECTION ---
st.subheader("📋 Ma Collection")

# Récupération de toutes les données
df = pd.read_sql_query("""
    SELECT id, titre as 'Titre', editeur as 'Éditeur', tome as 'N° Tome', 
    annee_publication as 'Année', scenariste as 'Auteur(s)', 
    prix as 'Prix (€)', note as 'Note /5', statut as 'Statut' 
    FROM comics
""", conn)

if not df.empty:
    # --- STATISTIQUES RAPIDES ---
    total_comics = len(df)
    valeur_totale = df['Prix (€)'].sum()
    
    # Transformation visuelle de la note chiffrée en petites étoiles ⭐ pour le tableau
    df['Note /5'] = df['Note /5'].apply(lambda x: "⭐" * int(x) if pd.notnull(x) else "")

    col_stat1, col_stat2 = st.columns(2)
    with col_stat1:
        st.metric(label="Nombre de comics", value=f"{total_comics} ex.")
    with col_stat2:
        st.metric(label="Valeur totale estimée", value=f"{valeur_totale:.2f} €")
    
    st.write("---")

    # Filtres rapides
    col1, col2 = st.columns(2)
    with col1:
        filtre_editeur = st.multiselect("Filtrer par Éditeur", options=df["Éditeur"].unique())
    with col2:
        filtre_statut = st.multiselect("Filtrer par Statut", options=df["Statut"].unique())
    
    # Application des filtres
    df_filtré = df.copy()
    if filtre_editeur:
        df_filtré = df_filtré[df_filtré["Éditeur"].isin(filtre_editeur)]
    if filtre_statut:
        df_filtré = df_filtré[df_filtré["Statut"].isin(filtre_statut)]
        
    # Affichage du tableau trié
    df_filtré = df_filtré.sort_values(by=["Titre", "N° Tome"])
    st.dataframe(df_filtré.drop(columns=["id"]), use_container_width=True)
    
    # Option pour supprimer un comic
    st.write("---")
    st.subheader("🗑️ Supprimer un élément")
    df['Label_Suppression'] = df["Titre"] + " #" + df["N° Tome"].astype(str) + " (" + df["Année"].astype(str) + ")"
    comic_a_supprimer = st.selectbox("Choisir un comic à retirer", df['Label_Suppression'])
    
    if st.button("Supprimer définitivement"):
        index_choisi = df.index[df['Label_Suppression'] == comic_a_supprimer].tolist()[0]
        id_database = int(df.iloc[index_choisi]["id"])
        
        cursor.execute("DELETE FROM comics WHERE id = ?", (id_database,))
        conn.commit()
        st.rerun()
else:
    st.info("Ta bibliothèque est vide pour le moment. Utilise le menu à gauche pour ajouter ton premier comic !")
