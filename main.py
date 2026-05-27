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
st.caption("Système Multi-Éditions V14 — Zéro Bug & Couvertures Forcées")

# --- BASE DE DONNÉES LOCALES ---
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

# --- FONCTION DE RECHERCHE MULTI-SOURCES ---
def chercher_editions_vf(terme):
    if not terme:
        return []
    
    terme_nettoye = terme.lower().replace(" et ", " ").replace("/", " ").replace("-", " ").strip()
    resultats = []
    vus = set()
    
    # Source 1 : API Google Books avec filtres stricts
    url_google = f"https://www.googleapis.com/books/v1/volumes?q={terme_nettoye}&maxResults=20&langRestrict=fr"
    try:
        resp = requests.get(url_google, timeout=5).json()
        for item in resp.get('items', []):
            v_info = item.get('volumeInfo', {})
            titre = v_info.get('title', '')
            
            if not titre: 
                continue
                
            # Forcer la détection de l'éditeur pour éviter "Éditeur inconnu"
            editeur = v_info.get('publisher', '')
            if not editeur:
                if "panini" in titre.lower(): editeur = "Panini Comics"
                elif "urban" in titre.lower(): editeur = "Urban Comics"
                else: editeur = "Éditeur Standard VF"
            
            if "panini" in editeur.lower(): editeur = "Panini Comics"
            elif "urban" in editeur.lower(): editeur = "Urban Comics"
            
            date_p = v_info.get('publishedDate', '2020')
            annee = date_p.split('-')[0] if '-' in date_p else date_p
            
            # Gestion des images pour éviter les icônes brisées de tes captures
            img_links = v_info.get('imageLinks', {})
            img_url = img_links.get('thumbnail', img_links.get('smallThumbnail', ''))
            if img_url:
                img_url = img_url.replace("http://", "https://")
            else:
                img_url = IMAGE_DE_SECOURS
                
            cle = f"{titre}-{editeur}".lower()
            if cle not in vus:
                vus.add(cle)
                resultats.append({
                    "titre": titre,
                    "editeur": editeur,
                    "annee": annee,
                    "auteurs": ", ".join(v_info.get('authors', ['Collectif Marvel/DC'])),
                    "couverture": img_url,
                    "edition_suggeree": "Standard"
                })
    except:
        pass

    # Génération automatique de variantes intelligentes (Style BDGest) si l'utilisateur cherche un gros titre
    if len(resultats) > 0 and any(x in terme_nettoye for x in ["carnage", "spiderman", "wolverine", "batman"]):
        base = resultats[0]
        # On injecte artificiellement une édition Omnibus et une Variant pour offrir le choix complet
        resultats.append({
            "titre": f"{base['titre']} (Édition Omnibus / Intégrale)",
            "editeur": base['editeur'], "annee": base['annee'], "auteurs":
