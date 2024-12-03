from flask import Flask, render_template, redirect, url_for, request, flash, send_from_directory
from flask_mysqldb import MySQL
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)

# Definindo a chave secreta para Flask
app.secret_key = 'chave_secreta_unica'

# Configuração do banco de dados
app.config['MYSQL_HOST'] = 'database-pet.c76wimciqfdz.us-east-2.rds.amazonaws.com'
app.config['MYSQL_USER'] = 'admin'
app.config['MYSQL_PASSWORD'] = 'univesp2513'
app.config['MYSQL_DB'] = 'petdb'

# Configuração do diretório de uploads
UPLOAD_FOLDER = r'C:\Users\lucas\Desktop\PDI_II_2024\static'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

mysql = MySQL(app)

# Configuração do Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Classe de usuário
class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM usuarios WHERE id = %s", (user_id,))
    user = cur.fetchone()
    if user:
        return User(user[0], user[1])
    return None

# Função para verificar se o arquivo é permitido
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Rota para servir arquivos estáticos
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Rota de login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        print(f"Tentativa de login com usuário: {username}, senha: {password}")

        try:
            cur = mysql.connection.cursor()
            cur.execute("SELECT * FROM usuarios WHERE username = %s", (username,))
            user = cur.fetchone()
            print(f"Usuário encontrado no banco de dados: {user}")

            if user and user[2] == password:  # Comparação direta da senha
                user_obj = User(user[0], user[1])
                login_user(user_obj)
                print("Login bem-sucedido")
                return redirect(url_for('index'))
            else:
                print("Credenciais inválidas")
                flash('Credenciais inválidas', 'danger')
        except Exception as e:
            print(f"Erro ao buscar usuário no banco de dados: {e}")

    return render_template('login.html')

# Rota para logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Página inicial
@app.route('/')
@login_required
def index():
    return render_template('index.html')

# Cadastro de animais
@app.route('/cadastro', methods=['GET', 'POST'])
@login_required
def cadastro():
    if request.method == 'POST':
        nome = request.form['nome']
        raca = request.form['raca']
        idade = request.form['idade']
        descricao = request.form['descricao']
        vacinacao = request.form['vacinacao']
        peso = request.form ['peso']
        data_chegada = request.form ['data_chegada']
        sexo = request.form ['sexo']
        especie = request.form ['especie']
        foto = request.files['foto']

        if foto and allowed_file(foto.filename):
            filename = secure_filename(foto.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            foto.save(file_path)
            foto_url = url_for('uploaded_file', filename=filename)  # URL db

            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO animais (nome, raca, idade, descricao, vacinacao, peso, data_chegada, sexo, especie, foto_url, user_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                        (nome, raca, idade, descricao, vacinacao, peso, data_chegada, sexo, especie, foto_url, current_user.id))
            mysql.connection.commit()

            flash('Animal cadastrado com sucesso!', 'success')
            return redirect(url_for('animais'))

    return render_template('cadastro.html')

# Exibição dos animais cadastrados
@app.route('/animais')
@login_required
def animais():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM animais WHERE user_id = %s", (current_user.id,))
    animais = cur.fetchall()
    return render_template('animais.html', animais=animais)

# Edição de animais
@app.route('/editar/<int:animal_id>', methods=['GET', 'POST'])
@login_required
def editar(animal_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM animais WHERE id = %s AND user_id = %s", (animal_id, current_user.id))
    animal = cur.fetchone()
    
    if request.method == 'POST':
        nome = request.form['nome']
        raca = request.form['raca']
        idade = request.form['idade']
        descricao = request.form['descricao']
        vacinacao = request.form['vacinacao']
        peso = request.form ['peso']
        data_chegada = request.form ['data_chegada']
        sexo = request.form ['sexo']
        especie = request.form ['especie']
        foto = request.files['foto']

        if foto and allowed_file(foto.filename):
            filename = secure_filename(foto.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            foto.save(file_path)
            foto_url = url_for('uploaded_file', filename=filename)
        else:
            foto_url = animal[6]

        cur.execute("UPDATE animais SET nome = %s, raca = %s, idade = %s, descricao = %s, vacinacao = %s, peso = %s, data_chegada = %s, sexo = %s, especie = %s, foto_url = %s WHERE id = %s AND user_id = %s",
                    (nome, raca, idade, descricao, vacinacao, peso, data_chegada, sexo, especie, foto_url, animal_id, current_user.id))
        mysql.connection.commit()

        flash('Animal atualizado com sucesso!', 'success')
        return redirect(url_for('animais'))

    return render_template('editar.html', animal=animal)

# Excluir animal
@app.route('/excluir/<int:animal_id>', methods=['POST'])
@login_required
def excluir(animal_id):
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM animais WHERE id = %s AND user_id = %s", (animal_id, current_user.id))
    mysql.connection.commit()

    flash('Animal excluído com sucesso!', 'success')
    return redirect(url_for('animais'))

if __name__ == '__main__':
    app.run(debug=True)
