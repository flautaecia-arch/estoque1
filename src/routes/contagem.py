from flask import Blueprint, request, jsonify
from src.database import db
from src.models.produto import Produto
from src.models.contagem import Contagem
from sqlalchemy import func

contagem_bp = Blueprint('contagem', __name__)

@contagem_bp.route('/contagens', methods=['GET'])
def listar_contagens():
    """Lista todas as contagens ordenadas por código do produto"""
    try:
        contagens = db.session.query(Contagem, Produto).join(
            Produto, Contagem.produto_id == Produto.id
        ).order_by(Produto.codigo, Contagem.lote).all()
        
        resultado = []
        for contagem, produto in contagens:
            item = contagem.to_dict()
            item['produto'] = produto.to_dict()
            resultado.append(item)
        
        return jsonify({
            'success': True,
            'contagens': resultado
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao listar contagens: {str(e)}'
        }), 500

@contagem_bp.route('/contagens', methods=['POST'])
def registrar_contagem():
    """Registra uma nova contagem ou soma à quantidade existente se o lote já existir"""
    try:
        data = request.get_json()
        
        # Validar dados obrigatórios
        campos_obrigatorios = ['codigo_produto', 'lote', 'validade_mes', 'validade_ano', 'quantidade']
        for campo in campos_obrigatorios:
            if campo not in data:
                return jsonify({
                    'success': False,
                    'message': f'Campo {campo} é obrigatório'
                }), 400
        
        # Buscar produto por código
        codigo_formatado = str(data['codigo_produto']).zfill(4)
        produto = Produto.query.filter_by(codigo=codigo_formatado).first()
        
        if not produto:
            return jsonify({
                'success': False,
                'message': f'Produto com código {codigo_formatado} não encontrado'
            }), 404
        
        # Validar validade
        valido, resultado = Contagem.validar_validade(data['validade_mes'], data['validade_ano'])
        if not valido:
            return jsonify({
                'success': False,
                'message': resultado
            }), 400
        
        mes, ano = resultado
        
        # Validar quantidade
        try:
            quantidade = int(data['quantidade'])
            if quantidade < 0:
                return jsonify({
                    'success': False,
                    'message': 'Quantidade não pode ser negativa'
                }), 400
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Quantidade deve ser um número inteiro'
            }), 400
        
        # Adicionar ou somar contagem
        contagem, criou_novo = Contagem.adicionar_ou_somar(
            produto.id, 
            data['lote'], 
            mes, 
            ano, 
            quantidade
        )
        
        db.session.add(contagem)
        db.session.commit()
        
        if criou_novo:
            acao = 'criada'
            message = f'✅ Produto "{produto.nome}" (Código: {produto.codigo})\nLote: {contagem.lote}\nQuantidade adicionada: {quantidade}\nTotal no lote: {contagem.quantidade}'
        else:
            quantidade_anterior = contagem.quantidade - quantidade
            acao = 'atualizada (quantidade somada)'
            message = f'✅ Produto "{produto.nome}" (Código: {produto.codigo})\nLote: {contagem.lote}\nQuantidade adicionada: {quantidade}\nQuantidade anterior: {quantidade_anterior}\nNova quantidade total: {contagem.quantidade}'
        
        return jsonify({
            'success': True,
            'message': message,
            'contagem': contagem.to_dict(),
            'produto': produto.to_dict(),
            'criou_novo': criou_novo,
            'quantidade_adicionada': quantidade
        }), 201 if criou_novo else 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Erro ao registrar contagem: {str(e)}'
        }), 500

@contagem_bp.route('/contagens/produto/<codigo>', methods=['GET'])
def listar_contagens_produto(codigo):
    """Lista todas as contagens de um produto específico"""
    try:
        codigo_formatado = str(codigo).zfill(4)
        produto = Produto.query.filter_by(codigo=codigo_formatado).first()
        
        if not produto:
            return jsonify({
                'success': False,
                'message': f'Produto com código {codigo_formatado} não encontrado'
            }), 404
        
        contagens = Contagem.query.filter_by(produto_id=produto.id).order_by(Contagem.lote).all()
        
        return jsonify({
            'success': True,
            'produto': produto.to_dict(),
            'contagens': [contagem.to_dict() for contagem in contagens],
            'total_quantidade': sum(c.quantidade for c in contagens)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao listar contagens do produto: {str(e)}'
        }), 500

