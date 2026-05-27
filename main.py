import streamlit as st
import sqlite3
import pandas as pd

# --- CONFIGURATION STYLE ---
st.set_page_config(page_title="Mon Catalogue Comics", page_icon="📚", layout="wide")

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
st.caption("Système de recherche intelligent local — Éditeurs, Années et Couvertures incluses")

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

# --- GRAND CATALOGUE OFFICIEL EMBARQUÉ ---
CATALOGUE_REFERENCE = [
    {
        "titre": "Spider-Man / Wolverine : L'Arme X-traordinaire",
        "auteurs": "Jason Aaron, Adam Kubert",
        "editeur": "Panini Comics",
        "annee": "2011",
        "edition_suggeree": "Standard",
        "format_suggere": "Hardcover (Rigide)",
        "couverture": "https://images.unsplash.com/photo-1604871000636-074fa5117945?q=80&w=300"
    },
    {
        "titre": "Spider-Man & Wolverine : Intégrale",
        "auteurs": "Collectif, Marvel",
        "editeur": "Panini Comics",
        "annee": "2021",
        "edition_suggeree": "Intégrale / Omnibus",
        "format_suggere": "Intégrale",
        "couverture": "https://images.unsplash.com/photo-1635863138275-d9b33299680b?q=80&w=300"
    },
    {
        "titre": "Absolute Carnage - Édition Standard",
        "auteurs": "Donny Cates, Ryan Stegman",
        "editeur": "Panini Comics",
        "annee": "2020",
        "edition_suggeree": "Standard",
        "format_suggere": "Hardcover (Rigide)",
        "couverture": "https://images.unsplash.com/photo-1608889174637-3c44f6326f20?q=80&w=300"
    },
    {
        "titre": "Absolute Carnage - Omnibus Intégrale",
        "auteurs": "Donny Cates, Collectif",
        "editeur": "Panini Comics",
        "annee": "2022",
        "edition_suggeree": "Intégrale / Omnibus",
        "format_suggere": "Intégrale",
        "couverture": "https://images.unsplash.com/photo-1612036782180-6f0b6cd846fe?q=80&w=300"
    },
    {
        "titre": "Batman Chronicles : 1987",
        "auteurs": "Frank Miller, David Mazzucchelli",
        "editeur": "Urban Comics",
        "annee": "2022",
        "edition_suggeree": "Standard",
        "format_suggere": "Hardcover (Rigide)",
        "couverture": "https://images.unsplash.com/photo-1534447677768-be436bb09401?q=80&w=300"
    },
    {
        "titre": "Batman Chronicles : 1988",
        "auteurs": "Alan Moore, Dennis O'Neil",
        "editeur": "Urban Comics",
        "annee": "2023",
        "edition_suggeree": "Standard",
        "format_suggere": "Hardcover (Rigide)",
        "couverture": "https://images.unsplash.com/photo-1478760329108-5c3ed9d495a0?q=80&w=300"
    },
    {
        "titre": "Spawn - Intégrale Tome 1",
        "auteurs": "Todd McFarlane",
        "editeur": "Delcourt",
        "annee": "2018",
        "edition_suggeree": "Intégrale / Omnibus",
        "format_suggere": "Intégrale",
        "couverture": "https://images.unsplash.com/photo-1620336655055-088d06e36bf0?q=80&w=300"
    }
]

IMAGE_DE_SECOURS = "https://images.unsplash.com/photo-1610116306796-6ebd3051c330?q=80&w=300"
TYPES_EDITIONS = ["Standard", "Édition Collector", "Variant Cover", "Intégrale / Omnibus", "Tirage Limité", "Édition Originale (EO)", "Deluxe"]
ETATS_LIVRE = ["Neuf ✨", "Très bon état 👍", "Bon état 👌", "Usé 📖"]
FORMATS_LIVRE = ["Hardcover (Rigide)", "Softcover (Souple)", "Deluxe", "Intégrale"]

