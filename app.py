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

def gerar_iban():
    codigo_pais = "PT"  
    numero_conta = ''.join([str(random.randint(0, 9)) for _ in range(19)]) 
    return f"{codigo_pais}{numero_conta}"

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
        nif = request.form['nif']
        
        # Gerar o IBAN para a conta do usuário
        iban = gerar_iban()

        # Verificar se o IBAN já existe no banco de dados
        cursor = mysql.connection.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM contas WHERE iban = %s", (iban,))
            result = cursor.fetchone()

            if result[0] > 0:  # Se o IBAN já existir, gere um novo IBAN
                iban = gerar_iban()
            
            # Hash da senha do usuário
            hashed_password = generate_password_hash(senha, method='pbkdf2:sha256')

            # Inserir o usuário na tabela de usuários
            cursor.execute("INSERT INTO usuarios (nome, email, senha, nif) VALUES (%s, %s, %s, %s)", (nome, email, hashed_password, nif))
            mysql.connection.commit()

            # Obter o ID do usuário recém-criado
            id_usuario = cursor.lastrowid

            # Criar uma conta com saldo inicial 0.00 e o IBAN gerado
            nome_conta = f"Conta {nome}"
            cursor.execute("INSERT INTO contas (id_usuario, nome_conta, saldo, iban) VALUES (%s, %s, %s, %s)", (id_usuario, nome_conta, 0.00, iban))
            mysql.connection.commit()

            flash("Usuário e conta criados com sucesso!", "success")
        except Exception as e:
            mysql.connection.rollback()  # Reverta qualquer alteração feita no banco até agora
            flash(f"Erro ao criar usuário e conta: {str(e)}", "danger")
        finally:
            cursor.close()

        return redirect(url_for('login'))

    return render_template('criar_usuario.html')

@app.route('/criar_conta', methods=['GET', 'POST'])
@login_required
def criar_conta():
    if request.method == 'POST':
        nome_conta = request.form.get('nome')  # Nome da nova conta
        montante = request.form.get('montante')  # Saldo inicial da nova conta

        # Validar o valor do montante
        try:
            montante = float(montante)
        except ValueError:
            flash("Valor inválido para o montante.", "danger")
            return redirect(url_for('criar_conta'))
        
        # Gerar IBAN para a nova conta
        iban = gerar_iban()

        cursor = mysql.connection.cursor()
        try:
            # Inserir nova conta no banco de dados
            cursor.execute(
                "INSERT INTO contas (id_usuario, nome_conta, saldo, iban) VALUES (%s, %s, %s, %s)",
                (current_user.id, nome_conta, montante, iban)
            )
            mysql.connection.commit()
            flash(f"Conta criada com sucesso! IBAN: {iban}", "success")
        except Exception as e:
            flash(f"Erro ao criar conta: {str(e)}", "danger")
        finally:
            cursor.close()

        return redirect(url_for('index'))
    
    return render_template('criar_conta.html')

@app.route('/fazer_transferencia', methods=['GET', 'POST'])
@login_required
def fazer_transferencia():
    if request.method == 'POST':
        valor = request.form['valor']
        iban_destino = request.form['iban_destino']
        id_conta_origem = request.form['id_conta_origem']

        try:
            valor = float(valor)

            if valor <= 0:
                flash("O valor da transferência deve ser maior que zero.", "danger")
                return redirect(url_for('fazer_transferencia'))

            cursor = mysql.connection.cursor()

            # Verifica o saldo da conta de origem
            cursor.execute("SELECT saldo FROM contas WHERE id_conta = %s", (id_conta_origem,))
            saldo_origem = cursor.fetchone()

            if saldo_origem is None or saldo_origem[0] < valor:
                flash("Saldo insuficiente para realizar a transferência.", "danger")
                cursor.close()
                return redirect(url_for('fazer_transferencia'))

            # Busca a conta de destino pelo IBAN fornecido
            cursor.execute("SELECT id_conta FROM contas WHERE iban = %s", (iban_destino,))
            conta_destino = cursor.fetchone()

            if conta_destino is None:
                flash("IBAN da conta de destino não encontrado.", "danger")
                cursor.close()
                return redirect(url_for('fazer_transferencia'))

            # Atualiza os saldos das contas de origem e destino
            cursor.execute(
                "UPDATE contas SET saldo = saldo - %s WHERE id_conta = %s",
                (valor, id_conta_origem)
            )
            cursor.execute(
                "UPDATE contas SET saldo = saldo + %s WHERE id_conta = %s",
                (valor, conta_destino[0])
            )

            # Registra a transação
            cursor.execute(
                "INSERT INTO transacoes (id_conta_origem, id_conta_destino, valor) VALUES (%s, %s, %s)",
                (id_conta_origem, conta_destino[0], valor)
            )

            mysql.connection.commit()
            cursor.close()

            flash("Transferência realizada com sucesso!", "success")
            return redirect(url_for('index'))

        except ValueError:
            flash("Valor inválido para a transferência.", "danger")
            return redirect(url_for('fazer_transferencia'))

    # Carregar as contas do usuário logado
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id_conta, nome_conta FROM contas WHERE id_usuario = %s", (current_user.id,))
    contas = cursor.fetchall()
    cursor.close()

    return render_template('transacao.html', contas=contas)



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

if __name__ == '__main__':
    app.run(debug=True)
