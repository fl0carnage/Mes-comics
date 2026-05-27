import streamlit as st
import sqlite3
import pandas as pd
import requests
import re

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

st.title("Mon Catalogue Comics & BD")
st.caption("Moteur de recherche Multi-Éditions VF (Scraper Google Books/Fnac Open API)")

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

IMAGE_DE_SECOURS = "https://images.unsplash.com/photo-1610116306796-6ebd3051c330?q=80&w=300"
TYPES_EDITIONS = ["Standard", "Édition Collector", "Variant Cover", "Intégrale / Omnibus", "Tirage Limité", "Édition Originale (EO)", "Deluxe"]
ETATS_LIVRE = ["Neuf ✨", "Très bon état 👍", "Bon état 👌", "Usé 📖"]
FORMATS_LIVRE = ["Hardcover (Rigide)", "Softcover (Souple)", "Deluxe", "Intégrale"]

# --- FONCTION SCRAPER / API MULTI-ÉDITIONS FRANÇAISES ---
def scraper_toutes_editions(nom_bd):
    # Nettoyage de la chaîne (ex: "spiderman et wolverine" devient "spiderman wolverine")
    mots = nom_bd.lower().replace(" et ", " ").replace("/", " ").replace("-", " ").split()
    mots_filtres = [m for m in mots if m not in ["le", "la", "les", "du", "un", "une", "avec"]]
    requete_propre = " ".join(mots_filtres)
    
    if not requete_propre:
        return []
        
    # Requête ciblée sur le marché francophone (&langRestrict=fr) pour choper Panini/Urban
    url = f"https://www.googleapis.com/books/v1/volumes?q={requete_propre}&langRestrict=fr&maxResults=20"
    
    try:
        reponse = requests.get(url).json()
        resultats = []
        
        for item in reponse.get('items', []):
            volume_info = item.get('volumeInfo', {})
            
            # Récupération et nettoyage du titre
            titre = volume_info.get('title', 'Sans titre')
            st_titre = volume_info.get('subtitle', '')
            titre_complet = f"{titre} - {st_titre}" if st_titre else titre
            
            # Filtrer pour éviter les doublons trop parfaits ou les romans textuels
            if "roman" in titre_complet.lower() or volume_info.get('printType', '') != 'BOOK':
                continue
                
            auteurs = ", ".join(volume_info.get('authors', ['Scénariste Inconnu']))
            
            # Détection de l'éditeur officiel
            editeur = volume_info.get('publisher', 'Éditeur non référencé')
            # Simplification des noms d'éditeurs bizarres renvoyés par l'API
            if "panini" in editeur.lower(): editeur = "Panini Comics"
            elif "urban" in editeur.lower(): editeur = "Urban Comics"
            elif "delcourt" in editeur.lower(): editeur = "Delcourt"
            elif "soleil" in editeur.lower(): editeur = "Soleil"
            elif "glenat" in editeur.lower(): editeur = "Glénat"
            
            # Année de publication
            date_pub = volume_info.get('publishedDate', 'N.C.')
            annee = date_pub.split('-')[0] if '-' in date_pub else date_pub
            
            # Détection automatique de la spécificité de l'édition
            edition_detectee = "Standard"
            desc = volume_info.get('description', '').lower()
            titre_low = titre_complet.lower()
            if "omnibus" in titre_low or "omnibus" in desc: edition_detectee = "Intégrale / Omnibus"
            elif "collector" in titre_low or "collector" in desc: edition_detectee = "Édition Collector"
            elif "deluxe" in titre_low or "deluxe" in desc: edition_detectee = "Deluxe"
            elif "variant" in titre_low or "variante" in desc: edition_detectee = "Variant Cover"
            
            # Gestion stricte de l'image de couverture pour éviter les icônes brisées
            images = volume_info.get('imageLinks', {})
            img_url = images.get('thumbnail', images.get('smallThumbnail', ''))
            if img_url:
                img_url = img_url.replace('http://', 'https://')  # Forçage SSL sécurisé pour Streamlit
            else:
                img_url = IMAGE_DE_SECOURS
                
            resultats.append({
                "titre": titre_complet,
                "auteurs": auteurs,
                "editeur": editeur,
                "annee": annee,
                "couverture": img_url,
                "edition_suggeree": edition_detectee
            })
            
        return resultats
    except:
        return []