# --- MOTEUR DE RECHERCHE FLOU INTELLIGENT ---
def recherche_decoupee(texte):
    if not texte:
        return []
    # On découpe la recherche en mots (ex: ["spiderman", "wolverine"]) et on ignore les petits mots comme "et", "le"
    mots_recherche = [m.lower().strip() for m in texte.replace("/", " ").replace("-", " ").split() if len(m) > 1 and m.lower() not in ["et", "du", "le", "la", "un"]]
    
    if not mots_recherche:
        return []
        
    resultats = []
    for item in CATALOGUE_REFERENCE:
        titre_fusion = f"{item['titre']} {item['editeur']} {item['auteurs']}".lower()
        # Il suffit qu'un ou plusieurs mots-clés correspondent pour faire remonter l'album !
        score = sum(1 for mot in mots_recherche if mot in titre_fusion)
        if score > 0:
            resultats.append((score, item))
            
    # On trie pour mettre les meilleurs résultats en premier
    resultats.sort(key=lambda x: x[0], reverse=True)
    return [r[1] for r in resultats]

# --- ONGLETS ---
onglet_vitrine, onglet_recherche, onglet_stats = st.tabs([
    "🖼️ Mes Étagères (Bookshelf)", 
    "🔍 Chercher une Édition (BDGest)", 
    "📊 Statistiques"
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
                            st.image(row['couverture_url'] if row['couverture_url'] else IMAGE_DE_SECOURS, use_container_width=True)
                            st.markdown(f"**{row['titre']}**")
                            st.caption(f"{row['edition_speciale']} | {row['editeur']} ({row['annee_publication']})")
                            st.caption(f"Tome {row['tome']}")
                            
                            with st.popover("📝 Fiche BDGest"):
                                st.write(f"**Auteur(s) :** {row['scenariste']}")
                                st.write(f"**Format :** {row['format_livre']}")
                                st.write(f"**État :** {row['etat_livre']}")
                                st.write(f"**Prix :** {row['prix']:.2f} € | **Note :** {'⭐' * int(row['note'])}")
                                if row['commentaire']: st.caption(f"💬 *{row['commentaire']}*")
                                if st.button("🗑️ Supprimer", key=f"del_{row['id']}"):
                                    cursor.execute("DELETE FROM comics WHERE id = ?", (row['id'],))
                                    conn.commit()
                                    st.rerun()
            st.markdown('<div class="etagere-bois"></div>', unsafe_allow_html=True)
    else:
        st.info("Aucun album sur tes étagères. Va sur le deuxième onglet !")

# --- ONGLET 2 : RECHERCHE DES ÉDITIONS ---
with onglet_recherche:
    st.subheader("🌐 Grand Catalogue des Éditions")
    nom_recherche = st.text_input("Rechercher un album ou un héros (Ex: spiderman wolverine, carnage...) :", placeholder="Tape ici...")
    
    if nom_recherche:
        editions_trouvees = recherche_decoupee(nom_recherche)
        
        if editions_trouvees:
            st.success(f"Éditions correspondantes trouvées ! Cliquez pour ouvrir.")
            for idx, ed in enumerate(editions_trouvees):
                with st.expander(f"📚 {ed['titre']} — [{ed['editeur']}] ({ed['annee']})"):
                    col_img, col_form = st.columns([1, 3])
                    with col_img:
                        st.image(ed['couverture'], use_container_width=True)
                    with col_form:
                        st.markdown(f"### {ed['titre']}")
                        st.markdown(f"🏛️ **Éditeur :** `{ed['editeur']}` | 📅 **Année d'édition :** `{ed['annee']}`")
                        st.caption(f"✍️ **Auteurs :** {ed['auteurs']}")
                        
                        with st.form(key=f"form_add_{idx}"):
                            c1, c2, c3 = st.columns(3)
                            with c1:
                                num_tome = st.number_input("N° de Tome", min_value=1, value=1, key=f"tome_{idx}")
                                idx_t = TYPES_EDITIONS.index(ed['edition_suggeree']) if ed['edition_suggeree'] in TYPES_EDITIONS else 0
                                type_ed = st.selectbox("Type d'édition", TYPES_EDITIONS, index=idx_t, key=f"type_{idx}")
                            with c2:
                                idx_f = FORMATS_LIVRE.index(ed['format_suggere']) if ed['format_suggere'] in FORMATS_LIVRE else 0
                                format_l = st.selectbox("Format", FORMATS_LIVRE, index=idx_f, key=f"form_{idx}")
                                etat_l = st.selectbox("État", ETATS_LIVRE, key=f"etat_{idx}")
                            with c3:
                                prix_l = st.number_input("Prix payé (€)", min_value=0.0, value=16.0, step=0.5, key=f"prix_{idx}")
                                note_l = st.slider("Note", 1, 5, 4, key=f"note_{idx}")
                                
                            statut_l = st.radio("Lecture", ["À lire 🔴", "En cours 🟡", "Lu 🟢"], horizontal=True, key=f"statut_{idx}")
                            comm_l = st.text_input("Commentaire libre", key=f"comm_{idx}")
                            
                            if st.form_submit_button("📥 Ajouter à mes étagères"):
                                cursor.execute(
                                    """INSERT INTO comics (titre, editeur, tome, annee_publication, scenariste, prix, note, statut, couverture_url, edition_speciale, etat_livre, format_livre, commentary) 
                                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                                    (ed['titre'], ed['editeur'], num_tome, ed['annee'], ed['auteurs'], prix_l, note_l, statut_l, ed['couverture'], type_ed, etat_l, format_l, comm_l)
                                )
                                conn.commit()
                                st.success("✨ Ajouté avec succès !")
                                st.rerun()
        else:
            st.warning("Aucun résultat automatique pour ces mots-clés.")
            
    # FORMULAIRE MANUEL EN CAS DE HORS-PISTE
    st.write("---")
    with st.expander("➕ L'édition exacte n'est pas dans la liste ? Ajoute-la manuellement ici !"):
        with st.form(key="form_manuel"):
            cm1, cm2 = st.columns(2)
            with cm1:
                t_m = st.text_input("Titre complet *")
                e_m = st.text_input("Éditeur (Ex: Panini, Urban) *")
                a_m = st.text_input("Année d'édition *")
                aut_m = st.text_input("Auteurs")
                tome_m = st.number_input("Tome N°", min_value=1, value=1)
            with cm2:
                type_m = st.selectbox("Type d'édition", TYPES_EDITIONS)
                form_m = st.selectbox("Format du support", FORMATS_LIVRE)
                etat_m = st.selectbox("État", ETATS_LIVRE)
                prix_m = st.number_input("Prix d'achat (€)", min_value=0.0, value=15.0)
                note_m = st.slider("Ta Note", 1, 5, 4)
            cov_m = st.text_input("Lien URL d'une image de couverture (Optionnel)")
            statut_m = st.radio("Statut", ["À lire 🔴", "En cours 🟡", "Lu 🟢"], horizontal=True)
            comm_m = st.text_input("Commentaire")
            
            if st.form_submit_button("📥 Forcer l'enregistrement manuel"):
                if t_m and e_m and a_m:
                    cursor.execute(
                        """INSERT INTO comics (titre, editeur, tome, annee_publication, scenariste, prix, note, statut, couverture_url, edition_speciale, etat_livre, format_livre, commentaire) 
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (t_m, e_m, tome_m, a_m, aut_m, prix_m, note_m, statut_m, cov_m if cov_m else IMAGE_DE_SECOURS, type_m, etat_m, form_m, comm_m)
                    )
                    conn.commit()
                    st.success("✨ Ajouté manuellement !")
                    st.rerun()

# --- ONGLET 3 : STATS ---
with clan_stats if 'clan_stats' in locals() else onglet_stats:
    df_s = pd.read_sql_query("SELECT * FROM comics", conn)
    if not df_s.empty:
        c_m1, c_m2 = st.columns(2)
        c_m1.metric("Total", f"{len(df_s)} volumes")
        c_m2.metric("Valeur", f"{df_s['prix'].sum():.2f} €")
