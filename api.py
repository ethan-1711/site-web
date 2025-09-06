# api.py (Version améliorée avec gestion de session et données utilisateur)
from flask import Flask, jsonify, request, redirect, url_for, session
from pymongo import MongoClient
import requests
import os
import uuid # Pour générer des clés de session uniques

# --- Configuration ---
app = Flask(__name__)

# Utilise une clé secrète pour sécuriser les sessions
# C'est TRÈS important de la changer et de la garder secrète !
# Idéalement, elle vient des variables d'environnement de Render.
app.secret_key = os.environ.get("FLASK_SECRET_KEY", str(uuid.uuid4())) # Clé unique

MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://StrexBot:Ethan2009_M@cluster0.vmdicn2.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
DISCORD_CLIENT_ID = os.environ.get("DISCORD_CLIENT_ID", "1379440380860174506")
DISCORD_CLIENT_SECRET = os.environ.get("DISCORD_CLIENT_SECRET", "dEMMWohPhzv54qh1WFml9BpbY667A8Up")

API_BASE_URL = os.environ.get("API_BASE_URL", "https://strexbot-wuxw.onrender.com") # URL de ton API
REDIRECT_URI = f"{API_BASE_URL}/callback" # Doit correspondre à l'URL sur Discord Dev Portal
SITE_BASE_URL = os.environ.get("SITE_BASE_URL", "https://strexbot-site.onrender.com")

# Connexion à MongoDB
client = MongoClient(MONGO_URI)
db = client.get_database("strexbot_db") # Utilise le nom de ta base de données
users_collection = db.get_collection("users")

# --- Routes d'Authentification Discord ---

# Route appelée par Discord après la connexion
@app.route('/callback')
def callback():
    code = request.args.get('code')
    if not code:
        return "Erreur: Code d'autorisation manquant.", 400

    token_data = {
        'client_id': DISCORD_CLIENT_ID,
        'client_secret': DISCORD_CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'scope': 'identify' # Demande l'identification de l'utilisateur
    }
    
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    
    try:
        # Échange le code contre un token d'accès
        r = requests.post('https://discord.com/api/oauth2/token', data=token_data, headers=headers)
        r.raise_for_status() # Lève une exception pour les codes d'erreur HTTP
        token_info = r.json()
        access_token = token_info['access_token']

        # Utilise le token pour obtenir les infos de l'utilisateur
        headers = {'Authorization': f'Bearer {access_token}'}
        r_user = requests.get('https://discord.com/api/users/@me', headers=headers)
        r_user.raise_for_status()
        user_info = r_user.json()
        
        user_id = user_info['id']
        username = user_info['username']
        avatar_hash = user_info['avatar']
        
        # URL de l'avatar Discord (générée à partir du hash)
        avatar_url = f"https://cdn.discordapp.com/avatars/{user_id}/{avatar_hash}.png" if avatar_hash else "https://discord.com/assets/f4d71597a7266710ae72a6b21589a19c.png" # Avatar par défaut si pas d'avatar

        # 4. Enregistre/met à jour l'utilisateur dans MongoDB
        user_data_db = users_collection.find_one({"user_id": user_id})
        if not user_data_db:
            users_collection.insert_one({
                "user_id": user_id,
                "username": username,
                "coins": 0, # Nouveau user commence avec 0 pièces
                "avatar_url": avatar_url
            })
        else:
            # Met à jour le nom d'utilisateur et l'avatar si l'utilisateur existe déjà
            users_collection.update_one(
                {"user_id": user_id},
                {"$set": {"username": username, "avatar_url": avatar_url}}
            )
        
        # 5. Stocke l'ID de l'utilisateur dans la session Flask
        session['user_id'] = user_id
        session['username'] = username
        session['avatar_url'] = avatar_url

        # Redirige vers le site statique, potentiellement vers une page de profil
        return redirect(f"{SITE_BASE_URL}?logged_in=true")

    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de la requête Discord: {e}")
        return jsonify({"error": "Failed to authenticate with Discord"}), 500
    except Exception as e:
        print(f"Erreur inattendue: {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500

# Route de déconnexion
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('avatar_url', None)
    return redirect(SITE_BASE_URL)

# --- API pour les données utilisateur ---
@app.route('/api/user_data')
def get_user_data():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401
    
    user_data_db = users_collection.find_one({"user_id": user_id})
    if user_data_db:
        return jsonify({
            "user_id": user_data_db["user_id"],
            "username": user_data_db["username"],
            "coins": user_data_db.get("coins", 0),
            "avatar_url": user_data_db.get("avatar_url", "https://discord.com/assets/f4d71597a7266710ae72a6b21589a19c.png")
        })
    return jsonify({"error": "User not found in DB after auth"}), 404

# --- API pour la boutique ---
# Ceci est un exemple, tu devras l'étendre
@app.route('/api/buy_coins/<int:amount>', methods=['POST'])
def buy_coins(amount):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401
    
    # Simule l'achat (ici, on ajoute juste les pièces)
    # Dans un vrai système, il y aurait une intégration de paiement
    result = users_collection.update_one(
        {"user_id": user_id},
        {"$inc": {"coins": amount}} # $inc ajoute au lieu de remplacer
    )
    
    if result.modified_count > 0:
        updated_user = users_collection.find_one({"user_id": user_id})
        return jsonify({"status": "success", "new_coins": updated_user["coins"]})
    return jsonify({"error": "Failed to buy coins"}), 500


# --- Lancement du serveur ---
if __name__ == "__main__":
    # Pour le développement local, il faut définir les variables d'environnement
    # Ou les décommenter ci-dessous (mais JAMAIS faire ça en production)
    # os.environ["MONGO_URI"] = "VOTRE_CHAINE_ICI"
    # os.environ["DISCORD_CLIENT_ID"] = "VOTRE_ID_ICI"
    # os.environ["DISCORD_CLIENT_SECRET"] = "VOTRE_SECRET_ICI"
    # os.environ["API_BASE_URL"] = "http://127.0.0.1:5000" # Pour le test local
    # os.environ["SITE_BASE_URL"] = "http://127.0.0.1:8000" # URL de ton site statique local (si tu le sers avec un serveur web)

    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
