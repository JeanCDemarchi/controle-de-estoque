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
    ncm = db.Column(db.String(8))
    quantidade = db.Column(db.Integer, default=0)
    custo = db.Column(db.Float, default=0.0) # Preço de Custo
    min_estoque = db.Column(db.Integer, default=5) # Ponto de Pedido

    def __repr__(self):
        return f'<Produto {self.nome} - {self.quantidade}>'

class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cpf_cnpj = db.Column(db.String(20), unique=True, nullable=False)
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    # Endereço Completo
    logradouro = db.Column(db.String(100)) # Rua, Av, etc.
    numero = db.Column(db.String(10))
    bairro = db.Column(db.String(50))
    cidade = db.Column(db.String(50))
    estado = db.Column(db.String(2))
    cep = db.Column(db.String(10))

    def __repr__(self):
        return f'<Cliente {self.nome}>'

# Cria o banco de dados e as tabelas (Execute isso uma vez)
with app.app_context():
    db.create_all()

# --- 3. ROTAS DO SERVIDOR WEB ---


# Rota principal: Lista o estoque com opção de busca
@app.route('/')
def lista_estoque():
    # Pega o termo de busca enviado pelo formulário (via método GET)
    termo_busca = request.args.get('q', '')

    if termo_busca:
        # Filtra produtos que contenham o termo no Nome OU no SKU
        produtos = Produto.query.filter(
            (Produto.nome.contains(termo_busca)) | 
            (Produto.sku.contains(termo_busca))
        ).all()
    else:
        # Se não houver busca, lista todos ordenados por nome
        produtos = Produto.query.order_by(Produto.nome).all()
    
    return render_template('estoque.html', produtos=produtos, busca=termo_busca)

# Rota para adicionar um novo produto
@app.route('/adicionar', methods=['GET', 'POST'])
def adicionar_produto():
    if request.method == 'POST':
        # Pega os dados do formulário
        nome = request.form['nome']
        sku = request.form['sku']
        ncm = request.form['ncm']
        quantidade = int(request.form['quantidade'])
        custo = float(request.form['custo'])
        min_estoque = int(request.form['min_estoque'])

        novo_produto = Produto(
            nome=nome, 
            sku=sku,
            ncm=ncm, 
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
        produto.ncm = request.form['ncm']
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

@app.route('/clientes')
def lista_clientes():
    # Pega o termo de busca do campo 'q' na URL
    termo_busca = request.args.get('q', '')

    if termo_busca:
        # Filtra clientes que contenham o termo no Nome OU no CPF/CNPJ
        clientes = Cliente.query.filter(
            (Cliente.nome.contains(termo_busca)) | 
            (Cliente.cpf_cnpj.contains(termo_busca))
        ).all()
    else:
        # Se não houver busca, lista todos por ordem alfabética
        clientes = Cliente.query.order_by(Cliente.nome).all()
    
    return render_template('clientes.html', clientes=clientes, busca=termo_busca)

@app.route('/clientes/novo', methods=['GET', 'POST'])
def adicionar_cliente():
    if request.method == 'POST':
        novo_cliente = Cliente(
            nome=request.form['nome'],
            cpf_cnpj=request.form['cpf_cnpj'],
            telefone=request.form['telefone'],
            email=request.form['email'],
            logradouro=request.form['logradouro'],
            numero=request.form['numero'],
            bairro=request.form['bairro'],
            cidade=request.form['cidade'],
            estado=request.form['estado'],
            cep=request.form['cep']
        )
        db.session.add(novo_cliente)
        db.session.commit()
        return redirect(url_for('lista_clientes'))
    return render_template('adicionar_cliente.html')

# Rota para Editar Cliente
@app.route('/clientes/editar/<int:id>', methods=['GET', 'POST'])
def editar_cliente(id):
    cliente = Cliente.query.get_or_404(id)
    if request.method == 'POST':
        cliente.nome = request.form['nome']
        cliente.cpf_cnpj = request.form['cpf_cnpj']
        cliente.telefone = request.form['telefone']
        cliente.email = request.form['email']
        cliente.logradouro = request.form['logradouro']
        cliente.numero = request.form['numero']
        cliente.bairro = request.form['bairro']
        cliente.cidade = request.form['cidade']
        cliente.estado = request.form['estado']
        cliente.cep = request.form['cep']
        
        db.session.commit()
        return redirect(url_for('lista_clientes'))
    
    return render_template('editar_cliente.html', cliente=cliente)

# Rota para Excluir Cliente
@app.route('/clientes/excluir/<int:id>', methods=['POST'])
def excluir_cliente(id):
    cliente = Cliente.query.get_or_404(id)
    db.session.delete(cliente)
    db.session.commit()
    return redirect(url_for('lista_clientes'))

# --- 4. EXECUÇÃO DO SERVIDOR ---
if __name__ == '__main__':
    # Cria o arquivo do banco de dados se não existir
    with app.app_context():
        db.create_all()
    # Inicia o servidor em http://127.0.0.1:5000/
    app.run(debug=True)
