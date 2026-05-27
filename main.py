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

# --- MOTEUR DE RECHERCHE PRÉCIS (ÉDITEUR, ANNÉE, COUVERTURE) ---
def rechercher_multi_editions(nom_comic):
    recherche_propre = nom_comic.strip()
    # Utilisation de l'API Google Books sans filtre bloquant pour maximiser les résultats
    url = f"https://www.googleapis.com/books/v1/volumes?q={recherche_propre}&maxResults=15"
    
    try:
        reponse = requests.get(url).json()
        resultats = []
        
        for item in reponse.get('items', []):
            volume_info = item.get('volumeInfo', {})
            
            titre_global = volume_info.get('title', 'Titre inconnu')
            sous_titre = volume_info.get('subtitle', '')
            titre_complet = f"{titre_global} - {sous_titre}" if sous_titre else titre_global
            
            auteurs = ", ".join(volume_info.get('authors', ['Inconnu']))
            
            # Extraction propre de l'éditeur
            editeur = volume_info.get('publisher', 'Éditeur non spécifié')
            
            # Extraction propre de l'année
            date_pub = volume_info.get('publishedDate', '')
            annee = date_pub.split('-')[0] if '-' in date_pub else date_pub
            if not annee:
                annee = "N.C."
                
            # Récupération de l'édition spécifique ou description courte
            description = volume_info.get('description', '')
            edition_trouvee = "Standard"
            if "omnibus" in titre_complet.lower() or "omnibus" in description.lower():
                edition_trouvee = "Intégrale / Omnibus"
            elif "collector" in titre_complet.lower() or "collector" in description.lower():
                edition_trouvee = "Édition Collector"
            elif "deluxe" in titre_complet.lower() or "deluxe" in description.lower():
                edition_trouvee = "Deluxe"
                
            # Gestion et forçage de l'image de couverture en HTTPS pour éviter l'icône brisée
            images = volume_info.get('imageLinks', {})
            img_url = images.get('thumbnail', images.get('smallThumbnail', ''))
            
            if img_url:
                if img_url.startswith('http://'):
                    img_url = img_url.replace('http://', 'https://')
            else:
                img_url = "https://images.unsplash.com/photo-1610116306796-6ebd3051c330?q=80&w=300"
                
            resultats.append({
                "titre": titre_complet,
                "auteurs": auteurs,
                "editeur": editeur,
                "annee": annee,
                "couverture": img_url,
                "edition_suggeree": edition_trouvee
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
TYPES_EDITIONS = ["Standard", "Édition Collector", "Variant Cover", "Intégrale / Omnibus", "Tirage Limité", "Édition Originale (EO)", "Deluxe"]
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
                                st.write(f"**Année :** {row['annee_publication']}")
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
    st.write("Tape un nom (ex: *Absolute Carnage*, *Batman Chronicles*...) pour charger l'éditeur historique, l'année et l'image officielle.")
    
    nom_recherche = st.text_input("Rechercher dans la base mondiale :", placeholder="Ex: Absolute Carnage")
    
    if nom_recherche:
        with st.spinner("Chargement des données détaillées du catalogue..."):
            editions_trouvees = rechercher_multi_editions(nom_recherche)
            
        if editions_trouvees:
            st.success(f"Éditions identifiées pour '{nom_recherche}' ! Choisis ton volume :")
            
            for idx, ed in enumerate(editions_trouvees):
                titre_volet = (ed['titre'][:65] + '...') if len(ed['titre']) > 65 else ed['titre']
                
                # Le titre du volet affiche désormais dynamiquement l'éditeur et l'année trouvés !
                with st.expander(f"📚 {titre_volet} — Éditeur : {ed['editeur']} ({ed['annee']})"):
                    col_img, col_form = st.columns([1, 3])
                    
                    with col_img:
                        # Affichage de la couverture récupérée
                        st.image(ed['couverture'], use_container_width=True)
                        
                    with col_form:
                        st.markdown(f"### {ed['titre']}")
                        st.markdown(f"🏛️ **Éditeur officiel :** `{ed['editeur']}` | 📅 **Année de sortie :** `{ed['annee']}`")
                        st.caption(f"✍️ **Auteurs :** {ed['auteurs']}")
                        
                        with st.form(key=f"form_add_{idx}"):
                            c1, c2, c3 = st.columns(3)
                            with c1:
                                num_tome = st.number_input("N° de Tome", min_value=1, value=1, key=f"tome_{idx}")
                                # Pré-sélectionne intelligemment le type d'édition détecté (Omnibus, Collector...)
                                idx_pref = TYPES_EDITIONS.index(ed['edition_suggeree']) if ed['edition_suggeree'] in TYPES_EDITIONS else 0
                                type_ed = st.selectbox("Type d'édition", TYPES_EDITIONS, index=idx_pref, key=f"type_{idx}")
                            with c2:
                                format_l = st.selectbox("Format du support", FORMATS_LIVRE, key=f"form_{idx}")
                                etat_l = st.selectbox("État de ton exemplaire", ETATS_LIVRE, key=f"etat_{idx}")
                            with c3:
                                prix_l = st.number_input("Prix d'achat (€)", min_value=0.0, value=15.0, step=0.5, key=f"prix_{idx}")
                                note_l = st.slider("Ta Note", min_value=1, max_value=5, value=4, key=f"note_{idx}")
                                
                            statut_l = st.radio("Statut de lecture", ["À lire 🔴", "En cours 🟡", "Lu 🟢"], horizontal=True, key=f"statut_{idx}")
                            comm_l = st.text_input("Commentaire / Note libre", key=f"comm_{idx}")
                            
                            click_ajouter = st.form_submit_button("📥 Confirmer cette édition exacte")
                            
                            if click_ajouter:
                                cursor.execute(
                                    """INSERT INTO comics (titre, editeur, tome, annee_publication, scenariste, prix, note, statut, couverture_url, edition_speciale, etat_livre, format_livre, commentaire) 
                                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                                    (ed['titre'], ed['editeur'], num_tome, ed['annee'], ed['auteurs'], prix_l, note_l, statut_l, ed['couverture'], type_ed, etat_l, format_l, comm_l)
                                )
                                conn.commit()
                                st.success(f"✨ L'édition de '{ed['titre']}' chez {ed['editeur']} ({ed['annee']}) a été ajoutée à tes étagères !")
                                st.rerun()
        else:
            st.warning("Aucun résultat. Réessaie avec un mot-clé plus générique.")

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
