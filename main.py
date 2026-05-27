import streamlit as st
import sqlite3
import pandas as pd
import requests
from datetime import datetime

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Mon Comic Den PRO", page_icon="📚", layout="wide")
st.title("📚 Mon Gestionnaire de Comics - Version Catalogue")

# --- CONNEXION BASE DE DONNÉES ---
conn = sqlite3.connect("comics_collection.db", check_same_thread=False)
cursor = conn.cursor()

# Création de la table si elle n'existe pas
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
conn.commit()

# --- FONCTION DE RECHERCHE DANS LE CATALOGUE MONDIAL ---
def chercher_dans_catalogue(recherche):
    url = f"https://openlibrary.org/search.json?q={recherche}&type=work"
    try:
        reponse = requests.get(url).json()
        resultats = []
        # On prend les 5 premiers résultats maximum
        for doc in reponse.get('docs', [])[:5]:
            titre_trouve = doc.get('title', 'Titre inconnu')
            auteur = ", ".join(doc.get('author_name', ['Inconnu']))
            annee = doc.get('first_publish_year', datetime.now().year)
            editeur_trouve = doc.get('publisher', ['Autre'])[0]
            
            resultats.append({
                "Titre": titre_trouve,
                "Auteur(s)": auteur,
                "Année": annee,
                "Éditeur": editeur_trouve
            })
        return resultats
    except:
        return []

# --- INTERFACE AVEC ONGLETS ---
onglet_collection, onglet_recherche_auto, onglet_ajout_manuel = st.tabs([
    "📋 Ma Collection", 
    "🔍 Recherche dans le Catalogue", 
    "✍️ Ajout Manuel Rapide"
])

# --- ONGLET 1 : MA COLLECTION ---
with onglet_collection:
    df = pd.read_sql_query("""
        SELECT id, titre as 'Titre', editeur as 'Éditeur', tome as 'N° Tome', 
        annee_publication as 'Année', scenariste as 'Auteur(s)', 
        prix as 'Prix (€)', note as 'Note /5', statut as 'Statut' 
        FROM comics
    """, conn)

    if not df.empty:
        # Stats
        total_comics = len(df)
        valeur_totale = df['Prix (€)'].sum()
        df['Note /5'] = df['Note /5'].apply(lambda x: "⭐" * int(x) if pd.notnull(x) else "")

        col_st1, col_st2 = st.columns(2)
        with col_st1: st.metric("Nombre de comics", f"{total_comics} ex.")
        with col_st2: st.metric("Valeur totale", f"{valeur_totale:.2f} €")
        
        st.write("---")
        
        # Filtres et Recherche locale
        recherche_locale = st.text_input("🔍 Rechercher un comic dans ma collection (Titre, Auteur...)", "")
        
        df_filtré = df.copy()
        if recherche_locale:
            df_filtré = df_filtré[
                df_filtré['Titre'].str.contains(recherche_locale, case=False, na=False) | 
                df_filtré['Auteur(s)'].str.contains(recherche_locale, case=False, na=False)
            ]

        # Affichage
        df_filtré = df_filtré.sort_values(by=["Titre", "N° Tome"])
        st.dataframe(df_filtré.drop(columns=["id"]), use_container_width=True)
        
        # Suppression
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
        st.info("Ta bibliothèque est vide. Utilise les autres onglets pour ajouter tes comics !")

# --- ONGLET 2 : RECHERCHE DANS LE CATALOGUE MONDIAL ---
with onglet_recherche_auto:
    st.subheader("🌐 Rechercher un comic existant")
    st.write("Tape le nom d'un comic (ex: *Batman The Killing Joke* ou *Spider-Man*). L'application va fouiller dans le catalogue mondial.")
    
    terme_recherche = st.text_input("Entrez le titre ou l'ISBN :", key="search_bar")
    
    if terme_recherche:
        with st.spinner("Recherche dans le catalogue en cours..."):
            resultats = chercher_dans_catalogue(terme_recherche)
            
        if resultats:
            st.write(f"### {len(resultats)} résultats trouvés :")
            for i, res in enumerate(resultats):
                with st.expander(f"📚 {res['Titre']} ({res['Année']}) - par {res['Auteur(s)']}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Éditeur d'origine :** {res['Éditeur']}")
                        tome_auto = st.number_input("Numéro / Tome", min_value=1, value=1, key=f"tome_{i}")
                        statut_auto = st.radio("Statut de lecture", ["À lire 🔴", "En cours 🟡", "Lu 🟢"], key=f"statut_{i}")
                    with col2:
                        prix_auto = st.number_input("Prix d'achat (€)", min_value=0.0, value=0.0, step=0.05, key=f"prix_{i}")
                        note_auto = st.slider("Ta Note", min_value=1, max_value=5, value=3, key=f"note_{i}")
                    
                    if st.button("Ajouter directement à ma collection", key=f"btn_{i}"):
                        cursor.execute(
                            """INSERT INTO comics (titre, editeur, tome, annee_publication, scenariste, prix, note, statut) 
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                            (res['Titre'], res['Éditeur'], tome_auto, res['Année'], res['Auteur(s)'], prix_auto, note_auto, statut_auto)
                        )
                        conn.commit()
                        st.success(f"🎉 '{res['Titre']}' a été ajouté à ta collection !")
        else:
            st.warning("Aucun comic trouvé avec ce nom. Essaie d'être plus précis ou utilise l'ajout manuel.")

# --- ONGLET 3 : AJOUT MANUEL RAPIDE ---
with onglet_ajout_manuel:
    st.subheader("✍️ Ajouter un comic introuvable dans le catalogue")
    annee_actuelle = datetime.now().year
    
    with st.form(key="manuel_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            t_man = st.text_input("Titre de la série / du comic *")
            e_man = st.selectbox("Éditeur", ["Marvel", "DC Comics", "Image Comics", "Urban Comics", "Panini Comics", "Autre"])
            tome_man = st.number_input("Numéro / Tome", min_value=1, value=1, step=1)
        with col2:
            a_man = st.number_input("Année de publication", min_value=1900, max_value=annee_actuelle+2, value=annee_actuelle, step=1)
            s_man = st.text_input("Scénariste / Dessinateur")
            p_man = st.number_input("Prix d'achat (€)", min_value=0.0, value=0.0, step=0.05)
            
        n_man = st.slider("Ta Note (Étoiles)", min_value=1, max_value=5, value=3)
        st_man = st.radio("Statut de lecture", ["À lire 🔴", "En cours 🟡", "Lu 🟢"], horizontal=True)
        
        submit_manuel = st.form_submit_button(label="Ajouter manuellement")
        
    if submit_manuel:
        if t_man:
            cursor.execute(
                """INSERT INTO comics (titre, editeur, tome, annee_publication, scenariste, prix, note, statut) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (t_man, e_man, tome_man, a_man, s_man, p_man, n_man, st_man)
            )
            conn.commit()
            st.success(f"🎉 '{t_man} #{tome_man}' ajouté avec succès !")
        else:
            st.error("Le titre est obligatoire !")
