from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.secret_key = "secreta" 

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''  # Substituir
app.config['MYSQL_DB'] = 'banco_flask'

mysql = MySQL(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' 

class User(UserMixin):
    def __init__(self, id, nome, email):
        self.id = id
        self.nome = nome
        self.email = email


@login_manager.user_loader
def load_user(user_id):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE id = %s", (user_id,))
    user_data = cursor.fetchone()
    cursor.close()
    if user_data:
        return User(user_data[0], user_data[1], user_data[2])
    return None

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
        user_data = cursor.fetchone()
        cursor.close()

        if user_data and check_password_hash(user_data[3], senha):  
            user = User(user_data[0], user_data[1], user_data[2])
            login_user(user)
            session['user_id'] = user.id 
            flash("Login bem-sucedido!", "success")
            return redirect(url_for('index')) 
        else:
            flash("Usuário ou senha incorretos", "danger")
    
    return render_template('login.html')

@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == 'POST':
        return redirect(url_for('logout'))
    return render_template('index.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.pop('user_id', None) 
    flash("Você saiu com sucesso.", "success")
    return redirect(url_for('login')) 

@app.route('/criar_usuario', methods=['GET', 'POST'])
def criar_usuario():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']

        hashed_password = generate_password_hash(senha, method='pbkdf2:sha256')

        cursor = mysql.connection.cursor()
        try:
            cursor.execute("INSERT INTO usuarios (nome, email, senha) VALUES (%s, %s, %s)", (nome, email, hashed_password))
            mysql.connection.commit()
            flash("Usuário criado com sucesso!", "success")
        except Exception as e:
            flash(f"Erro ao criar usuário: {str(e)}", "danger")
        finally:
            cursor.close()
        return redirect(url_for('login'))  
    return render_template('criar_usuario.html')


if __name__ == '__main__':
    app.run(debug=True)