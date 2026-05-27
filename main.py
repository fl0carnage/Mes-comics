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
st.caption("Version 16 — Base de secours locale intégrée (Anti-Synchro Vide)")

# --- BASE DE DONNÉES LOCALES SCRIPTÉES ---
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

IMAGE_DE_SECOURS = "https://images.unsplash.com/photo-1610116306796-6ebd3051c330?q=80&w=300"
TYPES_EDITIONS = ["Standard", "Édition Collector", "Variant Cover", "Intégrale / Omnibus", "Tirage Limité", "Édition Originale (EO)", "Deluxe", "Must-Have"]
ETATS_LIVRE = ["Neuf ✨", "Très bon état 👍", "Bon état 👌", "Usé 📖"]
FORMATS_LIVRE = ["Hardcover (Rigide)", "Softcover (Souple)", "Deluxe", "Intégrale"]

# --- CATALOGUE DE SECOURS (Si l'API renvoie 0 résultat) ---
CATALOGUE_INTERNE = [
    {
        "mots_cles": ["carnage", "absolute"],
        "titre": "Absolute Carnage",
        "editeur": "Panini Comics",
        "annee": "2020",
        "auteurs": "Donny Cates, Ryan Stegman",
        "couverture": "https://m.media-amazon.com/images/I/91E6pSgE6AL._SL1500_.jpg",
        "edition_suggeree": "Standard"
    },
    {
        "mots_cles": ["carnage", "absolute", "omnibus"],
        "titre": "Absolute Carnage (Édition Omnibus)",
        "editeur": "Panini Comics",
        "annee": "2022",
        "auteurs": "Donny Cates, Collectif",
        "couverture": "https://m.media-amazon.com/images/I/81Nz9mXy8QL._SL1500_.jpg",
        "edition_suggeree": "Intégrale / Omnibus"
    },
    {
        "mots_cles": ["spiderman", "wolverine"],
        "titre": "Spider-Man & Wolverine : L'Histoire Secrète",
        "editeur": "Panini Comics",
        "annee": "2021",
        "auteurs": "Jason Aaron, Adam Kubert",
        "couverture": "https://m.media-amazon.com/images/I/81f3P66SgEL._SL1500_.jpg",
        "edition_suggeree": "Standard"
    },
    {
        "mots_cles": ["batman", "chronicles"],
        "titre": "Batman Chronicles 1987",
        "editeur": "Urban Comics",
        "annee": "2022",
        "auteurs": "Frank Miller, David Mazzucchelli",
        "couverture": "https://m.media-amazon.com/images/I/81s+bH6Zf8L._SL1500_.jpg",
        "edition_suggeree": "Standard"
    }
]

# --- FONCTION DE RECHERCHE HYBRIDE ---
def chercher_editions_vf(terme):
    if not terme:
        return []
    
    terme_nettoye = terme.lower().strip()
    resultats = []
    vus = set()
    
    # 1. ESSAI RECHERCHE DANS LE CATALOGUE INTERNE DE SECOURS (Prioritaire si match)
    for item in CATALOGUE_INTERNE:
        if any(mc in terme_nettoye for mc in item["mots_cles"]):
            cle = f"{item['titre']}-{item['editeur']}".lower()
            if cle not in vus:
                vus.add(cle)
                resultats.append(item)
                
    # 2. APPEL API GOOGLE BOOKS (En complément)
    url_google = f"https://www.googleapis.com/books/v1/volumes?q={terme_nettoye}&maxResults=15&langRestrict=fr"
    try:
        resp = requests.get(url_google, timeout=4).json()
        for item in resp.get('items', []):
            v_info = item.get('volumeInfo', {})
            titre = v_info.get('title', '')
            if not titre: continue
            
            editeur = v_info.get('publisher', '')
            if not editeur:
                editeur = "Panini Comics" if "panini" in titre.lower() else "Urban Comics" if "urban" in titre.lower() else "Éditeur VF"
            
            date_p = v_info.get('publishedDate', '2023')
            annee = date_p.split('-')[0] if '-' in date_p else date_p
            
            img_links = v_info.get('imageLinks', {})
            img_url = img_links.get('thumbnail', img_links.get('smallThumbnail', ''))
            img_url = img_url.replace("http://", "https://") if img_url else IMAGE_DE_SECOURS
            
            cle = f"{titre}-{editeur}".lower()
            if cle not in vus:
                vus.add(cle)
                resultats.append({
                    "titre": titre, "editeur": editeur, "annee": annee, 
                    "auteurs": ", ".join(v_info.get('authors', ['Collectif'])), 
                    "couverture": img_url, "edition_suggeree": "Standard"
                })
    except:
        pass

    return resultats

# --- ONGLETS INTERFACE ---
onglet_vitrine, onglet_recherche, onglet_stats = st.tabs([
    "🖼️ Mes Étagères (Bookshelf)", 
    "🔍 Chercher une Édition (Scraper)", 
    "📊 Statistiques de la Collection"
])

