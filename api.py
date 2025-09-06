# api.py
from flask import Flask, jsonify
from pymongo import MongoClient
import os

# --- Configuration ---
# Crée notre application "cerveau"
app = Flask(__name__)

# Connecte-toi à ta base de données MongoDB.
# C'est plus sécurisé de mettre le lien dans les "Secrets" de Render.
# Pour l'instant, tu peux le coller directement pour tester.
MONGO_URI = "mongodb+srv://StrexBot:Ethan2009_M@cluster0.vmdicn2.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client.get_database("NomDeTaDB") # Ex: "strexbot_db"
collection = db.get_collection("users") # La collection qui stockera les utilisateurs

# --- Logique de l'API ---

# On va créer une route pour obtenir le solde
# Exemple d'URL : https://ton-api.onrender.com/api/balance/1234567890
@app.route('/api/balance/<user_id>')
def get_balance(user_id):
    # Cherche l'utilisateur dans la collection par son ID
    user_data = collection.find_one({"user_id": user_id})

    if user_data:
        # Si on trouve l'utilisateur, on renvoie ses pièces
        response = {
            "user_id": user_data["user_id"],
            "coins": user_data.get("coins", 0) # Utilise .get() pour éviter les erreurs si le champ n'existe pas
        }
    else:
        # Si on ne le trouve pas, on renvoie un solde de 0
        response = {
            "user_id": user_id,
            "coins": 0
        }
        
    return jsonify(response)

# Une route pour ajouter un utilisateur pour nos tests
# Exemple : https://ton-api.onrender.com/api/add_user/1234567890/500
@app.route('/api/add_user/<user_id>/<int:coins>')
def add_user(user_id, coins):
    # Vérifie si l'utilisateur existe déjà
    existing_user = collection.find_one({"user_id": user_id})
    if existing_user:
        # S'il existe, on met à jour son solde
        collection.update_one({"user_id": user_id}, {"$set": {"coins": coins}})
        return jsonify({"status": "updated", "user_id": user_id, "new_coins": coins})
    else:
        # Sinon, on le crée
        collection.insert_one({"user_id": user_id, "coins": coins})
        return jsonify({"status": "created", "user_id": user_id, "coins": coins})


# Cette partie est nécessaire pour le déploiement sur Render
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
