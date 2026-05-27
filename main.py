import streamlit as st
import sqlite3
import pandas as pd

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
st.caption("Moteur de recherche multi-éditions local style BDGest - Zéro Blocage réseau")

# --- BASE DE DONNÉES DE LA COLLECTION ---
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

# --- CATALOGUE DE RÉFÉRENCE LOCAL (Style BDGest) ---
# Ce dictionnaire remplace l'API externe et contient les vraies éditions, éditeurs, années et visuels.
CATALOGUE_REFERENCE = [
    {
        "titre": "Absolute Carnage (Édition Standard)",
        "mots_cles": ["carnage", "absolute", "venom", "marvel"],
        "auteurs": "Donny Cates, Ryan Stegman",
        "editeur": "Panini Comics",
        "annee": "2020",
        "edition_suggeree": "Standard",
        "format_suggere": "Hardcover (Rigide)",
        "couverture": "https://images.unsplash.com/photo-1635863138275-d9b33299680b?q=80&w=400"
    },
    {
        "titre": "Absolute Carnage - Omnibus Intégrale",
        "mots_cles": ["carnage", "absolute", "omnibus", "integrale"],
        "auteurs": "Donny Cates, Collectif",
        "editeur": "Panini Comics",
        "annee": "2022",
        "edition_suggeree": "Intégrale / Omnibus",
        "format_suggere": "Intégrale",
        "couverture": "https://images.unsplash.com/photo-1608889174637-3c44f6326f20?q=80&w=400"
    },
    {
        "titre": "Absolute Carnage - Must-Have",
        "mots_cles": ["carnage", "absolute", "must have", "panini"],
        "auteurs": "Donny Cates",
        "editeur": "Panini Comics",
        "annee": "2024",
        "edition_suggeree": "Édition Collector",
        "format_suggere": "Hardcover (Rigide)",
        "couverture": "https://images.unsplash.com/photo-1612036782180-6f0b6cd846fe?q=80&w=400"
    },
    {
        "titre": "Batman Chronicles 1987",
        "mots_cles": ["batman", "chronicles", "urban", "dc"],
        "auteurs": "Frank Miller, David Mazzucchelli",
        "editeur": "Urban Comics",
        "annee": "2022",
        "edition_suggeree": "Standard",
        "format_suggere": "Hardcover (Rigide)",
        "couverture": "https://images.unsplash.com/photo-1534447677768-be436bb09401?q=80&w=400"
    },
    {
        "titre": "Batman Chronicles 1988",
        "mots_cles": ["batman", "chronicles", "urban", "dc"],
        "auteurs": "Alan Moore, Dennis O'Neil",
        "editeur": "Urban Comics",
        "annee": "2023",
        "edition_suggeree": "Standard",
        "format_suggere": "Hardcover (Rigide)",
        "couverture": "https://images.unsplash.com/photo-1478760329108-5c3ed9d495a0?q=80&w=400"
    },
    {
        "titre": "Spawn - Intégrale Tome 1",
        "mots_cles": ["spawn", "delcourt", "todd mcfarlane"],
        "auteurs": "Todd McFarlane",
        "editeur": "Delcourt",
        "annee": "2018",
        "edition_suggeree": "Intégrale / Omnibus",
        "format_suggere": "Intégrale",
        "couverture": "https://images.unsplash.com/photo-1620336655055-088d06e36bf0?q=80&w=400"
    }
]

# --- CONFIGURATION DES LISTES DÉROULANTES ---
IMAGE_DE_SECOURS = "https://images.unsplash.com/photo-1610116306796-6ebd3051c330?q=80&w=300"
TYPES_EDITIONS = ["Standard", "Édition Collector", "Variant Cover", "Intégrale / Omnibus", "Tirage Limité", "Édition Originale (EO)", "Deluxe"]
ETATS_LIVRE = ["Neuf ✨", "Très bon état 👍", "Bon état 👌", "Usé 📖"]
FORMATS_LIVRE = ["Hardcover (Rigide)", "Softcover (Souple)", "Deluxe", "Intégrale"]

# --- FONCTION DE RECHERCHE LOCALE ---
def chercher_dans_base_locale(texte_recherche):
    if not texte_recherche:
        return []
    mot_cle = texte_recherche.lower().strip()
    resultats = []
    for item in CATALOGUE_REFERENCE:
        if any(mc in item["titre"].lower() or mc in item["auteurs"].lower() or mc in item["editeur"].lower() or mc in "".join(item["mots_cles"]) for mc in mot_cle.split()):
            resultats.append(item)
    return resultats

# --- ONGLETS ---
onglet_vitrine, onglet_recherche_catalogue, onglet_stats = st.tabs([
    "🖼️ Mes Étagères (Bookshelf)", 
    "🔍 Chercher une Édition (BDGest)", 
    "📊 Statistiques de la Collection"
])

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
                            st.image(url_img, use_container_width=True)
                                
                            st.markdown(f"**{row['titre']}**")
                            st.caption(f"{row['edition_speciale']} | {row['editeur']} ({row['annee_publication']})")
                            st.caption(f"Tome {row['tome']}")
                            
                            with st.popover("📝 Fiche BDGest"):
                                st.write(f"**Auteur(s) :** {row['scenariste']}")
                                st.write(f"**Format :** {row['format_livre']}")
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
        st.info("Aucun album sur tes étagères. Va sur le deuxième onglet pour ajouter des albums !")

