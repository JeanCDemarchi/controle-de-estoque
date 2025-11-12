from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

# --- 1. CONFIGURAÇÃO BÁSICA ---
app = Flask(__name__)
# Configura o banco de dados SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///estoque_oficina.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- 2. MODELO DE DADOS (Tabela do Banco de Dados) ---
class Produto(db.Model):
    # Campos baseados nos requisitos de uma oficina
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    sku = db.Column(db.String(20), unique=True, nullable=False) # Código Único
    quantidade = db.Column(db.Integer, default=0)
    custo = db.Column(db.Float, default=0.0) # Preço de Custo
    min_estoque = db.Column(db.Integer, default=5) # Ponto de Pedido

    def __repr__(self):
        return f'<Produto {self.nome} - {self.quantidade}>'

# Cria o banco de dados e as tabelas (Execute isso uma vez)
with app.app_context():
    db.create_all()

# --- 3. ROTAS DO SERVIDOR WEB ---

# Rota principal: Lista o estoque
@app.route('/')
def lista_estoque():
    # Ordena os produtos por nome
    produtos = Produto.query.order_by(Produto.nome).all()
    return render_template('estoque.html', produtos=produtos)

# Rota para adicionar um novo produto
@app.route('/adicionar', methods=['GET', 'POST'])
def adicionar_produto():
    if request.method == 'POST':
        # Pega os dados do formulário
        nome = request.form['nome']
        sku = request.form['sku']
        quantidade = int(request.form['quantidade'])
        custo = float(request.form['custo'])
        min_estoque = int(request.form['min_estoque'])

        novo_produto = Produto(
            nome=nome, 
            sku=sku, 
            quantidade=quantidade, 
            custo=custo, 
            min_estoque=min_estoque
        )
        try:
            db.session.add(novo_produto)
            db.session.commit()
            return redirect(url_for('lista_estoque'))
        except:
            # Em caso de erro (ex: SKU duplicado)
            return 'Ocorreu um erro ao adicionar o produto.'

    return render_template('adicionar.html')

# Rota para dar entrada/saída no estoque
@app.route('/movimentar/<int:produto_id>', methods=['GET', 'POST'])
def movimentar_estoque(produto_id):
    produto = Produto.query.get_or_404(produto_id)

    if request.method == 'POST':
        tipo = request.form['tipo'] # 'entrada' ou 'saida'
        movimento_qtd = int(request.form['quantidade'])
        
        if tipo == 'entrada':
            produto.quantidade += movimento_qtd
        elif tipo == 'saida':
            # Evita estoque negativo
            if produto.quantidade >= movimento_qtd:
                produto.quantidade -= movimento_qtd
            else:
                return 'Erro: Quantidade de saída excede o estoque atual.'
        
        db.session.commit()
        return redirect(url_for('lista_estoque'))

    return render_template('movimentar.html', produto=produto)
# Rota para EXCLUIR um produto
@app.route('/excluir/<int:produto_id>', methods=['POST'])
def excluir_produto(produto_id):
    produto = Produto.query.get_or_404(produto_id)
    try:
        db.session.delete(produto)
        db.session.commit()
        return redirect(url_for('lista_estoque'))
    except:
        return 'Ocorreu um erro ao excluir o produto.'

# Rota para EDITAR os detalhes de um produto
@app.route('/editar/<int:produto_id>', methods=['GET', 'POST'])
def editar_produto(produto_id):
    produto = Produto.query.get_or_404(produto_id)
    
    if request.method == 'POST':
        # Atualiza os campos do produto com os dados do formulário
        produto.nome = request.form['nome']
        produto.sku = request.form['sku']
        produto.custo = float(request.form['custo'])
        produto.min_estoque = int(request.form['min_estoque'])
        
        # A quantidade atual deve ser modificada apenas pela rota 'movimentar'
        # Mas, se quiser permitir ajuste manual, pode incluir aqui
        # produto.quantidade = int(request.form['quantidade'])
        
        try:
            db.session.commit()
            return redirect(url_for('lista_estoque'))
        except:
            return 'Ocorreu um erro ao editar o produto.'
            
    # Se for GET, mostra o formulário preenchido com os dados atuais
    return render_template('editar.html', produto=produto)

# --- 4. EXECUÇÃO DO SERVIDOR ---
if __name__ == '__main__':
    # Cria o arquivo do banco de dados se não existir
    with app.app_context():
        db.create_all()
    # Inicia o servidor em http://127.0.0.1:5000/
    app.run(debug=True)
