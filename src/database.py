import os

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def init_database(app):
    """Inicializa o banco de dados com a aplicação Flask"""
    db.init_app(app)
    
    with app.app_context():
        # Importar todos os modelos para garantir que as tabelas sejam criadas
        from src.models.produto import Produto
        from src.models.contagem import Contagem
        
        # Criar todas as tabelas
        db.create_all()
        
        print("Banco de dados inicializado com sucesso!")
        
    return db

