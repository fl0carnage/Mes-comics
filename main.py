import streamlit as st
import sqlite3
import pandas as pd
import urllib.parse
from datetime import datetime

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Mon Comic Den Collector", page_icon="📚", layout="wide")
st.title("📚 Mon Gestionnaire de Comics Visuel")

# --- CONNEXION BASE DE DONNÉES ---
conn = sqlite3.connect("comics_collection.db", check_same_thread=False)
cursor = conn.cursor()

# Création de la table
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
conn.commit()

# --- INTERFACE AVEC ONGLETS ---
onglet_collection, onglet_ajout_visuel = st.tabs([
    "📋 Ma Collection & Galerie", 
    "➕ Ajouter un Comic à ma Collection"
])

TYPES_EDITIONS = ["Standard", "Édition Collector", "Variant Cover", "Intégrale / Omnibus", "Tirage Limité", "Signé / Dédicacé"]
IMAGE_DE_SECOURS = "https://images.unsplash.com/photo-1588666309990-d68f08e3d4a6?q=80&w=300&auto=format&fit=crop"

# --- ONGLET 1 : MA COLLECTION ---
with onglet_collection:
    df = pd.read_sql_query("""
        SELECT id, titre, editeur, tome, annee_publication, scenariste, prix, note, statut, couverture_url, edition_speciale 
        FROM comics
    """, conn)

    if not df.empty:
        # Barre de recherche locale
        recherche_locale = st.text_input("🔍 Filtrer ma collection (Titre, Auteur, Éditeur, Édition...)", "")
        if recherche_locale:
            df = df[
                df['titre'].str.contains(recherche_locale, case=False, na=False) | 
                df['scenariste'].str.contains(recherche_locale, case=False, na=False) |
                df['editeur'].str.contains(recherche_locale, case=False, na=False) |
                df['edition_speciale'].str.contains(recherche_locale, case=False, na=False)
            ]
        
        df = df.sort_values(by=["titre", "tome"])

        # Affichage en Galerie
        st.write("---")
        colonnes_grille = st.columns(4)
        for index, row in df.reset_index().iterrows():
            col_courante = colonnes_grille[index % 4]
            with col_courante:
                with st.container(border=True):
                    # Affichage de la couverture (si URL valide, sinon image de secours)
                    url_img = row['couverture_url'] if row['couverture_url'] and row['couverture_url'].strip() != "" else IMAGE_DE_SECOURS
                    try:
                        st.image(url_img, use_container_width=True)
                    except:
                        st.image(IMAGE_DE_SECOURS, use_container_width=True)
                    
                    st.markdown(f"### {row['titre']} #{row['tome']}")
                    
                    # Badge édition spéciale
                    if row['edition_speciale'] and row['edition_speciale'] != "Standard":
                        st.warning(f"✨ {row['edition_speciale']}")
                    else:
                        st.caption("📦 Édition Standard")
                        
                    st.write(f"🏛️ **Éditeur :** {row['editeur']}")
                    st.write(f"📅 **Année :** {row['annee_publication']}")
                    if row['scenariste']:
                        st.write(f"✍️ *{row['scenariste']}*")
                    st.write(f"💰 {row['prix']:.2f} € | {'⭐' * int(row['note'])}")
                    st.write(f"Statut : {row['statut']}")
        
        # Section Suppression
        st.write("---")
        st.subheader("🗑️ Supprimer un élément")
        df['Label_Suppression'] = df["titre"] + " #" + df["tome"].astype(str) + " (" + df["edition_speciale"].fillna("Standard") + ")"
        comic_a_supprimer = st.selectbox("Choisir un comic à retirer", df['Label_Suppression'].unique())
        
        if st.button("Supprimer définitivement"):
            index_choisi = df.index[df['Label_Suppression'] == comic_a_supprimer].tolist()[0]
            id_database = int(df.iloc[index_choisi]["id"])
            cursor.execute("DELETE FROM comics WHERE id = ?", (id_database,))
            conn.commit()
            st.st.rerun()
    else:
        st.info("Ta bibliothèque est vide. Utilise l'onglet d'ajout pour commencer !")

# --- ONGLET 2 : AJOUT AVEC ASSISTANCE RECHERCHE IMAGE ---
with onglet_ajout_visuel:
    st.subheader("✍️ Enregistrer un nouveau comic")
    st.write("Remplis les infos du comic. L'application t'aidera à trouver la **vraie image exacte** de ta couverture sur Google.")
    
    annee_actuelle = datetime.now().year
    
    with st.form(key="form_ajout_visuel"):
        col1, col2 = st.columns(2)
        with col1:
            t_titre = st.text_input("Titre de la série / de l'album *")
            t_editeur = st.selectbox("Éditeur *", ["Panini Comics", "Urban Comics", "Marvel", "DC Comics", "Delcourt", "Glénat", "Autre"])
            t_tome = st.number_input("Numéro / Tome", min_value=1, value=1)
            t_edition = st.selectbox("Type d'édition", TYPES_EDITIONS)
        with col2:
            t_annee = st.number_input("Année de publication", min_value=1900, max_value=annee_actuelle+2, value=annee_actuelle)
            t_auteur = st.text_input("Auteurs (Scénariste / Dessinateur)")
            t_prix = st.number_input("Prix d'achat (€)", min_value=0.0, value=0.0, step=0.05)
            
        st.write("---")
        st.write("#### 🖼️ Étape Couverture :")
        
        t_url_image = st.text_input("Colle ici l'adresse (URL) de la vraie couverture :", placeholder="https://exemple.com/image.jpg")
        
        t_note = st.slider("Ta Note (Étoiles)", min_value=1, max_value=5, value=3)
        t_statut = st.radio("Statut de lecture", ["À lire 🔴", "En cours 🟡", "Lu 🟢"], horizontal=True)
        
        bouton_valider = st.form_submit_button("💾 Sauvegarder dans ma collection")

    # Bouton d'aide à la recherche hors du formulaire pour s'actualiser en direct
    if t_titre:
        # On prépare la recherche Google pour l'utilisateur
        requete_recherche = f"{t_titre} {t_editeur} tome {t_tome} {t_edition} couverture"
        url_google_images = f"https://www.google.com/search?tbm=isch&q={urllib.parse.quote(requete_recherche)}"
        
        st.info("💡 **Besoin de la couverture exacte ?**")
        st.link_button(f"🔍 Chercher la couverture de '{t_titre}' sur Google Images", url_google_images)
        st.caption("👉 Clique sur le bouton ci-dessus, fais un **clic droit** sur la bonne image sur Google -> **'Copier l'adresse de l'image'**, puis colle-la dans la case du formulaire ci-dessus.")

    if bouton_valider:
        if t_titre:
            cursor.execute(
                """INSERT INTO comics (titre, editeur, tome, annee_publication, scenariste, prix, note, statut, couverture_url, edition_speciale) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (t_titre, t_editeur, t_tome, t_annee, t_auteur, t_prix, t_note, t_statut, t_url_image, t_edition)
            )
            conn.commit()
            st.success(f"🎉 '{t_titre} #{t_tome}' ({t_edition}) a été ajouté avec succès !")
        else:
            st.error("Le titre est obligatoire !")
