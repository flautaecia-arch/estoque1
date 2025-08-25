from src.database import db
from datetime import datetime

class Contagem(db.Model):
    __tablename__ = 'contagens'
    
    id = db.Column(db.Integer, primary_key=True)
    produto_id = db.Column(db.Integer, db.ForeignKey('produtos.id'), nullable=False)
    lote = db.Column(db.String(50), nullable=False)
    validade_mes = db.Column(db.Integer, nullable=False)  # 1-12
    validade_ano = db.Column(db.Integer, nullable=False)  # YYYY
    quantidade = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Índice único para evitar duplicação de lotes por produto
    __table_args__ = (db.UniqueConstraint('produto_id', 'lote', name='unique_produto_lote'),)
    
    def __init__(self, produto_id, lote, validade_mes, validade_ano, quantidade):
        self.produto_id = produto_id
        self.lote = lote.strip().upper()
        self.validade_mes = int(validade_mes)
        self.validade_ano = int(validade_ano)
        self.quantidade = int(quantidade)
    
    @staticmethod
    def validar_validade(mes, ano):
        """Valida se mês e ano são válidos"""
        try:
            mes_int = int(mes)
            ano_int = int(ano)
            
            if mes_int < 1 or mes_int > 12:
                return False, "Mês deve estar entre 1 e 12"
            
            if ano_int < 2000 or ano_int > 2099:
                return False, "Ano deve estar entre 2000 e 2099"
                
            return True, (mes_int, ano_int)
        except ValueError:
            return False, "Mês e ano devem ser numéricos"
    
    @staticmethod
    def adicionar_ou_somar(produto_id, lote, validade_mes, validade_ano, quantidade):
        """
        Adiciona uma nova contagem ou soma à quantidade existente se o lote já existir
        """
        # Buscar se já existe uma contagem para este produto e lote
        contagem_existente = Contagem.query.filter_by(
            produto_id=produto_id,
            lote=lote.strip().upper()
        ).first()
        
        if contagem_existente:
            # Se existe, somar a quantidade
            contagem_existente.quantidade += int(quantidade)
            contagem_existente.updated_at = datetime.utcnow()
            return contagem_existente, False  # False = não criou novo
        else:
            # Se não existe, criar novo
            nova_contagem = Contagem(produto_id, lote, validade_mes, validade_ano, quantidade)
            return nova_contagem, True  # True = criou novo
    
    def get_validade_formatada(self):
        """Retorna a validade no formato MM/YYYY"""
        return f"{self.validade_mes:02d}/{self.validade_ano}"
    
    def to_dict(self):
        return {
            'id': self.id,
            'produto_id': self.produto_id,
            'lote': self.lote,
            'validade_mes': self.validade_mes,
            'validade_ano': self.validade_ano,
            'validade_formatada': self.get_validade_formatada(),
            'quantidade': self.quantidade,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Contagem Produto:{self.produto_id} Lote:{self.lote} Qtd:{self.quantidade}>'