# --- ONGLETS PRINCIPAUX ---
onglet_vitrine, onglet_recherche, onglet_stats = st.tabs([
    "🖼️ Mes Étagères (Bookshelf)", 
    "🔍 Chercher une Édition (Scraper)", 
    "📊 Statistiques"
])

# --- ONGLET 1 : VISUALISATION (MES ÉTAGÈRES) ---
with onglet_vitrine:
    df = pd.read_sql_query("SELECT * FROM comics", conn)
    if not df.empty:
        recherche_locale = st.text_input("🔍 Filtrer instantanément mes étagères (Titre, Auteur, Éditeur)...", "")
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
                            st.image(row['couverture_url'] if row['couverture_url'] else IMAGE_DE_SECOURS, use_container_width=True)
                            st.markdown(f"**{row['titre']}**")
                            st.caption(f"{row['edition_speciale']} | {row['editeur']} ({row['annee_publication']})")
                            st.caption(f"Tome {row['tome']}")
                            
                            with st.popover("📝 Fiche BDGest"):
                                st.write(f"**Auteurs :** {row['scenariste']}")
                                st.write(f"**Format :** {row['format_livre']}")
                                st.write(f"**État :** {row['etat_livre']}")
                                st.write(f"**Prix :** {row['prix']:.2f} € | **Note :** {'⭐' * int(row['note'])}")
                                st.write(f"**Statut :** {row['statut']}")
                                if row['commentaire']: st.caption(f"💬 *{row['commentaire']}*")
                                if st.button("🗑️ Supprimer", key=f"del_{row['id']}"):
                                    cursor.execute("DELETE FROM comics WHERE id = ?", (row['id'],))
                                    conn.commit()
                                    st.rerun()
            st.markdown('<div class="etagere-bois"></div>', unsafe_allow_html=True)
    else:
        st.info("Aucun album sur tes étagères. Va dans l'onglet 'Chercher une Édition' pour scanner le catalogue !")

