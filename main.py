import streamlit as st
import sqlite3
import pandas as pd
import requests

# --- CONFIGURATION STYLE ---
st.set_page_config(page_title="Ma Bédéthèque Pro", page_icon="📚", layout="wide")

st.markdown("""
    <style>
    .etagere-bois {
        background-color: #8B5A2B;
        height: 15px;
        border-radius: 4px;
        margin-bottom: 25px;
        box-shadow: 0px 4px 8px rgba(0,0,0,0.3);
    }
    </style>
""", unsafe_allow_html=True)

st.title("📚 Mon Catalogue Comics & BD")
st.caption("Recherche multi-éditions automatisée avec design Bookshelf x BDGest")

# --- BASE DE DONNÉES ---
conn = sqlite3.connect("comics_collection.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS comics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titre TEXT,
        editeur TEXT,
        tome INTEGER,
        annee_publication TEXT,
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
conn.commit()

# --- NOUVEAU MOTEUR DE RECHERCHE PAR ÉDITIONS INDIVIDUELLES ---
def rechercher_multi_editions(nom_comic):
    recherche_propre = nom_comic.strip()
    # On cible directement le catalogue d'éditions d'Open Library
    url = f"https://openlibrary.org/search.json?q={recherche_propre}&limit=15"
    
    try:
        reponse = requests.get(url).json()
        resultats = []
        
        for doc in reponse.get('docs', []):
            titre_global = doc.get('title', 'Titre inconnu')
            auteurs = ", ".join(doc.get('author_name', ['Inconnu']))
            
            # Open Library regroupe souvent les éditeurs et années sous forme de listes pour chaque édition
            liste_editeurs = doc.get('publisher', ['Éditeur inconnu'])
            liste_annees = doc.get('publish_year', ['****'])
            liste_covers = doc.get('edition_key', [])
            
            # On va générer une entrée par édition disponible (max 4 par œuvre pour ne pas surcharger)
            nb_editions = min(len(liste_editeurs), 4)
            for k in range(nb_editions):
                editeur = liste_editeurs[k]
                annee = str(liste_annees[min(k, len(liste_annees)-1)])
                
                # Récupération de la couverture propre à cette version si dispo
                if k < len(liste_covers):
                    img_url = f"https://covers.openlibrary.org/b/olid/{liste_covers[k]}-M.jpg"
                else:
                    cover_id = doc.get('cover_i')
                    img_url = f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg" if cover_id else ""
                
                if not img_url or "-M.jpg" not in img_url:
                    img_url = "https://images.unsplash.com/photo-1610116306796-6ebd3051c330?q=80&w=300"
                
                resultats.append({
                    "titre": f"{titre_global}",
                    "auteurs": auteurs,
                    "editeur": editeur,
                    "annee": annee,
                    "couverture": img_url
                })
                
        return resultats
    except:
        return []

# --- ONGLETS PRINCIPAUX ---
onglet_vitrine, onglet_recherche_catalogue, onglet_stats = st.tabs([
    "🖼️ Mes Étagères (Bookshelf)", 
    "🔍 Chercher une Édition (BDGest)", 
    "📊 Statistiques de la Collection"
])

IMAGE_DE_SECOURS = "https://images.unsplash.com/photo-1610116306796-6ebd3051c330?q=80&w=300"
TYPES_EDITIONS = ["Standard", "Édition Collector", "Variant Cover", "Intégrale / Omnibus", "Tirage Limité", "Édition Originale (EO)"]
ETATS_LIVRE = ["Neuf ✨", "Très bon état 👍", "Bon état 👌", "Usé 📖"]
FORMATS_LIVRE = ["Hardcover (Rigide)", "Softcover (Souple)", "Deluxe", "Intégrale"]

# --- ONGLET 1 : LES ÉTAGÈRES VISUELLES ---
with onglet_vitrine:
    df = pd.read_sql_query("SELECT * FROM comics", conn)
    if not df.empty:
        recherche_locale = st.text_input("🔍 Filtrer instantanément mes étagères...", "")
        if recherche_locale:
            df = df[df['titre'].str.contains(recherche_locale, case=False, na=False) | df['editeur'].str.contains(recherche_locale, case=False, na=False)]
        
        df = df.sort_values(by=["titre", "tome"])
        
        nb_cols = 5
        liste_items = list(df.iterrows())
        for i in range(0, len(liste_items), nb_cols):
            cols = st.columns(nb_cols)
            for j in range(nb_cols):
                if i + j < len(liste_items):
                    idx, row = liste_items[i + j]
                    with cols[j]:
                        with st.container(border=True):
                            url_img = row['couverture_url'] if row['couverture_url'] else IMAGE_DE_SECOURS
                            try:
                                st.image(url_img, use_container_width=True)
                            except:
                                st.image(IMAGE_DE_SECOURS, use_container_width=True)
                                
                            st.markdown(f"**{row['titre']}**")
                            st.caption(f"Tome {row['tome']} | {row['editeur']}")
                            
                            with st.popover("📝 Fiche BDGest"):
                                st.write(f"**Auteur(s) :** {row['scenariste']}")
                                st.write(f"**Édition :** {row['edition_speciale']} ({row['format_livre']})")
                                st.write(f"**État :** {row['etat_livre']}")
                                st.write(f"**Prix :** {row['prix']:.2f} € | **Note :** {'⭐' * int(row['note'])}")
                                st.write(f"**Statut :** {row['statut']}")
                                if row['commentaire']:
                                    st.caption(f"💬 *{row['commentaire']}*")
                                if st.button("🗑️ Supprimer", key=f"del_{row['id']}"):
                                    cursor.execute("DELETE FROM comics WHERE id = ?", (row['id'],))
                                    conn.commit()
                                    st.rerun()
            st.markdown('<div class="etagere-bois"></div>', unsafe_allow_html=True)
    else:
        st.info("Aucun album sur tes étagères. Va sur le deuxième onglet pour lancer une recherche !")

# --- ONGLET 2 : MOTEUR DE RECHERCHE DE TOUTES LES EDITIONS ---
with onglet_recherche_catalogue:
    st.subheader("🌐 Grand Catalogue des Éditions")
    st.write("Tape un mot-clé (ex: *Carnage*, *Batman*, *Spawn*...) pour afficher toutes les déclinaisons d'éditeurs.")
    
    nom_recherche = st.text_input("Rechercher dans la base mondiale :", placeholder="Ex: Carnage")
    
    if nom_recherche:
        with st.spinner("Chargement des différentes éditions du catalogue..."):
            editions_trouvees = rechercher_multi_editions(nom_recherche)
            
        if editions_trouvees:
            st.success(f"Déclinaisons trouvées pour '{nom_recherche}' ! Choisis ta version ci-dessous :")
            
            for idx, ed in enumerate(editions_trouvees):
                titre_volet = (ed['titre'][:65] + '...') if len(ed['titre']) > 65 else ed['titre']
                
                with st.expander(f"📚 {titre_volet} — [{ed['editeur']}] ({ed['annee']})"):
                    col_img, col_form = st.columns([1, 3])
                    
                    with col_img:
                        try:
                            st.image(ed['couverture'], width=140)
                        except:
                            st.image(IMAGE_DE_SECOURS, width=140)
                        
                    with col_form:
                        st.markdown(f"### {ed['titre']}")
                        st.caption(f"✍️ **Auteurs :** {ed['auteurs']} | 🏛️ **Éditeur :** {ed['editeur']} | 📅 **Année :** {ed['annee']}")
                        
                        with st.form(key=f"form_add_{idx}"):
                            c1, c2, c3 = st.columns(3)
                            with c1:
                                num_tome = st.number_input("N° de Tome", min_value=1, value=1, key=f"tome_{idx}")
                                type_ed = st.selectbox("Type d'édition", TYPES_EDITIONS, key=f"type_{idx}")
                            with c2:
                                format_l = st.selectbox("Format du support", FORMATS_LIVRE, key=f"form_{idx}")
                                etat_l = st.selectbox("État de ton exemplaire", ETATS_LIVRE, key=f"etat_{idx}")
                            with c3:
                                prix_l = st.number_input("Prix d'achat (€)", min_value=0.0, value=15.0, step=0.5, key=f"prix_{idx}")
                                note_l = st.slider("Ta Note", min_value=1, max_value=5, value=4, key=f"note_{idx}")
                                
                            statut_l = st.radio("Statut de lecture", ["À lire 🔴", "En cours 🟡", "Lu 🟢"], horizontal=True, key=f"statut_{idx}")
                            comm_l = st.text_input("Commentaire libre (ex: Cover variante, EO...)", key=f"comm_{idx}")
                            
                            click_ajouter = st.form_submit_button("📥 Valider et placer sur mon étagère")
                            
                            if click_ajouter:
                                cursor.execute(
                                    """INSERT INTO comics (titre, editeur, tome, annee_publication, scenariste, prix, note, statut, couverture_url, edition_speciale, etat_livre, format_livre, commentaire) 
                                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                                    (ed['titre'], ed['editeur'], num_tome, ed['annee'], ed['auteurs'], prix_l, note_l, statut_l, ed['couverture'], type_ed, etat_l, format_l, comm_l)
                                )
                                conn.commit()
                                st.success(f"✨ L'édition de '{ed['titre']}' chez [{ed['editeur']}] a été ajoutée !")
                                st.rerun()
        else:
            st.warning("Aucun résultat. Essaie avec un mot-clé plus simple.")

# --- ONGLET 3 : SUIVI & STATS ---
with onglet_stats:
    st.subheader("📊 Données de ta Collection")
    df_s = pd.read_sql_query("SELECT * FROM comics", conn)
    if not df_s.empty:
        col_m1, col_m2 = st.columns(2)
        with col_m1: st.metric("Nombre total d'albums", f"{len(df_s)} volumes")
        with col_m2: st.metric("Valeur estimée du catalogue", f"{df_s['prix'].sum():.2f} €")
        st.write("---")
        st.dataframe(df_s[['titre', 'tome', 'editeur', 'annee_publication', 'edition_speciale', 'etat_livre', 'prix', 'statut']], use_container_width=True, hide_index=True)
    else:
        st.info("Ajoute des albums pour voir tes statistiques.")
