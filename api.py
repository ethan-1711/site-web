# api.py
from flask import Flask, jsonify

# Crée notre application "cerveau"
app = Flask(__name__)

# On définit une "route" ou une "URL" que notre site pourra appeler
# Par exemple : https://mon-api.onrender.com/api/balance/testuser123
@app.route('/api/balance/<user_id>')
def get_balance(user_id):
    # Pour l'instant, on ne se connecte pas à une base de données.
    # On simule la réponse pour voir si ça marche.
    
    # On fait semblant de chercher l'utilisateur et on renvoie son solde.
    fake_user_data = {
        "username": user_id,
        "coins": 500  # Un solde fixe pour le test
    }
    
    # On renvoie les données au format JSON, le langage que les API utilisent pour parler.
    return jsonify(fake_user_data)

# Cette partie est nécessaire pour le déploiement sur Render
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