# --- ONGLET 2 : MOTEUR DE RECHERCHE ET SCRAPER FR ---
with onglet_recherche:
    st.subheader("🌐 Recherche multi-éditions francophones")
    st.write("Le système va nettoyer ta saisie et chercher toutes les éditions françaises disponibles (Panini, Urban, etc.)")
    
    saisie_user = st.text_input("Tape ta recherche (Ex: spiderman et wolverine, absolute carnage) :", placeholder="Rechercher...")
    
    if saisie_user:
        with st.spinner("Scraping et alignement des éditions en cours..."):
            editions_trouvees = scraper_toutes_editions(saisie_user)
            
        if editions_trouvees:
            st.success(f"Nous avons localisé {len(editions_trouvees)} éditions dans les catalogues francophones !")
            
            for idx, ed in enumerate(editions_trouvees):
                # Titre de l'expander mis en valeur avec Éditeur et Année
                with st.expander(f"📚 {ed['titre']} — Éditeur : {ed['editeur']} ({ed['annee']})"):
                    col_img, col_form = st.columns([1, 3])
                    
                    with col_img:
                        st.image(ed['couverture'], use_container_width=True)
                        
                    with col_form:
                        st.markdown(f"### {ed['titre']}")
                        st.markdown(f"🏛️ **Maison d'édition :** `{ed['editeur']}` | 📅 **Année de sortie :** `{ed['annee']}`")
                        st.caption(f"✍️ **Auteur(s) référencé(s) :** {ed['auteurs']}")
                        
                        with st.form(key=f"form_add_{idx}"):
                            c1, c2, c3 = st.columns(3)
                            with c1:
                                num_tome = st.number_input("N° de Tome", min_value=1, value=1, key=f"tome_{idx}")
                                idx_t = TYPES_EDITIONS.index(ed['edition_suggeree']) if ed['edition_suggeree'] in TYPES_EDITIONS else 0
                                type_ed = st.selectbox("Type d'édition", TYPES_EDITIONS, index=idx_t, key=f"type_{idx}")
                            with c2:
                                format_l = st.selectbox("Format", FORMATS_LIVRE, key=f"form_{idx}")
                                etat_l = st.selectbox("État de l'exemplaire", ETATS_LIVRE, key=f"etat_{idx}")
                            with c3:
                                prix_l = st.number_input("Prix payé (€)", min_value=0.0, value=15.0, step=0.5, key=f"prix_{idx}")
                                note_l = st.slider("Ta note", 1, 5, 4, key=f"note_{idx}")
                                
                            statut_l = st.radio("Statut de lecture", ["À lire 🔴", "En cours 🟡", "Lu 🟢"], horizontal=True, key=f"statut_{idx}")
                            comm_l = st.text_input("Commentaire / Variante de couverture", key=f"comm_{idx}")
                            
                            if st.form_submit_button("📥 Valider et placer cette édition exacte"):
                                cursor.execute(
                                    """INSERT INTO comics (titre, editeur, tome, annee_publication, scenariste, prix, note, statut, couverture_url, edition_speciale, etat_livre, format_livre, commentaire) 
                                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                                    (ed['titre'], ed['editeur'], num_tome, ed['annee'], ed['auteurs'], prix_l, note_l, statut_l, ed['couverture'], type_ed, etat_l, format_l, comm_l)
                                )
                                conn.commit()
                                st.success("✨ Ajouté à tes étagères !")
                                st.rerun()
        else:
            st.warning("Aucun résultat trouvé de manière automatisée.")
            
    # SECTION AJOUT SUR MESURE (SI ÉDITION DE NICHE)
    st.write("---")
    with st.expander("➕ Ton édition est introuvable ou ultra-rare ? Ajoute-la manuellement en 5 secondes !"):
        with st.form(key="form_manuel_secours"):
            cm1, cm2 = st.columns(2)
            with cm1:
                t_m = st.text_input("Titre du comic *")
                e_m = st.text_input("Éditeur (Ex: Panini Comics, Urban) *")
                a_m = st.text_input("Année de parution *")
                aut_m = st.text_input("Auteurs")
                tome_m = st.number_input("Tome", min_value=1, value=1)
            with cm2:
                type_m = st.selectbox("Type d'édition", TYPES_EDITIONS)
                form_m = st.selectbox("Format", FORMATS_LIVRE)
                etat_m = st.selectbox("État", ETATS_LIVRE)
                prix_m = st.number_input("Prix (€)", min_value=0.0, value=15.0)
                note_m = st.slider("Note", 1, 5, 4)
            cov_m = st.text_input("URL d'une image de couverture (Optionnel)")
            statut_m = st.radio("Statut", ["À lire 🔴", "En cours 🟡", "Lu 🟢"], horizontal=True)
            comm_m = st.text_input("Notes libres")
            
            if st.form_submit_button("📥 Enregistrer l'édition sur mesure"):
                if t_m and e_m and a_m:
                    cursor.execute(
                        """INSERT INTO comics (titre, editeur, tome, annee_publication, scenariste, prix, note, statut, couverture_url, edition_speciale, etat_livre, format_livre, commentaire) 
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (t_m, e_m, tome_m, a_m, aut_m, prix_m, note_m, statut_m, cov_m if cov_m else IMAGE_DE_SECOURS, type_m, etat_m, form_m, comm_m)
                    )
                    conn.commit()
                    st.success("✨ Album ajouté !")
                    st.rerun()

# --- ONGLET 3 : STATISTIQUES ---
with onglet_stats:
    st.subheader("📊 Données de ta Collection")
    df_s = pd.read_sql_query("SELECT * FROM comics", conn)
    if not df_s.empty:
        col1, col2 = st.columns(2)
        col1.metric("Nombre total d'albums", f"{len(df_s)} volumes")
        col2.metric("Valeur financière de la collection", f"{df_s['prix'].sum():.2f} €")
        st.write("---")
        st.dataframe(df_s[['titre', 'tome', 'editeur', 'annee_publication', 'edition_speciale', 'etat_livre', 'prix', 'statut']], use_container_width=True, hide_index=True)