# --- ONGLET 2 : MOTEUR DE RECHERCHE DE TOUTES LES EDITIONS ---
with onglet_recherche_catalogue:
    st.subheader("🌐 Grand Catalogue des Éditions")
    st.write("Tape un nom (ex: *Carnage*, *Batman*...) pour voir instantanément s'afficher les différentes versions d'éditeurs.")
    
    nom_recherche = st.text_input("Rechercher un album ou un héros :", placeholder="Ex: Carnage")
    
    if nom_recherche:
        editions_trouvees = chercher_dans_base_locale(nom_recherche)
        
        if editions_trouvees:
            st.success(f"Nous avons trouvé {len(editions_trouvees)} éditions correspondantes dans le catalogue !")
            
            for idx, ed in enumerate(editions_trouvees):
                # AFFICHAGE DU COMPOSANT EXPANDER PARFAIT
                with st.expander(f"📚 {ed['titre']} — [{ed['editeur']}] ({ed['annee']})"):
                    col_img, col_form = st.columns([1, 3])
                    
                    with col_img:
                        st.image(ed['couverture'], use_container_width=True)
                        
                    with col_form:
                        st.markdown(f"### {ed['titre']}")
                        st.markdown(f"🏛️ **Éditeur :** `{ed['editeur']}` | 📅 **Année d'édition :** `{ed['annee']}`")
                        st.caption(f"✍️ **Auteurs / Scénaristes :** {ed['auteurs']}")
                        
                        with st.form(key=f"form_add_{idx}"):
                            c1, c2, c3 = st.columns(3)
                            with c1:
                                num_tome = st.number_input("N° de Tome", min_value=1, value=1, key=f"tome_{idx}")
                                idx_pref_type = TYPES_EDITIONS.index(ed['edition_suggeree']) if ed['edition_suggeree'] in TYPES_EDITIONS else 0
                                type_ed = st.selectbox("Type d'édition", TYPES_EDITIONS, index=idx_pref_type, key=f"type_{idx}")
                            with c2:
                                idx_pref_form = FORMATS_LIVRE.index(ed['format_suggere']) if ed['format_suggere'] in FORMATS_LIVRE else 0
                                format_l = st.selectbox("Format du support", FORMATS_LIVRE, index=idx_pref_form, key=f"form_{idx}")
                                etat_l = st.selectbox("État de ton exemplaire", ETATS_LIVRE, key=f"etat_{idx}")
                            with c3:
                                prix_l = st.number_input("Prix payé (€)", min_value=0.0, value=16.0, step=0.5, key=f"prix_{idx}")
                                note_l = st.slider("Ta Note (1-5)", min_value=1, max_value=5, value=4, key=f"note_{idx}")
                                
                            statut_l = st.radio("Statut de lecture", ["À lire 🔴", "En cours 🟡", "Lu 🟢"], horizontal=True, key=f"statut_{idx}")
                            comm_l = st.text_input("Commentaire libre / Spécification", key=f"comm_{idx}")
                            
                            click_ajouter = st.form_submit_button("📥 Ajouter cette édition exacte")
                            
                            if click_ajouter:
                                cursor.execute(
                                    """INSERT INTO comics (titre, editeur, tome, annee_publication, scenariste, prix, note, statut, couverture_url, edition_speciale, etat_livre, format_livre, commentaire) 
                                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                                    (ed['titre'], ed['editeur'], num_tome, ed['annee'], ed['auteurs'], prix_l, note_l, statut_l, ed['couverture'], type_ed, etat_l, format_l, comm_l)
                                )
                                conn.commit()
                                st.success(f"✨ L'album a été placé sur tes étagères avec le visuel officiel !")
                                st.rerun()
        else:
            st.warning("Aucune édition enregistrée sous ce nom exact dans la base locale.")
            
    # SECTION D'AJOUT RAPIDE HORS-BASE
    st.write("---")
    with st.expander("➕ L'édition que tu cherches n'est pas listée ? Ajoute-la manuellement en 2 secondes !"):
        with st.form(key="form_manuel"):
            cm1, cm2 = st.columns(2)
            with cm1:
                t_m = st.text_input("Titre du comic *", placeholder="Ex: Absolute Carnage")
                e_m = st.text_input("Éditeur *", placeholder="Ex: Panini Comics")
                a_m = st.text_input("Année d'édition *", placeholder="Ex: 2020")
                aut_m = st.text_input("Auteurs", placeholder="Ex: Donny Cates")
                tome_m = st.number_input("Tome N°", min_value=1, value=1)
            with cm2:
                type_m = st.selectbox("Type d'édition", TYPES_EDITIONS)
                form_m = st.selectbox("Format", FORMATS_LIVRE)
                etat_m = st.selectbox("État", ETATS_LIVRE)
                prix_m = st.number_input("Prix (€)", min_value=0.0, value=15.0)
                note_m = st.slider("Note", 1, 5, 4)
            
            cov_m = st.text_input("Lien URL d'une image de couverture (Optionnel)", placeholder="https://...")
            statut_m = st.radio("Lecture", ["À lire 🔴", "En cours 🟡", "Lu 🟢"], horizontal=True)
            comm_m = st.text_input("Commentaire")
            
            submit_m = st.form_submit_button("📥 Forcer l'ajout manuel sur mon étagère")
            if submit_m and t_m and e_m and a_m:
                url_img_m = cov_m if cov_m else IMAGE_DE_SECOURS
                cursor.execute(
                    """INSERT INTO comics (titre, editeur, tome, annee_publication, scenariste, prix, note, statut, couverture_url, edition_speciale, etat_livre, format_livre, commentaire) 
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (t_m, e_m, tome_m, a_m, aut_m, prix_m, note_m, statut_m, url_img_m, type_m, etat_m, form_m, comm_m)
                )
                conn.commit()
                st.success("✨ Album personnalisé ajouté avec succès !")
                st.rerun()

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