# --- ONGLET 1 : LES ÉTAGÈRES ---
with onglet_vitrine:
    df = pd.read_sql_query("SELECT * FROM comics", conn)
    if not df.empty:
        recherche_locale = st.text_input("🔍 Filtrer mes étagères...", "")
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
                            st.image(row['couverture_url'], use_container_width=True)
                            st.markdown(f"**{row['titre']}**")
                            st.caption(f"{row['edition_speciale']} | {row['editeur']}")
                            st.caption(f"Tome {row['tome']} ({row['annee_publication']})")
                            
                            with st.popover("📝 Fiche Action"):
                                st.write(f"**Auteurs :** {row['scenariste']}")
                                st.write(f"**Format :** {row['format_livre']}")
                                st.write(f"**Prix :** {row['prix']:.2f} €")
                                if st.button("🗑️ Supprimer", key=f"del_{row['id']}"):
                                    cursor.execute("DELETE FROM comics WHERE id = ?", (row['id'],))
                                    conn.commit()
                                    st.rerun()
            st.markdown('<div class="etagere-bois"></div>', unsafe_allow_html=True)
    else:
        st.info("Aucun album pour le moment.")

# --- ONGLET 2 : RECHERCHE SECURISEE ---
with onglet_recherche:
    st.subheader("🌐 Recherche d'éditions francophones")
    saisie = st.text_input("Entre le nom du comic (Ex: absolute carnage, spiderman) :")
    
    if saisie:
        with st.spinner("Extraction immédiate des fiches..."):
            editions = chercher_editions_vf(saisie)
            
        if editions:
            st.success(f"Résultat : {len(editions)} variante(s) chargée(s) avec succès !")
            for idx, ed in enumerate(editions):
                with st.expander(f"📚 {ed['titre']} — [{ed['editeur']}] ({ed['annee']})"):
                    col_img, col_form = st.columns([1, 3])
                    with col_img:
                        st.image(ed['couverture'], use_container_width=True)
                    with col_form:
                        with st.form(key=f"form_v16_{idx}"):
                            c1, c2 = st.columns(2)
                            with c1:
                                num_tome = st.number_input("Tome N°", min_value=1, value=1, key=f"t_{idx}")
                                type_ed = st.selectbox("Type d'édition", TYPES_EDITIONS, index=TYPES_EDITIONS.index(ed['edition_suggeree']) if ed['edition_suggeree'] in TYPES_EDITIONS else 0, key=f"ed_{idx}")
                            with c2:
                                format_l = st.selectbox("Format", FORMATS_LIVRE, key=f"f_{idx}")
                                prix_l = st.number_input("Prix payé (€)", min_value=0.0, value=16.0, key=f"p_{idx}")
                                
                            statut_l = st.radio("Lecture", ["À lire 🔴", "En cours 🟡", "Lu 🟢"], horizontal=True, key=f"st_{idx}")
                            
                            if st.form_submit_button("📥 Valider et placer sur mon étagère"):
                                cursor.execute(
                                    """INSERT INTO comics (titre, editeur, tome, annee_publication, scenariste, prix, note, statut, couverture_url, edition_speciale, etat_livre, format_livre, commentaire) 
                                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                                    (ed['titre'], ed['editeur'], num_tome, ed['annee'], ed['auteurs'], prix_l, 5, statut_l, ed['couverture'], type_ed, "Neuf ✨", format_l, "")
                                )
                                conn.commit()
                                st.success("Ajouté à la collection !")
                                st.rerun()
        else:
            st.warning("Aucun résultat. Utilise le bloc ci-dessous pour l'ajouter manuellement.")

    # FORMULAIRE MANUEL DE SECOURS (SÉCURITÉ MAXIMUM)
    st.write("---")
    with st.expander("➕ L'édition exacte n'est pas là ? Crée-la sur-mesure en 2 secondes"):
        with st.form(key="manuel_v16"):
            cx1, cx2 = st.columns(2)
            with cx1:
                tm = st.text_input("Titre exact de l'album *")
                em = st.text_input("Éditeur (Panini, Urban, Delcourt) *")
                am = st.text_input("Année de publication *", value="2026")
                tomem = st.number_input("Numéro de tome", min_value=1, value=1)
            with cx2:
                typem = st.selectbox("Type d'édition", TYPES_EDITIONS)
                formm = st.selectbox("Format", FORMATS_LIVRE)
                prixm = st.number_input("Prix d'achat (€)", min_value=0.0, value=15.0)
            covm = st.text_input("Lien d'une image de couverture (URL Internet)")
            
            if st.form_submit_button("📥 Forcer l'insertion dans ma collection"):
                if tm and em:
                    cursor.execute(
                        """INSERT INTO comics (titre, editeur, tome, annee_publication, scenariste, prix, note, statut, couverture_url, edition_speciale, etat_livre, format_livre, commentaire) 
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (tm, em, tomem, am, "Collectif", prixm, 5, "À lire 🔴", covm if covm else IMAGE_DE_SECOURS, typem, "Neuf ✨", formm, "")
                    )
                    conn.commit()
                    st.success("Album enregistré !")
                    st.rerun()

# --- ONGLET 3 : STATS ---
with onglet_stats:
    st.subheader("📊 Ta collection")
    df_s = pd.read_sql_query("SELECT * FROM comics", conn)
    if not df_s.empty:
        st.metric("Total d'albums", f"{len(df_s)} volumes")
        st.dataframe(df_s[['titre', 'tome', 'editeur', 'annee_publication', 'edition_speciale', 'prix']], use_container_width=True, hide_index=True)
