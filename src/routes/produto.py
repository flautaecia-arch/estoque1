from flask import Blueprint, request, jsonify
from src.database import db
from src.models.produto import Produto
from src.models.contagem import Contagem
import pandas as pd
from werkzeug.utils import secure_filename
import os
import tempfile

produto_bp = Blueprint('produto', __name__)

@produto_bp.route('/produtos', methods=['GET'])
def listar_produtos():
    """Lista todos os produtos ordenados por código"""
    try:
        produtos = Produto.query.order_by(Produto.codigo).all()
        return jsonify({
            'success': True,
            'produtos': [produto.to_dict() for produto in produtos]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao listar produtos: {str(e)}'
        }), 500

@produto_bp.route('/produtos', methods=['POST'])
def criar_produto():
    """Cria um novo produto"""
    try:
        data = request.get_json()
        
        if not data or 'codigo' not in data or 'nome' not in data:
            return jsonify({
                'success': False,
                'message': 'Código e nome são obrigatórios'
            }), 400
        
        # Validar código
        valido, resultado = Produto.validar_codigo(data['codigo'])
        if not valido:
            return jsonify({
                'success': False,
                'message': resultado
            }), 400
        
        codigo_formatado = resultado
        
        # Verificar se já existe
        produto_existente = Produto.query.filter_by(codigo=codigo_formatado).first()
        if produto_existente:
            return jsonify({
                'success': False,
                'message': f'Produto com código {codigo_formatado} já existe'
            }), 400
        
        # Criar produto
        produto = Produto(codigo_formatado, data['nome'])
        db.session.add(produto)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Produto criado com sucesso',
            'produto': produto.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Erro ao criar produto: {str(e)}'
        }), 500

@produto_bp.route('/produtos/<codigo>', methods=['GET'])
def buscar_produto(codigo):
    """Busca um produto por código"""
    try:
        # Formatar código com zeros à esquerda
        codigo_formatado = str(codigo).zfill(4)
        
        produto = Produto.query.filter_by(codigo=codigo_formatado).first()
        if not produto:
            return jsonify({
                'success': False,
                'message': f'Produto com código {codigo_formatado} não encontrado'
            }), 404
        
        return jsonify({
            'success': True,
            'produto': produto.to_dict()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao buscar produto: {str(e)}'
        }), 500

@produto_bp.route('/produtos/<int:produto_id>', methods=['PUT'])
def atualizar_produto(produto_id):
    """Atualiza um produto"""
    try:
        produto = Produto.query.get(produto_id)
        if not produto:
            return jsonify({
                'success': False,
                'message': 'Produto não encontrado'
            }), 404
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'Dados não fornecidos'
            }), 400
        
        # Atualizar nome se fornecido
        if 'nome' in data:
            produto.nome = data['nome'].strip().upper()
        
        # Atualizar código se fornecido
        if 'codigo' in data:
            valido, resultado = Produto.validar_codigo(data['codigo'])
            if not valido:
                return jsonify({
                    'success': False,
                    'message': resultado
                }), 400
            
            codigo_formatado = resultado
            
            # Verificar se o novo código já existe (exceto o próprio produto)
            produto_existente = Produto.query.filter(
                Produto.codigo == codigo_formatado,
                Produto.id != produto_id
            ).first()
            
            if produto_existente:
                return jsonify({
                    'success': False,
                    'message': f'Produto com código {codigo_formatado} já existe'
                }), 400
            
            produto.codigo = codigo_formatado
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Produto atualizado com sucesso',
            'produto': produto.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Erro ao atualizar produto: {str(e)}'
        }), 500

@produto_bp.route('/produtos/<int:produto_id>', methods=['DELETE'])
def excluir_produto(produto_id):
    """Exclui um produto e todas suas contagens"""
    try:
        produto = Produto.query.get(produto_id)
        if not produto:
            return jsonify({
                'success': False,
                'message': 'Produto não encontrado'
            }), 404
        
        # As contagens serão excluídas automaticamente devido ao cascade
        db.session.delete(produto)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Produto excluído com sucesso'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Erro ao excluir produto: {str(e)}'
        }), 500

