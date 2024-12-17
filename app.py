from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import random
app = Flask(__name__)
app.secret_key = "secreta" 

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Noelia18.A' 
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

@app.route('/', methods=['GET', 'POST'])
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

@app.route('/index', methods=['GET', 'POST'])
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
        nif= request.form['nif']
        iban = gerar_iban()  
        hashed_password = generate_password_hash(senha, method='pbkdf2:sha256')

        cursor = mysql.connection.cursor()
        try:
            cursor.execute("INSERT INTO usuarios (nome, email, senha, nif) VALUES (%s, %s, %s, %s)", (nome, email, hashed_password, nif))
            mysql.connection.commit()

            id_usuario = cursor.lastrowid

            nome_conta = f"Conta {nome}" 
            cursor.execute("INSERT INTO contas (id_usuario, nome_conta, saldo,iban) VALUES (%s, %s, %s, %s)", (id_usuario, nome_conta, 0.00, iban))
            mysql.connection.commit()

            flash("Usuário e conta criados com sucesso!", "success")
        except Exception as e:
            flash(f"Erro ao criar usuário e conta: {str(e)}", "danger")
        finally:
            cursor.close()
        return redirect(url_for('login'))

    return render_template('criar_usuario.html')

@app.route('/criar_conta', methods=['GET', 'POST'])
@login_required
def criar_conta():
    if request.method == 'POST':
        nome_conta = request.form.get('nome')  
        montante = request.form.get('montante')  

        # Validação do montante
        try:
            montante = float(montante)
        except ValueError:
            flash("Valor inválido para o montante.", "danger")
            return redirect(url_for('criar_conta'))
        
        # Geração automática do IBAN
        iban = gerar_iban()

        print(f"Dados recebidos: ID Usuário: {current_user.id}, Nome: {nome_conta}, Montante: {montante}, IBAN: {iban}")

        cursor = mysql.connection.cursor()
        try:
            print("Executando SQL de inserção...")
            cursor.execute(
                "INSERT INTO contas (id_usuario, nome_conta, saldo, iban) VALUES (%s, %s, %s, %s)",
                (current_user.id, nome_conta, montante, iban)
            )
            mysql.connection.commit()
            print("Conta criada com sucesso!")
            flash(f"Conta criada com sucesso! IBAN: {iban}", "success")
        except Exception as e:
            print(f"Erro ao executar SQL: {e}")
            flash(f"Erro ao criar conta: {str(e)}", "danger")
        finally:
            cursor.close()

        return redirect(url_for('index'))
    
    return render_template('criar_conta.html')

def gerar_iban():
    # Geração de IBAN simples para teste
    codigo_pais = "PT"
    digitos_controle = f"{random.randint(10, 99)}"
    numero_banco_conta = ''.join([str(random.randint(0, 9)) for _ in range(21)])
    return f"{codigo_pais}{digitos_controle}{numero_banco_conta}"


@app.route('/deposito', methods=['GET', 'POST'])
@login_required
def deposito():
    
    cursor = mysql.connection.cursor()
    try:
        cursor.execute("SELECT id_conta, nome_conta FROM contas WHERE id_usuario = %s", (current_user.id,))
        contas = cursor.fetchall()  
    except Exception as e:
        flash(f"Erro ao carregar as contas: {str(e)}", "danger")
        contas = []  
    finally:
        cursor.close()

    if request.method == 'POST':
        montante = request.form['montante']
        id_conta = request.form['id_conta_deposito']

        try:
            montante = float(montante)
            if montante <= 0:
                flash("O montante deve ser maior que zero!", "danger")
                return redirect(url_for('deposito'))
        except ValueError:
            flash("Por favor, insira um valor válido para o montante.", "danger")
            return redirect(url_for('deposito'))

        cursor = mysql.connection.cursor()
        try:
            cursor.execute(
                "INSERT INTO depositos (id_conta_deposito, montante) VALUES (%s, %s)", 
                (id_conta, montante)
            )
            mysql.connection.commit()

            cursor.execute(
                "UPDATE contas SET saldo = saldo + %s WHERE id_conta = %s", 
                (montante, id_conta)
            )
            mysql.connection.commit()

            flash(f"Depósito de R${montante:.2f} realizado com sucesso!", "success")
        except Exception as e:
            flash(f"Erro ao realizar o depósito: {str(e)}", "danger")
        finally:
            cursor.close()

        return redirect(url_for('deposito'))  
    return render_template('deposito.html', contas=contas)


@app.route('/fazer_transferencia', methods=['GET', 'POST'])
@login_required
def fazer_transferencia():
    cursor = mysql.connection.cursor()
    try:
        # Buscar todas as contas no banco de dados (não apenas do usuário atual)
        cursor.execute("SELECT id_conta, nome_conta, id_usuario FROM contas")
        contas = cursor.fetchall()
    except Exception as e:
        flash(f"Erro ao carregar contas: {str(e)}", "danger")
        contas = []
    finally:
        cursor.close()

    if request.method == 'POST':
        conta_origem = request.form.get('conta_origem')
        conta_destino = request.form.get('conta_destino')
        montante = request.form.get('montante')

        # Validar entrada
        if not conta_origem or not conta_destino or not montante:
            flash("Todos os campos são obrigatórios.", "danger")
            return redirect(url_for('fazer_transferencia'))
        
        if conta_origem == conta_destino:
            flash("A conta de origem e destino devem ser diferentes.", "danger")
            return redirect(url_for('fazer_transferencia'))

        try:
            montante = float(montante)
            if montante <= 0:
                flash("O montante deve ser maior que zero.", "danger")
                return redirect(url_for('fazer_transferencia'))
        except ValueError:
            flash("Insira um valor numérico válido para o montante.", "danger")
            return redirect(url_for('fazer_transferencia'))

        # Realizar a transferência
        cursor = mysql.connection.cursor()
        try:
            # Verificar saldo suficiente na conta de origem
            cursor.execute("SELECT saldo FROM contas WHERE id_conta = %s", (conta_origem,))
            saldo_origem = cursor.fetchone()
            if not saldo_origem or saldo_origem[0] < montante:
                flash("Saldo insuficiente para realizar a transferência.", "danger")
                return redirect(url_for('fazer_transferencia'))

            # Deduzir da conta de origem
            cursor.execute("UPDATE contas SET saldo = saldo - %s WHERE id_conta = %s", (montante, conta_origem))
            # Adicionar à conta de destino
            cursor.execute("UPDATE contas SET saldo = saldo + %s WHERE id_conta = %s", (montante, conta_destino))

            # Registrar a transação
            cursor.execute("""
                INSERT INTO transacoes (id_conta_origem, id_conta_destino, valor) 
                VALUES (%s, %s, %s)
            """, (conta_origem, conta_destino, montante))

            mysql.connection.commit()
            flash("Transferência realizada com sucesso!", "success")
        except Exception as e:
            mysql.connection.rollback()
            flash(f"Erro ao realizar transferência: {str(e)}", "danger")
        finally:
            cursor.close()
        return redirect(url_for('fazer_transferencia'))

    return render_template('transacao.html', contas=contas)

if __name__ == '__main__':
    app.run(debug=True)
