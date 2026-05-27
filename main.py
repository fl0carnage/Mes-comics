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
st.caption("Gestionnaire de bédéthèque personnalisé")

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

# --- ONGLETS ---
onglet_vitrine, onglet_ajout, onglet_stats = st.tabs([
    "🖼️ Mes Étagères (Bookshelf)", 
    "➕ Ajouter un Album à ma Collection",
    "📊 Statistiques"
])

# --- ONGLET 1 : LES ÉTAGÈRES ---
with onglet_vitrine:
    df = pd.read_sql_query("SELECT * FROM comics", conn)
    if not df.empty:
        recherche_locale = st.text_input("🔍 Filtrer mes étagères (Titre, éditeur...)...", "")
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
        st.info("Aucun album sur tes étagères pour le moment. Utilise le deuxième onglet pour ajouter tes premiers comics !")

# --- ONGLET 2 : FORMULAIRE D'AJOUT MAÎTRISÉ ---
with onglet_ajout:
    st.subheader("📝 Ajouter manuellement une édition exacte")
    st.write("Pour éviter les erreurs des bases de données américaines, entre ici les vraies infos de ton album.")
    
    with st.form(key="form_manuel_principal"):
        cm1, cm2 = st.columns(2)
        with cm1:
            t_m = st.text_input("Titre de l'album / Série *", placeholder="Ex: Absolute Carnage")
            e_m = st.text_input("Éditeur (Ex: Panini Comics, Urban Comics) *", placeholder="Ex: Panini Comics")
            a_m = st.text_input("Année de publication *", placeholder="Ex: 2020")
            aut_m = st.text_input("Auteurs / Dessinateurs", placeholder="Ex: Donny Cates, Ryan Stegman")
            tome_m = st.number_input("Numéro de Tome", min_value=1, value=1)
        with cm2:
            type_m = st.selectbox("Type d'édition (Spécificité)", TYPES_EDITIONS)
            form_m = st.selectbox("Format du support", FORMATS_LIVRE)
            etat_m = st.selectbox("État de ton exemplaire", ETATS_LIVRE)
            prix_m = st.number_input("Prix d'achat (€)", min_value=0.0, value=15.0, step=0.5)
            note_m = st.slider("Ta Note", 1, 5, 4)
            
        st.write("---")
        cov_m = st.text_input("🔗 Lien URL de l'image de couverture", placeholder="Fais un clic droit sur une image Google -> 'Copier l'adresse de l'image'")
        statut_m = st.radio("Statut de lecture", ["À lire 🔴", "En cours 🟡", "Lu 🟢"], horizontal=True)
        comm_m = st.text_input("Commentaire libre (Ex: Édition avec couverture variante collector)")
        
        envoi = st.form_submit_button("📥 Placer ce comic sur mon étagère")
        
        if envoi:
            if t_m and e_m and a_m:
                url_finale = cov_m.strip() if cov_m else IMAGE_DE_SECOURS
                cursor.execute(
                    """INSERT INTO comics (titre, editeur, tome, annee_publication, scenariste, prix, note, statut, couverture_url, edition_speciale, etat_livre, format_livre, commentaire) 
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (t_m, e_m, tome_m, a_m, aut_m, prix_m, note_m, statut_m, url_finale, type_m, etat_m, form_m, comm_m)
                )
                conn.commit()
                st.success(f"✨ '{t_m}' a été correctement ajouté à ton étagère !")
                st.rerun()
            else:
                st.error("Veuillez remplir les champs obligatoires (*) : Titre, Éditeur et Année.")

# --- ONGLET 3 : STATS ---
with onglet_stats:
    st.subheader("📊 Données de ta Collection")
    df_s = pd.read_sql_query("SELECT * FROM comics", conn)
    if not df_s.empty:
        c_m1, c_m2 = st.columns(2)
        c_m1.metric("Total d'albums", f"{len(df_s)} volumes")
        c_m2.metric("Valeur de la collection", f"{df_s['prix'].sum():.2f} €")
        st.write("---")
        st.dataframe(df_s[['titre', 'tome', 'editeur', 'annee_publication', 'edition_speciale', 'etat_livre', 'prix', 'statut']], use_container_width=True, hide_index=True)
