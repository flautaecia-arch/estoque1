# Sistema de Controle de Estoque

Sistema completo de gestão de produtos e controle de estoque com códigos de 4 dígitos numéricos, relatórios ordenados e importação via Excel.

## Funcionalidades Implementadas

✅ **Códigos de Produto de 4 Dígitos**
- Validação rigorosa: apenas códigos numéricos de exatamente 4 dígitos
- Preenchimento automático com zeros à esquerda para códigos menores
- Rejeição de códigos com mais de 4 dígitos

✅ **Ordenação por Código do Produto**
- Todos os relatórios (PDF e Excel) são ordenados por código em ordem crescente
- Listagem de produtos ordenada por código
- Contagens organizadas por código do produto

✅ **Importação de Produtos via XLSX**
- Upload de arquivos Excel (.xlsx e .xls)
- Detecção automática de colunas (código e nome)
- Validação e conversão automática de códigos para 4 dígitos
- Relatório detalhado de importação com erros

✅ **Interface Web Completa**
- Design responsivo e moderno
- Navegação por abas (Produtos, Contagem, Relatórios)
- Formulários intuitivos com validação
- Feedback visual para operações

✅ **Controle de Lotes**
- Não permite duplicação de lotes por produto
- Soma automaticamente quantidades quando o lote já existe
- Validação de datas de validade (mês e ano)

✅ **Geração de Relatórios**
- Relatório PDF idêntico ao modelo fornecido
- Relatório Excel com formatação e fórmulas
- Resumo online interativo
- Todos os produtos incluídos, mesmo com estoque zerado

## Estrutura do Projeto

```
estoque_app/
├── src/
│   ├── main.py              # Aplicação principal Flask
│   ├── database.py          # Configuração do SQLAlchemy
│   ├── models/
│   │   ├── produto.py       # Modelo de produto com validação
│   │   └── contagem.py      # Modelo de contagem de estoque
│   ├── routes/
│   │   ├── produto.py       # Rotas para gestão de produtos
│   │   ├── contagem.py      # Rotas para contagem de estoque
│   │   └── relatorio.py     # Rotas para relatórios PDF/Excel
│   └── static/
│       ├── index.html       # Interface web
│       ├── styles.css       # Estilos CSS
│       └── script.js        # JavaScript da aplicação
├── venv/                    # Ambiente virtual Python
├── requirements.txt         # Dependências do projeto
├── render.yaml             # Configuração para deploy no Render
└── README.md               # Esta documentação
```

## Como Executar Localmente

### 1. Preparar o Ambiente
```bash
cd estoque_app
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows
```

### 2. Instalar Dependências
```bash
pip install -r requirements.txt
```

### 3. Executar a Aplicação
```bash
python src/main.py
```

A aplicação estará disponível em: http://localhost:5000

## API Endpoints

### Produtos
- `GET /api/produtos` - Listar produtos (ordenado por código)
- `POST /api/produtos` - Criar produto
- `GET /api/produtos/{codigo}` - Buscar produto por código
- `PUT /api/produtos/{id}` - Atualizar produto
- `DELETE /api/produtos/{id}` - Excluir produto

### Contagem
- `GET /api/contagens` - Listar contagens (ordenado por código)
- `POST /api/contagens` - Registrar contagem
- `GET /api/contagens/produto/{codigo}` - Contagens de um produto
- `DELETE /api/contagens/{id}` - Excluir contagem

### Relatórios
- `GET /api/relatorio/resumo` - Resumo do estoque (JSON)
- `GET /api/relatorio/pdf` - Relatório PDF (ordenado por código)
- `GET /api/relatorio/excel` - Relatório Excel (ordenado por código)

### Importação
- `POST /api/produtos/importar` - Importar produtos via XLSX
- `GET /api/produtos/template` - Baixar template Excel

## Validações Implementadas

### Código do Produto
- Deve ser numérico
- Deve ter exatamente 4 dígitos
- Códigos menores são preenchidos com zeros à esquerda
- Códigos maiores são rejeitados
- Deve ser único no sistema

### Contagem de Estoque
- Lote não pode ser duplicado por produto
- Quantidades são somadas automaticamente para lotes existentes
- Validação de mês (1-12) e ano (2000-2099)
- Quantidade deve ser não negativa

### Importação XLSX
- Detecção automática de colunas por nome
- Fallback para primeiras duas colunas
- Validação linha por linha
- Relatório detalhado de erros
- Rollback em caso de erro crítico

## Deploy no Render

### 1. Preparar Repositório
```bash
git init
git add .
git commit -m "Sistema de estoque completo"
git remote add origin <seu-repositorio>
git push -u origin main
```

### 2. Configurar no Render
1. Conectar repositório GitHub
2. Configurar como Web Service
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `python src/main.py`
5. Environment: Python 3.11

### 3. Variáveis de Ambiente (Opcional)
- `FLASK_ENV=production`
- `SECRET_KEY=sua_chave_secreta`

## Tecnologias Utilizadas

- **Backend**: Flask, SQLAlchemy, SQLite
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Relatórios**: ReportLab (PDF), Pandas + OpenPyXL (Excel)
- **Upload**: Werkzeug, Pandas
- **Deploy**: Render (recomendado)

## Características Especiais

### Design Responsivo
- Interface adaptável para desktop e mobile
- Navegação por abas intuitiva
- Formulários com validação em tempo real
- Notificações toast para feedback

### Relatórios Profissionais
- PDF idêntico ao modelo fornecido
- Excel com formatação e fórmulas
- Ordenação crescente por código
- Subtotais por produto e total geral

### Importação Inteligente
- Detecção automática de colunas
- Validação completa dos dados
- Relatório detalhado de erros
- Prevenção de dados inconsistentes

## Suporte

Para dúvidas ou problemas:
1. Verificar logs da aplicação
2. Consultar esta documentação
3. Verificar validações de entrada
4. Testar com dados de exemplo

---

**Desenvolvido com Flask e Python 🐍**

Sistema pronto para produção no Render.com

