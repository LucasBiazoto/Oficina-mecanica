from flask import Flask, jsonify, request, session, render_template
from flask_cors import CORS
import sqlite3

app = Flask(__name__, template_folder='.')
app.secret_key = 'oficina_vadao_secret_key_2026'
CORS(app, supports_credentials=True)

ADMIN_USER = "vadao"
ADMIN_PASS = "10203040"

def init_db():
    conn = sqlite3.connect('oficina.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ordens_servico (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            osNumero TEXT,
            clienteNome TEXT,
            clienteFone TEXT,
            clienteEndereco TEXT,
            veiculoMarca TEXT,
            veiculoPlaca TEXT,
            veiculoAno TEXT,
            veiculoCor TEXT,
            veiculoKm TEXT,
            dataEntrada TEXT,
            dataEntrega TEXT,
            maoDeObra REAL,
            totalGeral REAL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS itens_os (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            os_id INTEGER,
            descricao TEXT,
            preco REAL,
            FOREIGN KEY(os_id) REFERENCES ordens_servico(id)
        )
    ''')
    conn.commit()
    conn.close()

# Rota principal para carregar o sistema direto pelo servidor
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/login', methods=['POST'])
def login():
    dados = request.json
    usuario = dados.get('usuario')
    senha = dados.get('senha')
    
    if usuario == ADMIN_USER and senha == ADMIN_PASS:
        session['logado'] = True
        return jsonify({'sucesso': True, 'mensagem': 'Login efetuado com sucesso!'})
    else:
        return jsonify({'sucesso': False, 'erro': 'Usuário ou senha incorretos!'}), 401

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'sucesso': True})

@app.route('/api/verificar-sessao', methods=['GET'])
def verificar_sessao():
    if session.get('logado'):
        return jsonify({'logado': True})
    return jsonify({'logado': False}), 401

@app.route('/api/os/proximo-numero', methods=['GET'])
def proximo_numero():
    if not session.get('logado'):
        return jsonify({'erro': 'Não autorizado'}), 401
    
    conn = sqlite3.connect('oficina.db')
    cursor = conn.cursor()
    cursor.execute('SELECT MAX(id) FROM ordens_servico')
    row = cursor.fetchone()
    conn.close()
    proximo = (row[0] or 0) + 1
    return jsonify({'proximo_numero': f"{proximo:04d}"})

@app.route('/api/os', methods=['POST'])
def salvar_os():
    if not session.get('logado'):
        return jsonify({'erro': 'Não autorizado'}), 401
        
    dados = request.json
    try:
        conn = sqlite3.connect('oficina.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO ordens_servico (osNumero, clienteNome, clienteFone, clienteEndereco, veiculoMarca, veiculoPlaca, veiculoAno, veiculoCor, veiculoKm, dataEntrada, dataEntrega, maoDeObra, totalGeral)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            dados.get('osNumero'), dados.get('clienteNome'), dados.get('clienteFone'), 
            dados.get('clienteEndereco'), dados.get('veiculoMarca'), dados.get('veiculoPlaca'), 
            dados.get('veiculoAno'), dados.get('veiculoCor'), dados.get('veiculoKm'), 
            dados.get('dataEntrada'), dados.get('dataEntrega'), dados.get('maoDeObra'), dados.get('totalGeral')
        ))
        os_id = cursor.lastrowid
        
        for item in dados.get('itens', []):
            cursor.execute('''
                INSERT INTO itens_os (os_id, descricao, preco)
                VALUES (?, ?, ?)
            ''', (os_id, item.get('desc'), item.get('preco')))
            
        conn.commit()
        conn.close()
        return jsonify({'sucesso': True, 'os_numero': dados.get('osNumero')})
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@app.route('/api/os/consultar', methods=['GET'])
def consultar_os():
    if not session.get('logado'):
        return jsonify({'erro': 'Não autorizado'}), 401
        
    termo = request.args.get('termo', '')
    conn = sqlite3.connect('oficina.db')
    cursor = conn.cursor()
    
    query = '''
        SELECT id, osNumero, clienteNome, clienteFone, clienteEndereco, veiculoMarca, veiculoPlaca, veiculoAno, veiculoCor, veiculoKm, dataEntrada, dataEntrega, maoDeObra, totalGeral
        FROM ordens_servico
        WHERE osNumero LIKE ? OR clienteNome LIKE ? OR clienteFone LIKE ? OR veiculoPlaca LIKE ? OR dataEntrada LIKE ?
        ORDER BY id DESC
    '''
    like_termo = f"%{termo}%"
    cursor.execute(query, (like_termo, like_termo, like_termo, like_termo, like_termo))
    rows = cursor.fetchall()
    
    lista = []
    for r in rows:
        os_id = r[0]
        cursor.execute('SELECT descricao, preco FROM itens_os WHERE os_id = ?', (os_id,))
        itens_rows = cursor.fetchall()
        itens = [{'desc': i[0], 'preco': i[1]} for i in itens_rows]
        
        lista.append({
            'id': r[0], 'osNumero': r[1], 'clienteNome': r[2], 'clienteFone': r[3],
            'clienteEndereco': r[4], 'veiculoMarca': r[5], 'veiculoPlaca': r[6],
            'veiculoAno': r[7], 'veiculoCor': r[8], 'veiculoKm': r[9],
            'dataEntrada': r[10], 'dataEntrega': r[11], 'maoDeObra': r[12],
            'totalGeral': r[13], 'itens': itens
        })
        
    conn.close()
    return jsonify(lista)

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)