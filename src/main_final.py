from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import sqlite3
from datetime import datetime
import json

app = Flask(__name__)
CORS(app)

# Configuração do banco de dados
DATABASE = '/tmp/estoque.db'

def init_db():
    """Inicializa o banco de dados"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Tabela de produtos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT UNIQUE NOT NULL,
            nome TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabela de contagens
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contagens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produto_id INTEGER NOT NULL,
            lote TEXT NOT NULL,
            validade_mes INTEGER NOT NULL,
            validade_ano INTEGER NOT NULL,
            quantidade INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (produto_id) REFERENCES produtos (id),
            UNIQUE(produto_id, lote)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Banco de dados inicializado!")

def format_codigo(codigo):
    """Formata código para 4 dígitos"""
    try:
        num = int(codigo)
        if num < 0 or num > 9999:
            raise ValueError("Código deve estar entre 0 e 9999")
        return f"{num:04d}"
    except ValueError:
        raise ValueError("Código deve ser numérico")

# Rotas da API
@app.route('/api/produtos', methods=['GET'])
def listar_produtos():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM produtos ORDER BY codigo')
    produtos = cursor.fetchall()
    conn.close()
    
    return jsonify({
        'success': True,
        'produtos': [
            {
                'id': p[0],
                'codigo': p[1],
                'nome': p[2],
                'created_at': p[3]
            } for p in produtos
        ]
    })

@app.route('/api/produtos', methods=['POST'])
def criar_produto():
    data = request.get_json()
    
    try:
        codigo = format_codigo(data['codigo'])
        nome = data['nome'].strip()
        
        if not nome:
            raise ValueError("Nome é obrigatório")
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO produtos (codigo, nome) VALUES (?, ?)', (codigo, nome))
        conn.commit()
        produto_id = cursor.lastrowid
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Produto criado com sucesso',
            'produto': {
                'id': produto_id,
                'codigo': codigo,
                'nome': nome
            }
        }), 201
        
    except sqlite3.IntegrityError:
        return jsonify({
            'success': False,
            'message': 'Código já existe'
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400

@app.route('/api/produtos/<codigo>', methods=['GET'])
def buscar_produto(codigo):
    try:
        codigo_formatado = format_codigo(codigo)
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM produtos WHERE codigo = ?', (codigo_formatado,))
        produto = cursor.fetchone()
        conn.close()
        
        if not produto:
            return jsonify({
                'success': False,
                'message': 'Produto não encontrado'
            }), 404
        
        return jsonify({
            'success': True,
            'produto': {
                'id': produto[0],
                'codigo': produto[1],
                'nome': produto[2],
                'created_at': produto[3]
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400

@app.route('/api/contagens', methods=['POST'])
def registrar_contagem():
    data = request.get_json()
    
    try:
        codigo = format_codigo(data['codigo_produto'])
        lote = data['lote'].strip()
        validade_mes = int(data['validade_mes'])
        validade_ano = int(data['validade_ano'])
        quantidade = int(data['quantidade'])
        
        # Validações
        if not lote:
            raise ValueError("Lote é obrigatório")
        if validade_mes < 1 or validade_mes > 12:
            raise ValueError("Mês deve estar entre 1 e 12")
        if validade_ano < 2000 or validade_ano > 2099:
            raise ValueError("Ano deve estar entre 2000 e 2099")
        if quantidade < 0:
            raise ValueError("Quantidade não pode ser negativa")
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Buscar produto
        cursor.execute('SELECT id FROM produtos WHERE codigo = ?', (codigo,))
        produto = cursor.fetchone()
        if not produto:
            conn.close()
            return jsonify({
                'success': False,
                'message': 'Produto não encontrado'
            }), 404
        
        produto_id = produto[0]
        
        # Verificar se lote já existe
        cursor.execute('SELECT quantidade FROM contagens WHERE produto_id = ? AND lote = ?', 
                      (produto_id, lote))
        contagem_existente = cursor.fetchone()
        
        if contagem_existente:
            # Somar quantidade
            nova_quantidade = contagem_existente[0] + quantidade
            cursor.execute('UPDATE contagens SET quantidade = ? WHERE produto_id = ? AND lote = ?',
                          (nova_quantidade, produto_id, lote))
            criou_novo = False
        else:
            # Criar nova contagem
            cursor.execute('''INSERT INTO contagens 
                             (produto_id, lote, validade_mes, validade_ano, quantidade) 
                             VALUES (?, ?, ?, ?, ?)''',
                          (produto_id, lote, validade_mes, validade_ano, quantidade))
            criou_novo = True
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Contagem registrada com sucesso',
            'criou_novo': criou_novo
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400

@app.route('/api/contagens/produto/<codigo>', methods=['GET'])
def listar_contagens_produto(codigo):
    try:
        codigo_formatado = format_codigo(codigo)
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT c.*, p.codigo, p.nome 
            FROM contagens c 
            JOIN produtos p ON c.produto_id = p.id 
            WHERE p.codigo = ? 
            ORDER BY c.lote
        ''', (codigo_formatado,))
        contagens = cursor.fetchall()
        conn.close()
        
        return jsonify({
            'success': True,
            'contagens': [
                {
                    'id': c[0],
                    'lote': c[2],
                    'validade_mes': c[3],
                    'validade_ano': c[4],
                    'quantidade': c[5],
                    'validade_formatada': f"{c[3]:02d}/{c[4]}",
                    'produto_codigo': c[7],
                    'produto_nome': c[8]
                } for c in contagens
            ]
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400

@app.route('/api/relatorio/resumo', methods=['GET'])
def resumo_estoque():
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Buscar todos os produtos com suas contagens
        cursor.execute('''
            SELECT p.id, p.codigo, p.nome,
                   c.id as contagem_id, c.lote, c.validade_mes, c.validade_ano, c.quantidade
            FROM produtos p
            LEFT JOIN contagens c ON p.id = c.produto_id
            ORDER BY p.codigo, c.lote
        ''')
        
        dados = cursor.fetchall()
        conn.close()
        
        # Organizar dados
        produtos_dict = {}
        total_geral = 0
        
        for row in dados:
            produto_id, codigo, nome = row[0], row[1], row[2]
            contagem_id, lote, val_mes, val_ano, quantidade = row[3], row[4], row[5], row[6], row[7]
            
            if produto_id not in produtos_dict:
                produtos_dict[produto_id] = {
                    'produto': {'id': produto_id, 'codigo': codigo, 'nome': nome},
                    'contagens': [],
                    'total_quantidade': 0
                }
            
            if contagem_id:  # Se tem contagem
                contagem = {
                    'id': contagem_id,
                    'lote': lote,
                    'validade_mes': val_mes,
                    'validade_ano': val_ano,
                    'quantidade': quantidade,
                    'validade_formatada': f"{val_mes:02d}/{val_ano}"
                }
                produtos_dict[produto_id]['contagens'].append(contagem)
                produtos_dict[produto_id]['total_quantidade'] += quantidade
                total_geral += quantidade
        
        resumo = list(produtos_dict.values())
        
        return jsonify({
            'success': True,
            'resumo': resumo,
            'total_geral': total_geral,
            'total_produtos': len(resumo)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# Servir arquivos estáticos
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_static(path):
    if path == '' or path == 'index.html':
        return send_from_directory('static', 'index.html')
    
    try:
        return send_from_directory('static', path)
    except:
        return send_from_directory('static', 'index.html')

if __name__ == '__main__':
    init_db()
    print("🚀 Sistema de Estoque iniciado!")
    print("📍 Acesse: http://localhost:5005")
    app.run(host='0.0.0.0', port=5005, debug=False)

