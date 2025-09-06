# api.py
from flask import Flask, jsonify, request, redirect
from pymongo import MongoClient
import requests
import os

# --- Configuration ---
app = Flask(__name__)

# Récupère les secrets depuis les variables d'environnement de Render (plus sécurisé)
MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://StrexBot:Ethan2009_M@cluster0.vmdicn2.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
DISCORD_CLIENT_ID = os.environ.get("DISCORD_CLIENT_ID", "1379440380860174506")
DISCORD_CLIENT_SECRET = os.environ.get("DISCORD_CLIENT_SECRET", "YkbhLgkV_LfUcqh-iavFzu-hqB4_HeLO")

# L'URL de ton API. Change-la pour correspondre à celle sur Render.
API_BASE_URL = "https://strexbot-wuxw.onrender.com"
REDIRECT_URI = f"{API_BASE_URL}/callback"

# Connexion à MongoDB
client = MongoClient(MONGO_URI)
db = client.get_database("NomDeTaDB")
collection = db.get_collection("users")

# --- Route de Connexion Discord ---
@app.route('/callback')
def callback():
    # 1. On récupère le code temporaire que Discord nous a envoyé
    code = request.args.get('code')
    if not code:
        return "Erreur: Code manquant.", 400

    # 2. On échange ce code contre un "access token"
    token_data = {
        'client_id': DISCORD_CLIENT_ID,
        'client_secret': DISCORD_CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    r = requests.post('https://discord.com/api/oauth2/token', data=token_data, headers=headers)
    r.raise_for_status() # S'assure que la requête a réussi
    token_info = r.json()
    access_token = token_info['access_token']

    # 3. On utilise l'access token pour récupérer les infos de l'utilisateur
    headers = {'Authorization': f'Bearer {access_token}'}
    r_user = requests.get('https://discord.com/api/users/@me', headers=headers)
    r_user.raise_for_status()
    user_info = r_user.json()
    
    user_id = user_info['id']
    username = user_info['username']

    # 4. On sauvegarde l'utilisateur dans notre base de données MongoDB
    existing_user = collection.find_one({"user_id": user_id})
    if not existing_user:
        # Si l'utilisateur n'existe pas, on le crée avec un solde de 0
        new_user = {"user_id": user_id, "username": username, "coins": 0}
        collection.insert_one(new_user)

    # 5. Redirige l'utilisateur vers le site principal, en lui indiquant que c'est un succès
    # On pourra utiliser cette information plus tard pour afficher "Bienvenue, [username] !"
    return redirect("https://VOTRE_SITE_STATIQUE.onrender.com/?login_success=true")


# --- API pour les pièces (comme avant) ---
@app.route('/api/balance/<user_id>')
def get_balance(user_id):
    user_data = collection.find_one({"user_id": user_id})
    if user_data:
        response = {"user_id": user_data["user_id"], "coins": user_data.get("coins", 0)}
    else:
        response = {"user_id": user_id, "coins": 0, "error": "user not found"}
    return jsonify(response)


# --- Lancement du serveur ---
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
