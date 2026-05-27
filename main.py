import streamlit as st
import sqlite3
import pandas as pd
import requests
from datetime import datetime

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Mon Comic Den Collector", page_icon="📚", layout="wide")
st.title("📚 Mon Gestionnaire de Comics & Éditions Spéciales")

# --- CONNEXION BASE DE DONNÉES ---
conn = sqlite3.connect("comics_collection.db", check_same_thread=False)
cursor = conn.cursor()

# Création de la table avec les nouvelles colonnes (couverture et edition_speciale)
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
        note INTEGER,
        couverture_url TEXT,
        edition_speciale TEXT
    )
''')

# Sécurité pour ajouter les colonnes si la table existait déjà
for col, type_col in [("couverture_url", "TEXT"), ("edition_speciale", "TEXT")]:
    try:
        cursor.execute(f"ALTER TABLE comics ADD COLUMN {col} {type_col}")
    except sqlite3.OperationalError:
        pass
conn.commit()

# --- FONCTION DE RECHERCHE DANS LE CATALOGUE ---
def chercher_dans_catalogue(recherche):
    url = f"https://openlibrary.org/search.json?q={recherche}&type=work"
    try:
        reponse = requests.get(url).json()
        resultats = []
        for doc in reponse.get('docs', [])[:5]:
            titre_trouve = doc.get('title', 'Titre inconnu')
            auteur = ", ".join(doc.get('author_name', ['Inconnu']))
            annee = doc.get('first_publish_year', datetime.now().year)
            editeur_trouve = doc.get('publisher', ['Autre'])[0]
            
            # Récupération sécurisée de l'ID de la couverture
            cover_id = doc.get('cover_i')
            
            # Si le cover_id est absent, vaut 0, ou n'est pas valide, on met l'image par défaut
            if not cover_id or str(cover_id) == "0":
                img_url = "https://images.unsplash.com/photo-1588666309990-d68f08e3d4a6?q=80&w=300&auto=format&fit=crop" # Une jolie image de bibliothèque par défaut
            else:
                img_url = f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg"
            
            resultats.append({
                "Titre": titre_trouve,
                "Auteur(s)": auteur,
                "Année": annee,
                "Éditeur": editeur_trouve,
                "Couverture": img_url
            })
        return resultats
    except:
        return []

# --- INTERFACE AVEC ONGLETS ---
onglet_collection, onglet_recherche_auto, onglet_ajout_manuel = st.tabs([
    "📋 Ma Collection", 
    "🔍 Catalogue Mondial (Auto)", 
    "✍️ Ajout Manuel"
])

# --- TYPES D'ÉDITIONS DISPONIBLES ---
TYPES_EDITIONS = ["Standard", "Édition Collector", "Variant Cover", "Intégrale / Omnibus", "Tirage Limité", "Signé / Dédicacé"]

# --- ONGLET 1 : MA COLLECTION ---
with onglet_collection:
    df = pd.read_sql_query("""
        SELECT id, titre, editeur, tome, annee_publication, scenariste, prix, note, statut, couverture_url, edition_speciale 
        FROM comics
    """, conn)

    if not df.empty:
        # Barre de recherche locale
        recherche_locale = st.text_input("🔍 Rechercher dans ma collection (Titre, Auteur, Édition...)", "")
        if recherche_locale:
            df = df[
                df['titre'].str.contains(recherche_locale, case=False, na=False) | 
                df['scenariste'].str.contains(recherche_locale, case=False, na=False) |
                df['edition_speciale'].str.contains(recherche_locale, case=False, na=False)
            ]
        
        df = df.sort_values(by=["titre", "tome"])

        # --- AFFICHAGE SOUS FORME DE GRILLE VISUELLE ---
        st.write("### 🖼️ Vue Galerie")
        
        # On affiche les comics par lignes de 4 colonnes
        colonnes_grille = st.columns(4)
        for index, row in df.iterrows():
            col_courante = colonnes_grille[index % 4]
            with col_courante:
                with st.container(border=True):
                    # Affichage de la couverture
                    url_img = row['couverture_url'] if row['couverture_url'] else "https://via.placeholder.com/150x225.png?text=No+Cover"
                    st.image(url_img, use_container_width=True)
                    
                    # Infos du comic
                    st.markdown(f"**{row['titre']} #{row['tome']}**")
                    st.caption(f"📅 {row['annee_publication']} | 🏛️ {row['editeur']}")
                    
                    # Badge pour l'édition spéciale
                    if row['edition_speciale'] and row['edition_speciale'] != "Standard":
                        st.info(f"✨ {row['edition_speciale']}")
                        
                    st.write(f"✍️ *{row['scenariste']}*")
                    st.write(f"💰 {row['prix']:.2f} € | {'⭐' * int(row['note'])}")
                    st.write(f"Statut : {row['statut']}")
        
        # --- SECTION SUPPRESSION ---
        st.write("---")
        st.subheader("🗑️ Supprimer un élément")
        labels_suppr = df["titre"] + " #" + df["tome"].astype(str) + " (" + df["edition_speciale"].fillna("Standard") + ")"
        df['Label_Suppression'] = labels_suppr
        comic_a_supprimer = st.selectbox("Choisir un comic à retirer", df['Label_Suppression'].unique())
        
        if st.button("Supprimer définitivement"):
            index_choisi = df.index[df['Label_Suppression'] == comic_a_supprimer].tolist()[0]
            id_database = int(df.iloc[index_choisi]["id"])
            cursor.execute("DELETE FROM comics WHERE id = ?", (id_database,))
            conn.commit()
            st.rerun()
    else:
        st.info("Ta bibliothèque est vide. Ajoute tes premiers comics avec les autres onglets !")

# --- ONGLET 2 : RECHERCHE AUTO + COUVERTURE ---
with onglet_recherche_auto:
    st.subheader("🌐 Recherche automatique de couvertures")
    terme_recherche = st.text_input("Entrez le titre du comic :", key="search_bar")
    
    if terme_recherche:
        with st.spinner("Recherche des visuels en cours..."):
            resultats = chercher_dans_catalogue(terme_recherche)
            
        if resultats:
            for i, res in enumerate(resultats):
                with st.expander(f"📖 {res['Titre']} ({res['Année']})"):
                    col_img, col_form = st.columns([1, 2])
                    
                    with col_img:
                        st.image(res['Couverture'], width=150)
                        
                    with col_form:
                        c1, c2 = st.columns(2)
                        with c1:
                            tome_auto = st.number_input("Numéro / Tome", min_value=1, value=1, key=f"tome_{i}")
                            ed_speciale_auto = st.selectbox("Type d'édition", TYPES_EDITIONS, key=f"spec_{i}")
                            statut_auto = st.radio("Statut", ["À lire 🔴", "En cours 🟡", "Lu 🟢"], key=f"statut_{i}")
                        with c2:
                            prix_auto = st.number_input("Prix d'achat (€)", min_value=0.0, value=0.0, step=0.05, key=f"prix_{i}")
                            note_auto = st.slider("Ta Note", min_value=1, max_value=5, value=3, key=f"note_{i}")
                        
                        if st.button("Ajouter à ma collection", key=f"btn_{i}"):
                            cursor.execute(
                                """INSERT INTO comics (titre, editeur, tome, annee_publication, scenariste, prix, note, statut, couverture_url, edition_speciale) 
                                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                                (res['Titre'], res['Éditeur'], tome_auto, res['Année'], res['Auteur(s)'], prix_auto, note_auto, statut_auto, res['Couverture'], ed_speciale_auto)
                            )
                            conn.commit()
                            st.success(f"🎉 '{res['Titre']}' ajouté avec succès !")
        else:
            st.warning("Aucun résultat.")

# --- ONGLET 3 : AJOUT MANUEL AVEC URL COUVERTURE ---
with onglet_ajout_manuel:
    st.subheader("✍️ Ajouter manuellement une version très spéciale")
    annee_actuelle = datetime.now().year
    
    with st.form(key="manuel_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            t_man = st.text_input("Titre *")
            e_man = st.selectbox("Éditeur", ["Marvel", "DC Comics", "Urban Comics", "Panini Comics", "Image Comics", "Autre"])
            tome_man = st.number_input("Numéro / Tome", min_value=1, value=1)
            ed_speciale_man = st.selectbox("Type d'édition", TYPES_EDITIONS)
        with col2:
            a_man = st.number_input("Année", min_value=1900, max_value=annee_actuelle+2, value=annee_actuelle)
            s_man = st.text_input("Auteurs (Scénariste/Dessinateur)")
            p_man = st.number_input("Prix (€)", min_value=0.0, value=0.0, step=0.05)
            url_img_man = st.text_input("Lien/URL d'une image de couverture (facultatif)")
            
        n_man = st.slider("Note", min_value=1, max_value=5, value=3)
        st_man = st.radio("Statut de lecture", ["À lire 🔴", "En cours 🟡", "Lu 🟢"], horizontal=True)
        
        submit_manuel = st.form_submit_button(label="Ajouter l'édition spéciale")
        
    if submit_manuel:
        if t_man:
            cursor.execute(
                """INSERT INTO comics (titre, editeur, tome, annee_publication, scenariste, prix, note, statut, couverture_url, edition_speciale) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (t_man, e_man, tome_man, a_man, s_man, p_man, n_man, st_man, url_img_man, ed_speciale_man)
            )
            conn.commit()
            st.success(f"🎉 Édition '{t_man}' enregistrée !")