@produto_bp.route('/produtos/importar', methods=['POST'])
def importar_produtos():
    """Importa produtos de um arquivo XLSX"""
    try:
        if 'arquivo' not in request.files:
            return jsonify({
                'success': False,
                'message': 'Nenhum arquivo enviado'
            }), 400
        
        arquivo = request.files['arquivo']
        if arquivo.filename == '':
            return jsonify({
                'success': False,
                'message': 'Nenhum arquivo selecionado'
            }), 400
        
        if not arquivo.filename.lower().endswith(('.xlsx', '.xls')):
            return jsonify({
                'success': False,
                'message': 'Arquivo deve ser .xlsx ou .xls'
            }), 400
        
        # Salvar arquivo temporariamente
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as temp_file:
            arquivo.save(temp_file.name)
            
            # Ler arquivo Excel
            df = pd.read_excel(temp_file.name)
            
            # Remover arquivo temporário
            os.unlink(temp_file.name)
        
        if df.empty:
            return jsonify({
                'success': False,
                'message': 'Arquivo está vazio'
            }), 400
        
        # Detectar colunas automaticamente
        colunas = df.columns.tolist()
        col_codigo = None
        col_nome = None
        
        # Procurar por nomes de colunas conhecidos
        for col in colunas:
            col_lower = str(col).lower()
            if 'codigo' in col_lower or 'código' in col_lower:
                col_codigo = col
            elif 'nome' in col_lower or 'produto' in col_lower or 'descricao' in col_lower or 'descrição' in col_lower:
                col_nome = col
        
        # Se não encontrou, usar as duas primeiras colunas
        if col_codigo is None or col_nome is None:
            if len(colunas) >= 2:
                col_codigo = colunas[0]
                col_nome = colunas[1]
            else:
                return jsonify({
                    'success': False,
                    'message': 'Arquivo deve ter pelo menos 2 colunas (código e nome)'
                }), 400
        
        # Processar dados
        produtos_criados = 0
        produtos_atualizados = 0
        erros = []
        
        for index, row in df.iterrows():
            try:
                codigo_raw = row[col_codigo]
                nome_raw = row[col_nome]
                
                # Pular linhas vazias
                if pd.isna(codigo_raw) or pd.isna(nome_raw):
                    continue
                
                # Validar código
                valido, resultado = Produto.validar_codigo(codigo_raw)
                if not valido:
                    erros.append(f'Linha {index + 2}: {resultado}')
                    continue
                
                codigo_formatado = resultado
                nome = str(nome_raw).strip().upper()
                
                if not nome:
                    erros.append(f'Linha {index + 2}: Nome não pode estar vazio')
                    continue
                
                # Verificar se produto já existe
                produto_existente = Produto.query.filter_by(codigo=codigo_formatado).first()
                
                if produto_existente:
                    # Atualizar nome se diferente
                    if produto_existente.nome != nome:
                        produto_existente.nome = nome
                        produtos_atualizados += 1
                else:
                    # Criar novo produto
                    produto = Produto(codigo_formatado, nome)
                    db.session.add(produto)
                    produtos_criados += 1
                    
            except Exception as e:
                erros.append(f'Linha {index + 2}: {str(e)}')
        
        # Salvar alterações
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Importação concluída: {produtos_criados} criados, {produtos_atualizados} atualizados',
            'detalhes': {
                'produtos_criados': produtos_criados,
                'produtos_atualizados': produtos_atualizados,
                'erros': erros,
                'total_erros': len(erros)
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Erro ao importar produtos: {str(e)}'
        }), 500

@produto_bp.route('/produtos/template', methods=['GET'])
def baixar_template():
    """Retorna um template Excel para importação de produtos"""
    try:
        # Criar DataFrame com template
        template_data = {
            'codigo': ['1', '2', '3'],
            'nome': ['PRODUTO EXEMPLO 1', 'PRODUTO EXEMPLO 2', 'PRODUTO EXEMPLO 3']
        }
        
        df = pd.DataFrame(template_data)
        
        # Criar arquivo temporário
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as temp_file:
            df.to_excel(temp_file.name, index=False)
            
            # Ler arquivo para retornar
            with open(temp_file.name, 'rb') as f:
                arquivo_bytes = f.read()
            
            # Remover arquivo temporário
            os.unlink(temp_file.name)
        
        from flask import Response
        return Response(
            arquivo_bytes,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={'Content-Disposition': 'attachment; filename=template_produtos.xlsx'}
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao gerar template: {str(e)}'
        }), 500

