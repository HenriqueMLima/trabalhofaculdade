from flask import Flask, request, jsonify, session
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
import bcrypt

app = Flask(__name__)
app.secret_key = 'chave secreta'  

CORS(app)
CORS(app, resources={r"/*": {"origins": "http://127.0.0.1:5500"}})

# Configurações de conexão
db_config = {
    'host': 'mysql-d30b100-gustavocnc.d.aivencloud.com',
    'user': 'avnadmin',
    'password': 'AVNS_QqNp6z-f2Lk7STAgZLH',
    'database': 'projetofaculdade',
    'port': 17859
}

def create_connection():
    """Estabelece a conexão com o banco de dados e retorna a conexão."""
    try:
        connection = mysql.connector.connect(
            host=db_config['host'],
            user=db_config['user'],
            password=db_config['password'],
            database=db_config['database'],
            port=db_config['port']
        )
        if connection.is_connected():
            print("Conexão bem-sucedida ao MySQL!")
            return connection
    except Error as e:
        print(f"Erro ao conectar ao MySQL: {e}")
        return None

def check_password(stored_password, provided_password):
    """Verifica se a senha fornecida corresponde ao hash armazenado."""
    return bcrypt.checkpw(provided_password.encode('utf-8'), stored_password.encode('utf-8'))

@app.route('/login', methods=['POST'])
def login():
    user_data = request.get_json()
    
    if not user_data or 'email' not in user_data or 'senha' not in user_data:
        return jsonify({"message": "Email e senha são obrigatórios"}), 400
    
    email = user_data['email']
    senha = user_data['senha']
    
    try:
        connection = create_connection()
        if connection:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT * FROM Usuario WHERE Email = %s", (email,))
            user = cursor.fetchone()
            
            if user and bcrypt.checkpw(senha.encode('utf-8'), user['Senha'].encode('utf-8')):
                # Login bem-sucedido, salva informações na sessão
                session['user_id'] = user['ID']
                session['user_name'] = user['Nome']
                return jsonify({"message": "Login bem-sucedido!"}), 200
            else:
                return jsonify({"message": "Credenciais inválidas"}), 401
        else:
            return jsonify({"message": "Erro ao conectar ao banco de dados"}), 500
    except Error as e:
        print(f"Erro ao verificar credenciais: {e}")
        return jsonify({"message": f"Erro ao verificar credenciais: {str(e)}"}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/register', methods=['POST'])
def register():
    """Cadastra um novo usuário no sistema."""
    user_data = request.json
    
    # Validação de entrada
    if not user_data or not user_data.get('nome') or not user_data.get('email') or not user_data.get('senha'):
        return jsonify({"message": "Nome, email e senha são obrigatórios"}), 400
    
    nome = user_data['nome']
    email = user_data['email']
    senha = user_data['senha']
    
    # Hash da senha com bcrypt
    hashed_senha = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt())
    
    try:
        connection = create_connection()
        if connection:
            cursor = connection.cursor()
            
            # Verifica se o usuário já existe
            cursor.execute("SELECT * FROM Usuario WHERE Email = %s", (email,))
            user = cursor.fetchone()
            
            if user:
                return jsonify({"message": "Usuário já existe com esse email"}), 409
            
            # Insere o novo usuário no banco de dados
            insert_query = """
                INSERT INTO Usuario (Nome, Email, Senha) 
                VALUES (%s, %s, %s)
            """
            cursor.execute(insert_query, (nome, email, hashed_senha))
            connection.commit()
            
            return jsonify({"message": "Usuário cadastrado com sucesso!"}), 201
        else:
            return jsonify({"message": "Erro ao conectar ao banco de dados"}), 500
    except Error as e:
        print(f"Erro ao cadastrar usuário: {e}")
        return jsonify({"message": "Erro ao cadastrar usuário"}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            
@app.route('/artigos', methods=['POST'])
def cadastrar_artigo():
    # Verifica se o usuário está autenticado
    if 'user_id' not in session:
        return jsonify({"message": "Você precisa estar autenticado para cadastrar um artigo"}), 401
    
    artigo_data = request.json
    
    # Validação de entrada
    if not artigo_data or not artigo_data.get('titulo') or not artigo_data.get('conteudo') or not artigo_data.get('categoria'):
        return jsonify({"message": "Título, conteúdo e categoria são obrigatórios"}), 400
    
    titulo = artigo_data['titulo']
    conteudo = artigo_data['conteudo']
    categoria = artigo_data['categoria']
    user_id = session['user_id']  # Pega o ID do usuário logado da sessão

    try:
        connection = create_connection()
        if connection:
            cursor = connection.cursor()
            
            # Insere o novo artigo no banco de dados A
            insert_query = """
                INSERT INTO Artigos (Titulo, Conteudo, Categoria, Autor_ID, Data_Publicacao) 
                VALUES (%s, %s, %s, %s, NOW())
            """
            cursor.execute(insert_query, (titulo, conteudo, categoria, user_id))
            connection.commit()
            
            return jsonify({"message": "Artigo cadastrado com sucesso!"}), 201
        else:
            return jsonify({"message": "Erro ao conectar ao banco de dados"}), 500
    except Error as e:
        print(f"Erro ao cadastrar artigo: {e}")
        return jsonify({"message": "Erro ao cadastrar artigo"}), 500
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)