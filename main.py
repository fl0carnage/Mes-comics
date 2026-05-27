import streamlit as st
import sqlite3
import pandas as pd
import urllib.parse
from datetime import datetime

# --- CONFIGURATION STYLE "BOOKSHELF" ---
st.set_page_config(page_title="Ma Bibliothèque de Comics", page_icon="📚", layout="wide")

# CSS personnalisé pour créer l'effet d'étagères en bois (木) comme sur Bookshelf
st.markdown("""
    <style>
    .etagere-bois {
        background-color: #8B5A2B;
        height: 15px;
        border-radius: 4px;
        margin-bottom: 25px;
        box-shadow: 0px 4px 8px rgba(0,0,0,0.3);
    }
    .card-comic {
        background-color: #1E1E1E;
        padding: 10px;
        border-radius: 8px;
        box-shadow: 0px 4px 6px rgba(0,0,0,0.2);
    }
    </style>
""", unsafe_allow_html=True)

st.title("📚 Ma Bédéthèque Perso")
st.caption("Le look visuel de Bookshelf combiné à la précision de BDGest.")

# --- BASE DE DONNÉES BDGEST STYLE ---
conn = sqlite3.connect("comics_collection.db", check_same_thread=False)
cursor = conn.cursor()

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
        edition_speciale TEXT,
        etat_livre TEXT,
        format_livre TEXT,
        commentaire TEXT
    )
