from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import exc

app = Flask(__name__)
import os
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class UserHistory(db.Model):
    __tablename__ = 'user_history'
    transaction_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id_sold = db.Column(db.Integer, nullable=False)
    user_id_bought = db.Column(db.Integer, nullable=False)

@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    data = request.json
    user_id_sold = data.get('user_id_sold')
    user_id_bought = data.get('user_id_bought')

    new_transaction = UserHistory(user_id_sold=user_id_sold, user_id_bought=user_id_bought)

    try:
        db.session.add(new_transaction)
        db.session.commit()
        return jsonify({"message": "Transaction added successfully"}), 201
    except exc.IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Transaction ID already exists"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/user_transactions/<int:user_id>', methods=['GET'])
def get_user_transactions(user_id):
    user_transactions = UserHistory.query.filter((UserHistory.user_id_sold == user_id) | (UserHistory.user_id_bought == user_id)).all()
    transactions = []
    for transaction in user_transactions:
        transaction_data = {
            'transaction_id': transaction.transaction_id,
            'user_id_sold': transaction.user_id_sold,
            'user_id_bought': transaction.user_id_bought
        }
        if transaction.user_id_sold == user_id:
            transaction_data['action'] = 'Sold'
        else:
            transaction_data['action'] = 'Bought'
        transactions.append(transaction_data)
    return jsonify({"transactions": transactions}), 200

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
