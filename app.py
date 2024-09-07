from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:802128@localhost/stock'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'khasjh212w@3jqke878@12323AHDn'

db = SQLAlchemy(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255))
    stocks = db.relationship('Stock', backref='owner', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Stock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    ticker = db.Column(db.String(10), nullable=False)
    price = db.Column(db.Float, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'ticker': self.ticker,
            'price': self.price
        }

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    if User.query.filter_by(username=data['username']).first():
        return jsonify({"msg": "Username already exists"}), 400
    user = User(username=data['username'])
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()
    return jsonify({"msg": "User created successfully"}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(username=data['username']).first()
    if user and user.check_password(data['password']):
        access_token = create_access_token(identity=user.id)
        return jsonify(access_token=access_token), 200
    return jsonify({"msg": "Bad username or password"}), 401

@app.route('/api/stocks', methods=['GET'])
@jwt_required()
def get_stocks():
    current_user_id = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    pagination = Stock.query.filter_by(user_id=current_user_id).paginate(page=page, per_page=per_page, error_out=False)
    
    stocks = pagination.items
    
    return jsonify({
        'stocks': [stock.to_dict() for stock in stocks],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })

@app.route('/api/stocks', methods=['POST'])
@jwt_required()
def add_stock():
    current_user_id = get_jwt_identity()
    data = request.json
    new_stock = Stock(name=data['name'], ticker=data['ticker'], price=data['price'], user_id=current_user_id)
    db.session.add(new_stock)
    db.session.commit()
    return jsonify(new_stock.to_dict()), 201

@app.route('/api/stocks/<int:id>', methods=['GET'])
@jwt_required()
def get_stock(id):
    current_user_id = get_jwt_identity()
    stock = Stock.query.filter_by(id=id, user_id=current_user_id).first_or_404()
    return jsonify(stock.to_dict())

@app.route('/api/stocks/<int:id>', methods=['PUT'])
@jwt_required()
def update_stock(id):
    current_user_id = get_jwt_identity()
    stock = Stock.query.filter_by(id=id, user_id=current_user_id).first_or_404()
    data = request.json
    stock.name = data['name']
    stock.ticker = data['ticker']
    stock.price = data['price']
    db.session.commit()
    return jsonify(stock.to_dict())

@app.route('/api/stocks/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_stock(id):
    current_user_id = get_jwt_identity()
    stock = Stock.query.filter_by(id=id, user_id=current_user_id).first_or_404()
    db.session.delete(stock)
    db.session.commit()
    return '', 204

if __name__ == '__main__':
    app.run(debug=True)