@contagem_bp.route('/contagens/<int:contagem_id>', methods=['GET', 'PUT', 'DELETE'])
def contagem_detail(contagem_id):
    """Obtém, altera ou exclui uma contagem específica"""
    contagem = Contagem.query.get(contagem_id)

    if not contagem:
        return jsonify({'success': False, 'message': 'Contagem não encontrada'}), 404

    if request.method == 'GET':
        produto = Produto.query.get(contagem.produto_id)
        resultado = contagem.to_dict()
        resultado['produto'] = produto.to_dict()
        return jsonify({'success': True, 'contagem': resultado})

    if request.method == 'PUT':
        try:
            data = request.get_json()
            if not data:
                return jsonify({'success': False, 'message': 'Dados não fornecidos'}), 400

            # Validar dados obrigatórios
            campos_obrigatorios = ['lote', 'validade_mes', 'validade_ano', 'quantidade']
            for campo in campos_obrigatorios:
                if campo not in data:
                    return jsonify({'success': False, 'message': f'Campo {campo} é obrigatório'}), 400

            # Validar tipos de dados
            try:
                validade_mes = int(data['validade_mes'])
                validade_ano = int(data['validade_ano'])
                quantidade = int(data['quantidade'])
            except ValueError:
                return jsonify({'success': False, 'message': 'Mês, ano e quantidade devem ser números inteiros'}), 400

            # Validar valores
            if validade_mes < 1 or validade_mes > 12:
                return jsonify({'success': False, 'message': 'Mês deve estar entre 1 e 12'}), 400

            if quantidade < 0:
                return jsonify({'success': False, 'message': 'Quantidade não pode ser negativa'}), 400

            # Verificar se o novo lote já existe para o mesmo produto (exceto a contagem atual)
            lote_existente = Contagem.query.filter(
                Contagem.produto_id == contagem.produto_id,
                Contagem.lote == data['lote'].upper(),
                Contagem.id != contagem_id
            ).first()

            if lote_existente:
                return jsonify({'success': False, 'message': f'Lote {data["lote"].upper()} já existe para este produto. Use a função de soma automática ou escolha outro lote.'}), 400

            # Atualizar contagem
            contagem.lote = data['lote'].upper()
            contagem.validade_mes = validade_mes
            contagem.validade_ano = validade_ano
            contagem.quantidade = quantidade

            db.session.commit()

            return jsonify({'success': True, 'message': 'Contagem alterada com sucesso', 'contagem': contagem.to_dict()})

        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': f'Erro ao alterar contagem: {str(e)}'}), 500

    if request.method == 'DELETE':
        try:
            db.session.delete(contagem)
            db.session.commit()
            return jsonify({'success': True, 'message': 'Contagem excluída com sucesso'})

        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': f'Erro ao excluir contagem: {str(e)}'}), 500



@contagem_bp.route('/contagens/resumo', methods=['GET'])
def resumo_estoque():
    """Retorna um resumo do estoque com totais por produto"""
    try:
        # Buscar todos os produtos ordenados por código
        produtos = Produto.query.order_by(Produto.codigo).all()
        
        resumo = []
        total_geral = 0
        
        for produto in produtos:
            # Somar todas as quantidades deste produto
            total_produto = db.session.query(func.sum(Contagem.quantidade)).filter_by(
                produto_id=produto.id
            ).scalar() or 0
            
            # Buscar todas as contagens deste produto
            contagens = Contagem.query.filter_by(produto_id=produto.id).order_by(Contagem.lote).all()
            
            item_resumo = {
                'produto': produto.to_dict(),
                'contagens': [contagem.to_dict() for contagem in contagens],
                'total_quantidade': total_produto
            }
            
            resumo.append(item_resumo)
            total_geral += total_produto
        
        return jsonify({
            'success': True,
            'resumo': resumo,
            'total_geral': total_geral,
            'total_produtos': len(produtos)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao gerar resumo: {str(e)}'
        }), 500

@contagem_bp.route('/contagens/zerar', methods=['POST'])
def zerar_estoque():
    """Zera todas as contagens do estoque (usar com cuidado!)"""
    try:
        # Confirmar se o usuário realmente quer zerar
        data = request.get_json()
        if not data or data.get('confirmar') != 'SIM_ZERAR_TUDO':
            return jsonify({
                'success': False,
                'message': 'Para zerar o estoque, envie {"confirmar": "SIM_ZERAR_TUDO"}'
            }), 400
        
        # Contar quantas contagens serão excluídas
        total_contagens = Contagem.query.count()
        
        # Excluir todas as contagens
        Contagem.query.delete()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Estoque zerado com sucesso. {total_contagens} contagens foram excluídas.'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Erro ao zerar estoque: {str(e)}'
        }), 500