''')

# Mise à jour des colonnes pour les données précises de type BDGest
colonnes_bdgest = [
    ("etat_livre", "TEXT"),
    ("format_livre", "TEXT"),
    ("commentaire", "TEXT")
]
for col, type_col in colonnes_bdgest:
    try:
        cursor.execute(f"ALTER TABLE comics ADD COLUMN {col} {type_col}")
    except sqlite3.OperationalError:
        pass
conn.commit()

# --- STRUCTURE DES ONGLETS ---
onglet_bibliotheque, onglet_BDGest_stats, onglet_nouvel_ajout = st.tabs([
    "🖼️ Ma Bibliothèque (Bookshelf)", 
    "📊 Suivi & Stats (BDGest)", 
    "➕ Ajouter un Album"
])

TYPES_EDITIONS = ["Standard", "Édition Collector", "Variant Cover", "Intégrale / Omnibus", "Tirage Limité", "Édition Originale (EO)"]
ETATS_LIVRE = ["Neuf ✨", "Très bon état 👍", "Bon état 👌", "Usé 📖", "Abîmé 💥"]
FORMATS_LIVRE = ["Hardcover (Rigide)", "Softcover (Souple)", "Deluxe", "Manga / Poche", "Autre"]
IMAGE_DE_SECOURS = "https://images.unsplash.com/photo-1610116306796-6ebd3051c330?q=80&w=300&auto=format&fit=crop"

# --- ONGLET 1 : LES ÉTAGÈRES VISUELLES (BOOKSHELF) ---
with onglet_bibliotheque:
    df = pd.read_sql_query("SELECT * FROM comics", conn)
    
    if not df.empty:
        # Recherche et Filtres rapides
        col_recherche, col_filtre_editeur, col_filtre_statut = st.columns([2, 1, 1])
        with col_recherche:
            recherche = st.text_input("🔍 Rechercher un titre, un auteur, un mot-clé...", "")
        with col_filtre_editeur:
            editeurs_dispo = ["Tous"] + list(df['editeur'].unique())
            choix_editeur = st.selectbox("Filtrer par Éditeur", editeurs_dispo)
        with col_filtre_statut:
            statuts_dispo = ["Tous"] + list(df['statut'].unique())
            choix_statut = st.selectbox("Filtrer par Statut", statuts_dispo)
            
        # Application des filtres
        df_filtre = df.copy()
        if recherche:
            df_filtre = df_filtre[df_filtre['titre'].str.contains(recherche, case=False, na=False) | df_filtre['scenariste'].str.contains(recherche, case=False, na=False)]
        if choix_editeur != "Tous":
            df_filtre = df_filtre[df_filtre['editeur'] == choix_editeur]
        if choix_statut != "Tous":
            df_filtre = df_filtre[df_filtre['statut'] == choix_statut]

        df_filtre = df_filtre.sort_values(by=["titre", "tome"])

        # --- DESSIN DES ÉTAGÈRES ---
        st.write("---")
        
        # On affiche par rangées de 5 comics sur l'étagère
        nb_colonnes = 5
        liste_comics = list(df_filtre.iterrows())
        
        for i in range(0, len(liste_comics), nb_colonnes):
            cols_etagere = st.columns(nb_colonnes)
            
            for j in range(nb_colonnes):
                if i + j < len(liste_comics):
                    idx, row = liste_comics[i + j]
                    with cols_etagere[j]:
                        # Case du Comic
                        url_img = row['couverture_url'] if row['couverture_url'] and row['couverture_url'].strip() != "" else IMAGE_DE_SECOURS
                        
                        # Affichage de la couverture avec effet de survol natif streamlit container
                        with st.container(border=True):
                            try:
                                st.image(url_img, use_container_width=True)
                            except:
                                st.image(IMAGE_DE_SECOURS, use_container_width=True)
                            
                            st.markdown(f"**{row['titre']} #{row['tome']}**")
                            st.caption(f"{row['editeur']} ({row['annee_publication']})")
                            
                            # Popover d'infos (Clic pour ouvrir les détails complets façon BDGest)
                            with st.popover("🔎 Détails complets"):
                                st.markdown(f"### {row['titre']} #{row['tome']}")
                                st.write(f"**Éditeur :** {row['editeur']} | **Année :** {row['annee_publication']}")
                                st.write(f"**Auteur(s) :** {row['scenariste'] if row['scenariste'] else 'Non spécifié'}")
                                st.write(f"**Version :** {row['edition_speciale']} ({row['format_livre']})")
                                st.write(f"**État du livre :** {row['etat_livre']}")
                                st.write(f"**Prix payé :** {row['prix']:.2f} €")
                                st.write(f"**Note :** {'⭐' * int(row['note'])}")
                                st.write(f"**Statut de lecture :** {row['statut']}")
                                if row['commentaire']:
                                    st.info(f"💬 *Note perso : {row['commentaire']}*")
                                    
                                # Bouton supprimer à l'intérieur du détail
                                if st.button("🗑️ Supprimer cet album", key=f"del_{row['id']}"):
                                    cursor.execute("DELETE FROM comics WHERE id = ?", (row['id'],))
                                    conn.commit()
                                    st.rerun()
            
            # La planche de bois sous les 5 comics de cette ligne !
            st.markdown('<div class="etagere-bois"></div>', unsafe_allow_html=True)
            
    else:
        st.info("Ton étagère est vide. Ajoute ton premier album dans le 3ème onglet !")

# --- ONGLET 2 : SUIVI & STATS PRÉCISES (BDGEST STYLE) ---
with onglet_BDGest_stats:
    st.subheader("📊 Tableau de Bord de la Collection")
    df_stats = pd.read_sql_query("SELECT * FROM comics", conn)
    
    if not df_stats.empty:
        c_tot, c_val, c_lu = st.columns(3)
        with c_tot:
            st.metric("Total d'albums possédés", f"{len(df_stats)} ex.")
        with c_val:
            st.metric("Valeur financière du catalogue", f"{df_stats['prix'].sum():.2f} €")
        with c_lu:
            lus = len(df_stats[df_stats['statut'] == "Lu 🟢"])
            st.metric("Albums lus", f"{lus} / {len(df_stats)}")
            
        st.write("---")
        st.write("### 📋 Vue en liste tableur complète")
        # Affichage d'un vrai tableau de gestion propre
        df_affichage = df_stats[['titre', 'tome', 'editeur', 'annee_publication', 'edition_speciale', 'format_livre', 'etat_livre', 'prix', 'statut']].copy()
        df_affichage.columns = ['Titre', 'Tome N°', 'Éditeur', 'Année', 'Édition', 'Format', 'État', 'Prix (€)', 'Statut']
        st.dataframe(df_affichage, use_container_width=True, hide_index=True)
    else:
        st.info("Aucune statistique disponible pour le moment.")

# --- ONGLET 3 : FORMULAIRE D'ENTRÉE AMÉLIORÉ (BDGEST) ---
with onglet_nouvel_ajout:
    st.subheader("➕ Ajouter une nouvelle pièce au catalogue")
    annee_actuelle = datetime.now().year
    
    with st.form(key="form_complet_bdgest"):
        col1, col2 = st.columns(2)
        
        with col1:
            f_titre = st.text_input("Titre de la série / de l'album *")
            f_editeur = st.selectbox("Éditeur *", ["Panini Comics", "Urban Comics", "Marvel", "DC Comics", "Delcourt", "Glénat", "Dargaud", "Dupuis", "Le Lombard", "Autre"])
            f_tome = st.number_input("Numéro du Tome", min_value=1, value=1, step=1)
            f_auteur = st.text_input("Auteurs (Scénariste / Dessinateur)")
            f_annee = st.number_input("Année d'édition", min_value=1900, max_value=annee_actuelle+2, value=annee_actuelle)
            
        with col2:
            f_edition = st.selectbox("Type d'édition", TYPES_EDITIONS)
            f_format = st.selectbox("Format du livre", FORMATS_LIVRE)
            f_etat = st.selectbox("État de votre exemplaire", ETATS_LIVRE)
            f_prix = st.number_input("Prix d'achat ou estimation (€)", min_value=0.0, value=0.0, step=0.05)
            f_statut = st.radio("Statut de lecture", ["À lire 🔴", "En cours 🟡", "Lu 🟢"], horizontal=True)

        st.write("---")
        st.write("#### 🖼️ Visuel de la Couverture")
        f_url_image = st.text_input("Colle l'adresse URL de la couverture précise :", placeholder="https://mon-site.com/couverture_originale.jpg")
        
        f_note = st.slider("Ta Note personnelle", min_value=1, max_value=5, value=3)
        f_commentaire = st.text_area("Zone de notes / Commentaires libres (Ex: Acheter le tome suivant, dédicace obtenue au festival...)", "")
        
        bouton_sauvegarde = st.form_submit_button("💾 Enregistrer l'album sur mon étagère")

    # Moteur de recherche d'image Google intelligent juste en dessous
    if f_titre:
        requete_image = f"{f_titre} {f_editeur} tome {f_tome} {f_edition} couverture"
        url_recherche_google = f"https://www.google.com/search?tbm=isch&q={urllib.parse.quote(requete_image)}"
        st.info("💡 **Trouve la couverture exacte pour tes étagères :**")
        st.link_button(f"🔍 Ouvrir Google Images pour '{f_titre} #{f_tome}'", url_recherche_google)
        st.caption("👉 Clique, fais un clic droit sur la bonne image sur Google -> **'Copier l'adresse de l'image'**, puis colle-la dans la case 'Visuel de la Couverture' ci-dessus.")

    if bouton_sauvegarde:
        if f_titre:
            cursor.execute(
                """INSERT INTO comics (titre, editeur, tome, annee_publication, scenariste, prix, note, statut, couverture_url, edition_speciale, etat_livre, format_livre, commentaire) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (f_titre, f_editeur, f_tome, f_annee, f_auteur, f_prix, f_note, f_statut, f_url_image, f_edition, f_etat, f_format, f_commentaire)
            )
            conn.commit()
            st.success(f"🎉 '{f_titre} #{f_tome}' a rejoint ta bibliothèque en ligne !")
        else:
            st.error("Le titre de l'album est obligatoire !")
