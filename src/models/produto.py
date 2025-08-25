from src.database import db
from datetime import datetime

class Produto(db.Model):
    __tablename__ = 'produtos'
    
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(4), unique=True, nullable=False, index=True)
    nome = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamento com contagens
    contagens = db.relationship('Contagem', backref='produto', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, codigo, nome):
        # Garantir que o código tenha 4 dígitos com zeros à esquerda
        self.codigo = str(codigo).zfill(4)
        self.nome = nome.strip().upper()
    
    @staticmethod
    def validar_codigo(codigo):
        """Valida se o código é numérico e tem no máximo 4 dígitos"""
        try:
            codigo_int = int(codigo)
            if codigo_int < 0 or codigo_int > 9999:
                return False, "Código deve estar entre 0000 e 9999"
            return True, str(codigo_int).zfill(4)
        except ValueError:
            return False, "Código deve ser numérico"
    
    def to_dict(self):
        return {
            'id': self.id,
            'codigo': self.codigo,
            'nome': self.nome,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Produto {self.codigo}: {self.nome}>'

