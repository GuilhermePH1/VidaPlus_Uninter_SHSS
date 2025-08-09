"""
Sistema de Gestão Hospitalar e de Serviços de Saúde (SGHSS) - VidaPlus
Arquivo Consolidado - Todas as Rotas e Configurações

Este arquivo contém toda a aplicação Flask consolidada em um único arquivo,
incluindo:
- Configuração do banco de dados SQLAlchemy
- Configuração do sistema de autenticação JWT
- Configuração do CORS para permitir requisições cross-origin
- Todos os modelos do banco de dados
- Todas as rotas da aplicação (auth, pacientes, profissionais, administracao, telemedicina, relatorios)
- Criação das tabelas do banco de dados
- População inicial de dados

Autor: Sistema VidaPlus
Data: 2024
"""

# Importações necessárias do Flask e extensões
from flask import Flask, Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, JWTManager
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, timezone, date
from dotenv import load_dotenv
import os
import re
import json
import uuid
from sqlalchemy import func, and_, extract

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Instâncias das extensões Flask
db = SQLAlchemy()
jwt = JWTManager()
bcrypt = Bcrypt()

# =============================================================================
# MODELOS DO BANCO DE DADOS
# =============================================================================

class Usuario(db.Model, UserMixin):
    """Modelo base para todos os usuários do sistema"""
    
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # admin, paciente, profissional
    ativo = db.Column(db.Boolean, default=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    ultimo_acesso = db.Column(db.DateTime)
    
    def set_senha(self, senha):
        """Define a senha do usuário com criptografia"""
        self.senha_hash = generate_password_hash(senha)
    
    def check_senha(self, senha):
        """Verifica se a senha fornecida está correta"""
        return check_password_hash(self.senha_hash, senha)
    
    def __repr__(self):
        return f'<Usuario {self.email}>'

class Paciente(db.Model):
    """Modelo para cadastro de pacientes"""
    
    __tablename__ = 'pacientes'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    cpf = db.Column(db.String(14), unique=True, nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    data_nascimento = db.Column(db.Date, nullable=False)
    sexo = db.Column(db.String(1), nullable=False)  # M, F, O
    telefone = db.Column(db.String(20))
    endereco = db.Column(db.Text)
    plano_saude = db.Column(db.String(100))
    alergias = db.Column(db.Text)
    medicamentos_uso = db.Column(db.Text)
    historico_familiar = db.Column(db.Text)
    
    # Relacionamentos
    usuario = db.relationship('Usuario', backref='paciente', uselist=False)
    consultas = db.relationship('Consulta', backref='paciente', lazy=True)
    prescricoes = db.relationship('Prescricao', backref='paciente', lazy=True)
    
    def __repr__(self):
        return f'<Paciente {self.nome}>'

class Profissional(db.Model):
    """Modelo para profissionais de saúde"""
    
    __tablename__ = 'profissionais'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    crm_coren = db.Column(db.String(20), unique=True, nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    especialidade = db.Column(db.String(100))
    telefone = db.Column(db.String(20))
    email_profissional = db.Column(db.String(120))
    data_admissao = db.Column(db.Date, default=datetime.utcnow().date)
    ativo = db.Column(db.Boolean, default=True)
    
    # Relacionamentos
    usuario = db.relationship('Usuario', backref='profissional', uselist=False)
    consultas = db.relationship('Consulta', backref='profissional', lazy=True)
    prescricoes = db.relationship('Prescricao', backref='profissional', lazy=True)
    
    def __repr__(self):
        return f'<Profissional {self.nome} - {self.especialidade}>'

class Unidade(db.Model):
    """Modelo para unidades hospitalares"""
    
    __tablename__ = 'unidades'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    tipo = db.Column(db.String(50), nullable=False)
    endereco = db.Column(db.Text, nullable=False)
    telefone = db.Column(db.String(20))
    cnpj = db.Column(db.String(18), unique=True)
    ativo = db.Column(db.Boolean, default=True)
    
    # Relacionamentos
    consultas = db.relationship('Consulta', backref='unidade', lazy=True)
    
    def __repr__(self):
        return f'<Unidade {self.nome} - {self.tipo}>'

# Tabela Leito removida - não utilizada no sistema atual

class Consulta(db.Model):
    """Modelo para agendamento e gestão de consultas"""
    
    __tablename__ = 'consultas'
    
    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey('pacientes.id'), nullable=False)
    profissional_id = db.Column(db.Integer, db.ForeignKey('profissionais.id'), nullable=False)
    unidade_id = db.Column(db.Integer, db.ForeignKey('unidades.id'), nullable=False)
    data_hora = db.Column(db.DateTime, nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # presencial, telemedicina
    status = db.Column(db.String(20), default='agendada')
    observacoes = db.Column(db.Text)
    link_telemedicina = db.Column(db.String(255))
    
    # Relacionamentos removidos - tabelas não utilizadas
    
    def __repr__(self):
        return f'<Consulta {self.paciente.nome} - {self.profissional.nome} - {self.data_hora}>'

# Tabela Exame removida - não utilizada no sistema atual

# Tabela Prontuario removida - não utilizada no sistema atual

class Prescricao(db.Model):
    """Modelo para prescrições médicas digitais"""
    
    __tablename__ = 'prescricoes'
    
    id = db.Column(db.Integer, primary_key=True)
    paciente_id = db.Column(db.Integer, db.ForeignKey('pacientes.id'), nullable=False)
    profissional_id = db.Column(db.Integer, db.ForeignKey('profissionais.id'), nullable=False)
    data_prescricao = db.Column(db.DateTime, default=datetime.utcnow)
    medicamentos = db.Column(db.Text, nullable=False)
    dosagem = db.Column(db.Text, nullable=False)
    duracao = db.Column(db.String(50))
    observacoes = db.Column(db.Text)
    status = db.Column(db.String(20), default='ativa')
    
    def __repr__(self):
        return f'<Prescricao {self.paciente.nome} - {self.data_prescricao}>'

# Tabela Telemedicina removida - não utilizada no sistema atual

class Auditoria(db.Model):
    """Modelo para logs de auditoria"""
    
    __tablename__ = 'auditoria'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    acao = db.Column(db.String(50), nullable=False)  # CREATE, UPDATE, DELETE, LOGIN, etc.
    tabela = db.Column(db.String(50), nullable=False)
    registro_id = db.Column(db.Integer)
    dados_anteriores = db.Column(db.Text)  # JSON
    dados_novos = db.Column(db.Text)  # JSON
    ip = db.Column(db.String(45))
    data_hora = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    usuario = db.relationship('Usuario', backref='auditorias')
    
    def __repr__(self):
        return f'<Auditoria {self.usuario.email} - {self.acao} - {self.tabela}>'

class Notificacao(db.Model):
    """Modelo para notificações do sistema"""
    
    __tablename__ = 'notificacoes'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    titulo = db.Column(db.String(100), nullable=False)
    mensagem = db.Column(db.Text, nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # agendamento, resultado, sistema
    lida = db.Column(db.Boolean, default=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    usuario = db.relationship('Usuario', backref='notificacoes')
    
    def __repr__(self):
        return f'<Notificacao {self.usuario.email} - {self.titulo}>'

# =============================================================================
# FUNÇÕES UTILITÁRIAS
# =============================================================================

def registrar_auditoria(usuario_id, acao, tabela, registro_id=None, dados_anteriores=None, dados_novos=None):
    """Função utilitária para registrar ações de auditoria"""
    try:
        ip = request.remote_addr
        auditoria = Auditoria(
            usuario_id=usuario_id,
            acao=acao,
            tabela=tabela,
            registro_id=registro_id,
            dados_anteriores=dados_anteriores,
            dados_novos=dados_novos,
            ip=ip,
            data_hora=datetime.utcnow()
        )
        db.session.add(auditoria)
        db.session.commit()
    except Exception as e:
        print(f"Erro ao registrar auditoria: {e}")
        db.session.rollback()

def validar_email(email):
    """Valida o formato do email"""
    padrao = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(padrao, email) is not None

def validar_senha(senha):
    """Valida a força da senha"""
    if len(senha) < 8:
        return {'valida': False, 'mensagem': 'A senha deve ter pelo menos 8 caracteres'}
    if not re.search(r'[A-Z]', senha):
        return {'valida': False, 'mensagem': 'A senha deve conter pelo menos uma letra maiúscula'}
    if not re.search(r'[a-z]', senha):
        return {'valida': False, 'mensagem': 'A senha deve conter pelo menos uma letra minúscula'}
    if not re.search(r'\d', senha):
        return {'valida': False, 'mensagem': 'A senha deve conter pelo menos um número'}
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', senha):
        return {'valida': False, 'mensagem': 'A senha deve conter pelo menos um caractere especial'}
    return {'valida': True, 'mensagem': 'Senha válida'}

def validar_cpf(cpf):
    """Valida o formato e dígitos verificadores do CPF"""
    cpf = re.sub(r'[^0-9]', '', cpf)
    if len(cpf) != 11:
        return {'valido': False, 'mensagem': 'CPF deve ter 11 dígitos'}
    if cpf == cpf[0] * 11:
        return {'valido': False, 'mensagem': 'CPF inválido'}
    
    # Calcula dígitos verificadores
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    resto = soma % 11
    digito1 = 0 if resto < 2 else 11 - resto
    
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    resto = soma % 11
    digito2 = 0 if resto < 2 else 11 - resto
    
    if int(cpf[9]) != digito1 or int(cpf[10]) != digito2:
        return {'valido': False, 'mensagem': 'CPF inválido'}
    
    return {'valido': True, 'mensagem': 'CPF válido'}

def formatar_cpf(cpf):
    """Formata o CPF no padrão XXX.XXX.XXX-XX"""
    cpf = re.sub(r'[^0-9]', '', cpf)
    return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"

def validar_cnpj(cnpj):
    """Valida o formato e dígitos verificadores do CNPJ"""
    cnpj = re.sub(r'[^0-9]', '', cnpj)
    if len(cnpj) != 14:
        return {'valido': False, 'mensagem': 'CNPJ deve ter 14 dígitos'}
    if cnpj == cnpj[0] * 14:
        return {'valido': False, 'mensagem': 'CNPJ inválido'}
    
    # Calcula dígitos verificadores
    multiplicadores = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = sum(int(cnpj[i]) * multiplicadores[i] for i in range(12))
    resto = soma % 11
    digito1 = 0 if resto < 2 else 11 - resto
    
    multiplicadores = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = sum(int(cnpj[i]) * multiplicadores[i] for i in range(13))
    resto = soma % 11
    digito2 = 0 if resto < 2 else 11 - resto
    
    if int(cnpj[12]) != digito1 or int(cnpj[13]) != digito2:
        return {'valido': False, 'mensagem': 'CNPJ inválido'}
    
    return {'valido': True, 'mensagem': 'CNPJ válido'}

def validar_crm(crm):
    """Valida o formato do CRM/COREN"""
    crm_limpo = re.sub(r'[^0-9]', '', crm)
    if len(crm_limpo) < 5 or len(crm_limpo) > 10:
        return {'valido': False, 'mensagem': 'CRM/COREN deve ter entre 5 e 10 dígitos'}
    
    return {'valido': True, 'mensagem': 'CRM/COREN válido'}

def criar_notificacao(usuario_id, titulo, mensagem, tipo='sistema'):
    """Cria uma notificação para o usuário"""
    try:
        notificacao = Notificacao(
            usuario_id=usuario_id,
            titulo=titulo,
            mensagem=mensagem,
            tipo=tipo,
            lida=False,
            data_criacao=datetime.utcnow()
        )
        db.session.add(notificacao)
        db.session.commit()
    except Exception as e:
        print(f"Erro ao criar notificação: {e}")
        db.session.rollback()

def gerar_sala_virtual():
    """Gera um identificador único para sala virtual"""
    return f"sala_{uuid.uuid4().hex[:12]}"

def gerar_link_acesso(sala_virtual):
    """Gera o link de acesso para a sala virtual"""
    base_url = "https://telemedicina.vidaplus.com"
    return f"{base_url}/sala/{sala_virtual}"

def criar_dados_iniciais():
    """Função para criar dados iniciais do sistema"""
    if Usuario.query.first():
        return  # Sistema já foi inicializado
    
    # Criação do usuário administrador
    admin = Usuario(
        email='admin@vidaplus.com',
        tipo='admin',
        ativo=True
    )
    admin.set_senha('admin123')
    db.session.add(admin)
    
    # Criação da unidade hospitalar padrão
    unidade = Unidade(
        nome='Hospital VidaPlus Central',
        tipo='hospital',
        endereco='Rua das Flores, 123 - Centro - São Paulo/SP',
        telefone='(11) 1234-5678',
        cnpj='12.345.678/0001-90',
        ativo=True
    )
    db.session.add(unidade)
    db.session.commit()
    
    # Criação de leitos removida - funcionalidade não utilizada no sistema atual
    
    print("Dados iniciais criados com sucesso!")
    print("Usuário admin: admin@vidaplus.com")
    print("Senha: admin123")
    print("IMPORTANTE: Altere a senha do administrador após o primeiro login!")

# =============================================================================
# BLUEPRINTS E ROTAS
# =============================================================================

# Blueprint para autenticação
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    """Endpoint para autenticação de usuários"""
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({'erro': 'Dados não fornecidos'}), 400
        
        email = dados.get('email')
        senha = dados.get('senha')
        
        if not email or not senha:
            return jsonify({'erro': 'Email e senha são obrigatórios'}), 400
        
        usuario = Usuario.query.filter_by(email=email).first()
        
        if not usuario or not usuario.check_senha(senha):
            return jsonify({'erro': 'Email ou senha inválidos'}), 401
        
        if not usuario.ativo:
            return jsonify({'erro': 'Conta desativada. Entre em contato com o administrador.'}), 403
        
        usuario.ultimo_acesso = datetime.utcnow()
        db.session.commit()
        
        token = create_access_token(identity=usuario.id)
        
        registrar_auditoria(
            usuario_id=usuario.id,
            acao='LOGIN',
            tabela='usuarios',
            registro_id=usuario.id,
            dados_novos=json.dumps({'ultimo_acesso': usuario.ultimo_acesso.isoformat()})
        )
        
        return jsonify({
            'mensagem': 'Login realizado com sucesso',
            'token': token,
            'usuario': {
                'id': usuario.id,
                'email': usuario.email,
                'tipo': usuario.tipo,
                'ativo': usuario.ativo
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro interno do servidor: {str(e)}'}), 500

@auth_bp.route('/registro', methods=['POST'])
def registro():
    """Endpoint para registro de novos usuários"""
    try:
        dados = request.get_json()
        if not dados:
            return jsonify({'erro': 'Dados não fornecidos'}), 400
        
        email = dados.get('email')
        senha = dados.get('senha')
        tipo = dados.get('tipo', 'paciente')
        
        if not email or not senha:
            return jsonify({'erro': 'Email e senha são obrigatórios'}), 400
        
        if not validar_email(email):
            return jsonify({'erro': 'Formato de email inválido'}), 400
        
        validacao_senha = validar_senha(senha)
        if not validacao_senha['valida']:
            return jsonify({'erro': validacao_senha['mensagem']}), 400
        
        if Usuario.query.filter_by(email=email).first():
            return jsonify({'erro': 'Email já está em uso'}), 409
        
        tipos_validos = ['paciente', 'profissional', 'admin']
        if tipo not in tipos_validos:
            return jsonify({'erro': 'Tipo de usuário inválido'}), 400
        
        novo_usuario = Usuario(
            email=email,
            tipo=tipo,
            ativo=True,
            data_criacao=datetime.utcnow()
        )
        novo_usuario.set_senha(senha)
        
        db.session.add(novo_usuario)
        db.session.commit()
        
        registrar_auditoria(
            usuario_id=novo_usuario.id,
            acao='REGISTER',
            tabela='usuarios',
            registro_id=novo_usuario.id,
            dados_novos=json.dumps({
                'email': novo_usuario.email,
                'tipo': novo_usuario.tipo,
                'ativo': novo_usuario.ativo
            })
        )
        
        return jsonify({
            'mensagem': 'Usuário registrado com sucesso',
            'usuario': {
                'id': novo_usuario.id,
                'email': novo_usuario.email,
                'tipo': novo_usuario.tipo
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro interno do servidor: {str(e)}'}), 500

@auth_bp.route('/perfil', methods=['GET'])
@jwt_required()
def perfil():
    """Endpoint para obter informações do perfil do usuário logado"""
    try:
        usuario_id = get_jwt_identity()
        usuario = Usuario.query.get(usuario_id)
        
        if not usuario:
            return jsonify({'erro': 'Usuário não encontrado'}), 404
        
        return jsonify({
            'usuario': {
                'id': usuario.id,
                'email': usuario.email,
                'tipo': usuario.tipo,
                'ativo': usuario.ativo,
                'data_criacao': usuario.data_criacao.isoformat() if usuario.data_criacao else None,
                'ultimo_acesso': usuario.ultimo_acesso.isoformat() if usuario.ultimo_acesso else None
            }
        }), 200
        
    except Exception as e:
        return jsonify({'erro': f'Erro interno do servidor: {str(e)}'}), 500

@auth_bp.route('/alterar-senha', methods=['PUT'])
@jwt_required()
def alterar_senha():
    """Endpoint para alteração de senha do usuário logado"""
    try:
        usuario_id = get_jwt_identity()
        usuario = Usuario.query.get(usuario_id)
        
        if not usuario:
            return jsonify({'erro': 'Usuário não encontrado'}), 404
        
        dados = request.get_json()
        if not dados:
            return jsonify({'erro': 'Dados não fornecidos'}), 400
        
        senha_atual = dados.get('senha_atual')
        nova_senha = dados.get('nova_senha')
        
        if not senha_atual or not nova_senha:
            return jsonify({'erro': 'Senha atual e nova senha são obrigatórias'}), 400
        
        if not usuario.check_senha(senha_atual):
            return jsonify({'erro': 'Senha atual incorreta'}), 401
        
        validacao_senha = validar_senha(nova_senha)
        if not validacao_senha['valida']:
            return jsonify({'erro': validacao_senha['mensagem']}), 400
        
        usuario.set_senha(nova_senha)
        db.session.commit()
        
        registrar_auditoria(
            usuario_id=usuario.id,
            acao='UPDATE_PASSWORD',
            tabela='usuarios',
            registro_id=usuario.id,
            dados_anteriores=json.dumps({'senha_hash': '***'}),
            dados_novos=json.dumps({'senha_hash': '***'})
        )
        
        return jsonify({'mensagem': 'Senha alterada com sucesso'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro interno do servidor: {str(e)}'}), 500

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Endpoint para logout do usuário"""
    try:
        usuario_id = get_jwt_identity()
        usuario = Usuario.query.get(usuario_id)
        
        if not usuario:
            return jsonify({'erro': 'Usuário não encontrado'}), 404
        
        registrar_auditoria(
            usuario_id=usuario.id,
            acao='LOGOUT',
            tabela='usuarios',
            registro_id=usuario.id
        )
        
        return jsonify({'mensagem': 'Logout realizado com sucesso'}), 200
        
    except Exception as e:
        return jsonify({'erro': f'Erro interno do servidor: {str(e)}'}), 500

# Blueprint para pacientes
pacientes_bp = Blueprint('pacientes', __name__)

@pacientes_bp.route('/', methods=['POST'])
@jwt_required()
def cadastrar_paciente():
    """Endpoint para cadastrar um novo paciente"""
    try:
        usuario_id = get_jwt_identity()
        dados = request.get_json()
        
        if not dados:
            return jsonify({'erro': 'Dados não fornecidos'}), 400
        
        campos_obrigatorios = ['email', 'senha', 'cpf', 'nome', 'data_nascimento', 'sexo']
        for campo in campos_obrigatorios:
            if campo not in dados or not dados[campo]:
                return jsonify({'erro': f'Campo {campo} é obrigatório'}), 400
        
        validacao_cpf = validar_cpf(dados['cpf'])
        if not validacao_cpf['valido']:
            return jsonify({'erro': validacao_cpf['mensagem']}), 400
        
        cpf_limpo = re.sub(r'[^0-9]', '', dados['cpf'])
        if Paciente.query.filter_by(cpf=formatar_cpf(cpf_limpo)).first():
            return jsonify({'erro': 'CPF já cadastrado'}), 409
        
        if Usuario.query.filter_by(email=dados['email']).first():
            return jsonify({'erro': 'Email já está em uso'}), 409
        
        sexos_validos = ['M', 'F', 'O']
        if dados['sexo'] not in sexos_validos:
            return jsonify({'erro': 'Sexo deve ser M, F ou O'}), 400
        
        try:
            data_nasc = datetime.strptime(dados['data_nascimento'], '%Y-%m-%d').date()
            if data_nasc > date.today():
                return jsonify({'erro': 'Data de nascimento não pode ser futura'}), 400
        except ValueError:
            return jsonify({'erro': 'Formato de data inválido. Use YYYY-MM-DD'}), 400
        
        usuario = Usuario(
            email=dados['email'],
            tipo='paciente',
            ativo=True,
            data_criacao=datetime.utcnow()
        )
        usuario.set_senha(dados['senha'])
        
        db.session.add(usuario)
        db.session.flush()
        
        paciente = Paciente(
            usuario_id=usuario.id,
            cpf=formatar_cpf(cpf_limpo),
            nome=dados['nome'],
            data_nascimento=data_nasc,
            sexo=dados['sexo'],
            telefone=dados.get('telefone'),
            endereco=dados.get('endereco'),
            plano_saude=dados.get('plano_saude'),
            alergias=dados.get('alergias'),
            medicamentos_uso=dados.get('medicamentos_uso'),
            historico_familiar=dados.get('historico_familiar')
        )
        
        db.session.add(paciente)
        db.session.commit()
        
        registrar_auditoria(
            usuario_id=usuario_id,
            acao='CREATE',
            tabela='pacientes',
            registro_id=paciente.id,
            dados_novos=json.dumps({
                'nome': paciente.nome,
                'cpf': paciente.cpf,
                'email': usuario.email
            })
        )
        
        criar_notificacao(
            usuario_id=usuario.id,
            titulo='Bem-vindo ao VidaPlus!',
            mensagem=f'Olá {paciente.nome}, seu cadastro foi realizado com sucesso!',
            tipo='sistema'
        )
        
        return jsonify({
            'mensagem': 'Paciente cadastrado com sucesso',
            'paciente': {
                'id': paciente.id,
                'nome': paciente.nome,
                'cpf': paciente.cpf,
                'email': usuario.email,
                'data_nascimento': paciente.data_nascimento.isoformat(),
                'sexo': paciente.sexo
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro interno do servidor: {str(e)}'}), 500

@pacientes_bp.route('/', methods=['GET'])
@jwt_required()
def listar_pacientes():
    """Endpoint para listar pacientes com filtros"""
    try:
        nome = request.args.get('nome', '').strip()
        cpf = request.args.get('cpf', '').strip()
        plano_saude = request.args.get('plano_saude', '').strip()
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 10)), 100)
        
        query = Paciente.query.join(Usuario)
        
        if nome:
            query = query.filter(Paciente.nome.ilike(f'%{nome}%'))
        
        if cpf:
            cpf_formatado = formatar_cpf(re.sub(r'[^0-9]', '', cpf))
            query = query.filter(Paciente.cpf == cpf_formatado)
        
        if plano_saude:
            query = query.filter(Paciente.plano_saude.ilike(f'%{plano_saude}%'))
        
        query = query.order_by(Paciente.nome)
        
        paginacao = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        pacientes = []
        for paciente in paginacao.items:
            pacientes.append({
                'id': paciente.id,
                'nome': paciente.nome,
                'cpf': paciente.cpf,
                'email': paciente.usuario.email,
                'data_nascimento': paciente.data_nascimento.isoformat(),
                'sexo': paciente.sexo,
                'telefone': paciente.telefone,
                'plano_saude': paciente.plano_saude,
                'ativo': paciente.usuario.ativo
            })
        
        return jsonify({
            'pacientes': pacientes,
            'paginacao': {
                'pagina_atual': page,
                'total_paginas': paginacao.pages,
                'total_registros': paginacao.total,
                'registros_por_pagina': per_page,
                'tem_proxima': paginacao.has_next,
                'tem_anterior': paginacao.has_prev
            }
        }), 200
        
    except Exception as e:
        return jsonify({'erro': f'Erro interno do servidor: {str(e)}'}), 500

@pacientes_bp.route('/<int:paciente_id>', methods=['GET'])
@jwt_required()
def buscar_paciente(paciente_id):
    """Endpoint para buscar um paciente específico"""
    try:
        paciente = Paciente.query.get(paciente_id)
        if not paciente:
            return jsonify({'erro': 'Paciente não encontrado'}), 404
        
        return jsonify({
            'paciente': {
                'id': paciente.id,
                'nome': paciente.nome,
                'cpf': paciente.cpf,
                'email': paciente.usuario.email,
                'data_nascimento': paciente.data_nascimento.isoformat(),
                'sexo': paciente.sexo,
                'telefone': paciente.telefone,
                'endereco': paciente.endereco,
                'plano_saude': paciente.plano_saude,
                'alergias': paciente.alergias,
                'medicamentos_uso': paciente.medicamentos_uso,
                'historico_familiar': paciente.historico_familiar,
                'ativo': paciente.usuario.ativo
            }
        }), 200
        
    except Exception as e:
        return jsonify({'erro': f'Erro interno do servidor: {str(e)}'}), 500

@pacientes_bp.route('/<int:paciente_id>', methods=['PUT'])
@jwt_required()
def atualizar_paciente(paciente_id):
    """Endpoint para atualizar dados de um paciente"""
    try:
        usuario_id = get_jwt_identity()
        paciente = Paciente.query.get(paciente_id)
        if not paciente:
            return jsonify({'erro': 'Paciente não encontrado'}), 404
        
        dados = request.get_json()
        if not dados:
            return jsonify({'erro': 'Dados não fornecidos'}), 400
        
        # Atualiza campos permitidos
        if 'nome' in dados:
            paciente.nome = dados['nome']
        if 'telefone' in dados:
            paciente.telefone = dados['telefone']
        if 'endereco' in dados:
            paciente.endereco = dados['endereco']
        if 'plano_saude' in dados:
            paciente.plano_saude = dados['plano_saude']
        if 'alergias' in dados:
            paciente.alergias = dados['alergias']
        if 'medicamentos_uso' in dados:
            paciente.medicamentos_uso = dados['medicamentos_uso']
        if 'historico_familiar' in dados:
            paciente.historico_familiar = dados['historico_familiar']
        
        db.session.commit()
        
        registrar_auditoria(
            usuario_id=usuario_id,
            acao='UPDATE',
            tabela='pacientes',
            registro_id=paciente.id,
            dados_novos=json.dumps(dados)
        )
        
        return jsonify({
            'mensagem': 'Paciente atualizado com sucesso',
            'paciente': {
                'id': paciente.id,
                'nome': paciente.nome,
                'telefone': paciente.telefone,
                'endereco': paciente.endereco,
                'plano_saude': paciente.plano_saude
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro interno do servidor: {str(e)}'}), 500

@pacientes_bp.route('/<int:paciente_id>', methods=['DELETE'])
@jwt_required()
def excluir_paciente(paciente_id):
    """Endpoint para excluir um paciente"""
    try:
        usuario_id = get_jwt_identity()
        paciente = Paciente.query.get(paciente_id)
        if not paciente:
            return jsonify({'erro': 'Paciente não encontrado'}), 404
        
        # Verifica se há consultas associadas
        if paciente.consultas:
            return jsonify({'erro': 'Não é possível excluir paciente com consultas associadas'}), 400
        
        dados_anteriores = json.dumps({
            'nome': paciente.nome,
            'cpf': paciente.cpf,
            'email': paciente.usuario.email
        })
        
        # Primeiro excluir notificações do usuário
        notificacoes = Notificacao.query.filter_by(usuario_id=paciente.usuario.id).all()
        for notificacao in notificacoes:
            db.session.delete(notificacao)
        
        db.session.delete(paciente)
        db.session.delete(paciente.usuario)
        db.session.commit()
        
        registrar_auditoria(
            usuario_id=usuario_id,
            acao='DELETE',
            tabela='pacientes',
            registro_id=paciente_id,
            dados_anteriores=dados_anteriores
        )
        
        return jsonify({'mensagem': 'Paciente excluído com sucesso'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro interno do servidor: {str(e)}'}), 500

# Blueprint para profissionais
profissionais_bp = Blueprint('profissionais', __name__)

@profissionais_bp.route('/', methods=['POST'])
@jwt_required()
def cadastrar_profissional():
    """Endpoint para cadastrar um novo profissional"""
    try:
        usuario_id = get_jwt_identity()
        dados = request.get_json()
        
        if not dados:
            return jsonify({'erro': 'Dados não fornecidos'}), 400
        
        campos_obrigatorios = ['email', 'senha', 'crm_coren', 'nome', 'especialidade']
        for campo in campos_obrigatorios:
            if campo not in dados or not dados[campo]:
                return jsonify({'erro': f'Campo {campo} é obrigatório'}), 400
        
        validacao_crm = validar_crm(dados['crm_coren'])
        if not validacao_crm['valido']:
            return jsonify({'erro': validacao_crm['mensagem']}), 400
        
        crm_limpo = re.sub(r'[^0-9]', '', dados['crm_coren'])
        if Profissional.query.filter_by(crm_coren=crm_limpo).first():
            return jsonify({'erro': 'CRM/COREN já cadastrado'}), 409
        
        if Usuario.query.filter_by(email=dados['email']).first():
            return jsonify({'erro': 'Email já está em uso'}), 409
        
        especialidades_validas = [
            'Cardiologia', 'Cardiologia Intervencionista', 'Pediatria', 'Ortopedia', 
            'Ginecologia', 'Clínico Geral', 'Neurologia', 'Dermatologia', 
            'Anestesiologia', 'Cirurgia Geral'
        ]
        if dados['especialidade'] not in especialidades_validas:
            return jsonify({'erro': 'Especialidade inválida'}), 400
        
        try:
            data_admissao = datetime.strptime(dados['data_admissao'], '%Y-%m-%d').date()
            if data_admissao > date.today():
                return jsonify({'erro': 'Data de admissão não pode ser futura'}), 400
        except ValueError:
            return jsonify({'erro': 'Formato de data inválido. Use YYYY-MM-DD'}), 400
        
        usuario = Usuario(
            email=dados['email'],
            tipo='profissional',
            ativo=True,
            data_criacao=datetime.utcnow()
        )
        usuario.set_senha(dados['senha'])
        
        db.session.add(usuario)
        db.session.flush()
        
        profissional = Profissional(
            usuario_id=usuario.id,
            crm_coren=crm_limpo,
            nome=dados['nome'],
            especialidade=dados['especialidade'],
            telefone=dados.get('telefone'),
            email_profissional=dados.get('email_profissional'),
            data_admissao=data_admissao
        )
        
        db.session.add(profissional)
        db.session.commit()
        
        registrar_auditoria(
            usuario_id=usuario_id,
            acao='CREATE',
            tabela='profissionais',
            registro_id=profissional.id,
            dados_novos=json.dumps({
                'nome': profissional.nome,
                'crm_coren': profissional.crm_coren,
                'email': usuario.email
            })
        )
        
        criar_notificacao(
            usuario_id=usuario.id,
            titulo='Bem-vindo ao VidaPlus!',
            mensagem=f'Olá {profissional.nome}, seu cadastro como profissional foi realizado com sucesso!',
            tipo='sistema'
        )
        
        return jsonify({
            'mensagem': 'Profissional cadastrado com sucesso',
            'profissional': {
                'id': profissional.id,
                'nome': profissional.nome,
                'crm_coren': profissional.crm_coren,
                'email': usuario.email,
                'especialidade': profissional.especialidade,
                'data_admissao': profissional.data_admissao.isoformat()
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro interno do servidor: {str(e)}'}), 500

@profissionais_bp.route('/', methods=['GET'])
@jwt_required()
def listar_profissionais():
    """Endpoint para listar profissionais com filtros"""
    try:
        nome = request.args.get('nome', '').strip()
        especialidade = request.args.get('especialidade', '').strip()
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 10)), 100)
        
        query = Profissional.query.join(Usuario)
        
        if nome:
            query = query.filter(Profissional.nome.ilike(f'%{nome}%'))
        
        if especialidade:
            query = query.filter(Profissional.especialidade.ilike(f'%{especialidade}%'))
        
        query = query.order_by(Profissional.nome)
        
        paginacao = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        profissionais = []
        for profissional in paginacao.items:
            profissionais.append({
                'id': profissional.id,
                'nome': profissional.nome,
                'crm_coren': profissional.crm_coren,
                'email': profissional.usuario.email,
                'especialidade': profissional.especialidade,
                'ativo': profissional.usuario.ativo
            })
        
        return jsonify({
            'profissionais': profissionais,
            'paginacao': {
                'pagina_atual': page,
                'total_paginas': paginacao.pages,
                'total_registros': paginacao.total,
                'registros_por_pagina': per_page,
                'tem_proxima': paginacao.has_next,
                'tem_anterior': paginacao.has_prev
            }
        }), 200
        
    except Exception as e:
        return jsonify({'erro': f'Erro interno do servidor: {str(e)}'}), 500

@profissionais_bp.route('/<int:profissional_id>', methods=['GET'])
@jwt_required()
def buscar_profissional(profissional_id):
    """Endpoint para buscar um profissional específico"""
    try:
        profissional = Profissional.query.get(profissional_id)
        if not profissional:
            return jsonify({'erro': 'Profissional não encontrado'}), 404
        
        return jsonify({
            'profissional': {
                'id': profissional.id,
                'nome': profissional.nome,
                'crm_coren': profissional.crm_coren,
                'email': profissional.usuario.email,
                'especialidade': profissional.especialidade,
                'telefone': profissional.telefone,
                'email_profissional': profissional.email_profissional,
                'data_admissao': profissional.data_admissao.isoformat(),
                'ativo': profissional.usuario.ativo
            }
        }), 200
        
    except Exception as e:
        return jsonify({'erro': f'Erro interno do servidor: {str(e)}'}), 500

@profissionais_bp.route('/<int:profissional_id>', methods=['PUT'])
@jwt_required()
def atualizar_profissional(profissional_id):
    """Endpoint para atualizar dados de um profissional"""
    try:
        usuario_id = get_jwt_identity()
        profissional = Profissional.query.get(profissional_id)
        if not profissional:
            return jsonify({'erro': 'Profissional não encontrado'}), 404
        
        dados = request.get_json()
        if not dados:
            return jsonify({'erro': 'Dados não fornecidos'}), 400
        
        # Atualiza campos permitidos
        if 'nome' in dados:
            profissional.nome = dados['nome']
        if 'especialidade' in dados:
            especialidades_validas = [
                'Cardiologia', 'Cardiologia Intervencionista', 'Pediatria', 'Ortopedia', 
                'Ginecologia', 'Clínico Geral', 'Neurologia', 'Dermatologia', 
                'Anestesiologia', 'Cirurgia Geral'
            ]
            if dados['especialidade'] not in especialidades_validas:
                return jsonify({'erro': 'Especialidade inválida'}), 400
            profissional.especialidade = dados['especialidade']
        if 'telefone' in dados:
            profissional.telefone = dados['telefone']
        if 'email_profissional' in dados:
            profissional.email_profissional = dados['email_profissional']
        
        db.session.commit()
        
        registrar_auditoria(
            usuario_id=usuario_id,
            acao='UPDATE',
            tabela='profissionais',
            registro_id=profissional.id,
            dados_novos=json.dumps(dados)
        )
        
        return jsonify({
            'mensagem': 'Profissional atualizado com sucesso',
            'profissional': {
                'id': profissional.id,
                'nome': profissional.nome,
                'crm_coren': profissional.crm_coren,
                'especialidade': profissional.especialidade,
                'telefone': profissional.telefone
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro interno do servidor: {str(e)}'}), 500

@profissionais_bp.route('/<int:profissional_id>', methods=['DELETE'])
@jwt_required()
def excluir_profissional(profissional_id):
    """Endpoint para excluir um profissional"""
    try:
        usuario_id = get_jwt_identity()
        profissional = Profissional.query.get(profissional_id)
        if not profissional:
            return jsonify({'erro': 'Profissional não encontrado'}), 404
        
        # Verifica se há consultas associadas
        if profissional.consultas:
            return jsonify({'erro': 'Não é possível excluir profissional com consultas associadas'}), 400
        
        dados_anteriores = json.dumps({
            'nome': profissional.nome,
            'crm_coren': profissional.crm_coren,
            'email': profissional.usuario.email
        })
        
        # Primeiro excluir notificações do usuário
        notificacoes = Notificacao.query.filter_by(usuario_id=profissional.usuario.id).all()
        for notificacao in notificacoes:
            db.session.delete(notificacao)
        
        db.session.delete(profissional)
        db.session.delete(profissional.usuario)
        db.session.commit()
        
        registrar_auditoria(
            usuario_id=usuario_id,
            acao='DELETE',
            tabela='profissionais',
            registro_id=profissional_id,
            dados_anteriores=dados_anteriores
        )
        
        return jsonify({'mensagem': 'Profissional excluído com sucesso'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro interno do servidor: {str(e)}'}), 500

# Blueprint para consultas
consultas_bp = Blueprint('consultas', __name__)

@consultas_bp.route('/', methods=['POST'])
@jwt_required()
def agendar_consulta():
    """Endpoint para agendar uma nova consulta"""
    try:
        usuario_id = get_jwt_identity()
        dados = request.get_json()
        
        if not dados:
            return jsonify({'erro': 'Dados não fornecidos'}), 400
        
        campos_obrigatorios = ['paciente_id', 'profissional_id', 'unidade_id', 'data_hora', 'tipo']
        for campo in campos_obrigatorios:
            if campo not in dados or not dados[campo]:
                return jsonify({'erro': f'Campo {campo} é obrigatório'}), 400
        
        paciente = Paciente.query.get(dados['paciente_id'])
        if not paciente:
            return jsonify({'erro': 'Paciente não encontrado'}), 404
        
        profissional = Profissional.query.get(dados['profissional_id'])
        if not profissional:
            return jsonify({'erro': 'Profissional não encontrado'}), 404
        
        unidade = Unidade.query.get(dados['unidade_id'])
        if not unidade:
            return jsonify({'erro': 'Unidade não encontrada'}), 404
        
        try:
            data_hora = datetime.strptime(dados['data_hora'], '%Y-%m-%dT%H:%M:%S').replace(tzinfo=timezone.utc)
            if data_hora < datetime.now(timezone.utc):
                return jsonify({'erro': 'Data e hora da consulta não podem ser no passado'}), 400
        except ValueError:
            return jsonify({'erro': 'Formato de data/hora inválido. Use YYYY-MM-DDTHH:MM:SS'}), 400
        
        consulta = Consulta(
            paciente_id=paciente.id,
            profissional_id=profissional.id,
            unidade_id=unidade.id,
            data_hora=data_hora,
            tipo=dados['tipo'],
            status='agendada',
            observacoes=dados.get('observacoes')
        )
        
        db.session.add(consulta)
        db.session.commit()
        
        registrar_auditoria(
            usuario_id=usuario_id,
            acao='CREATE',
            tabela='consultas',
            registro_id=consulta.id,
            dados_novos=json.dumps({
                'paciente_id': consulta.paciente_id,
                'profissional_id': consulta.profissional_id,
                'unidade_id': consulta.unidade_id,
                'data_hora': consulta.data_hora.isoformat(),
                'tipo': consulta.tipo,
                'status': consulta.status
            })
        )
        
        return jsonify({
            'mensagem': 'Consulta agendada com sucesso',
            'consulta': {
                'id': consulta.id,
                'paciente': paciente.nome,
                'profissional': profissional.nome,
                'unidade': unidade.nome,
                'data_hora': consulta.data_hora.isoformat(),
                'tipo': consulta.tipo,
                'status': consulta.status
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro interno do servidor: {str(e)}'}), 500

@consultas_bp.route('/', methods=['GET'])
@jwt_required()
def listar_consultas():
    """Endpoint para listar consultas com filtros"""
    try:
        paciente_id = request.args.get('paciente_id')
        profissional_id = request.args.get('profissional_id')
        unidade_id = request.args.get('unidade_id')
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        status = request.args.get('status')
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 10)), 100)
        
        query = Consulta.query.join(Paciente).join(Profissional).join(Unidade)
        
        if paciente_id:
            query = query.filter(Consulta.paciente_id == paciente_id)
        if profissional_id:
            query = query.filter(Consulta.profissional_id == profissional_id)
        if unidade_id:
            query = query.filter(Consulta.unidade_id == unidade_id)
        
        if data_inicio:
            try:
                data_inicio_dt = datetime.strptime(data_inicio, '%Y-%m-%d').date()
                query = query.filter(Consulta.data_hora >= datetime.combine(data_inicio_dt, datetime.min.time()))
            except ValueError:
                return jsonify({'erro': 'Formato de data de início inválido. Use YYYY-MM-DD'}), 400
        if data_fim:
            try:
                data_fim_dt = datetime.strptime(data_fim, '%Y-%m-%d').date()
                query = query.filter(Consulta.data_hora <= datetime.combine(data_fim_dt, datetime.max.time()))
            except ValueError:
                return jsonify({'erro': 'Formato de data de fim inválido. Use YYYY-MM-DD'}), 400
        
        if status:
            statuses_validos = ['agendada', 'realizada', 'cancelada']
            if status not in statuses_validos:
                return jsonify({'erro': 'Status de consulta inválido'}), 400
            query = query.filter(Consulta.status == status)
        
        query = query.order_by(Consulta.data_hora)
        
        paginacao = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        consultas = []
        for consulta in paginacao.items:
            consultas.append({
                'id': consulta.id,
                'paciente': consulta.paciente.nome,
                'profissional': consulta.profissional.nome,
                'unidade': consulta.unidade.nome,
                'data_hora': consulta.data_hora.isoformat(),
                'tipo': consulta.tipo,
                'status': consulta.status,
                'observacoes': consulta.observacoes,
                'link_telemedicina': consulta.link_telemedicina
            })
        
        return jsonify({
            'consultas': consultas,
            'paginacao': {
                'pagina_atual': page,
                'total_paginas': paginacao.pages,
                'total_registros': paginacao.total,
                'registros_por_pagina': per_page,
                'tem_proxima': paginacao.has_next,
                'tem_anterior': paginacao.has_prev
            }
        }), 200
        
    except Exception as e:
        return jsonify({'erro': f'Erro interno do servidor: {str(e)}'}), 500

@consultas_bp.route('/<int:consulta_id>', methods=['GET'])
@jwt_required()
def buscar_consulta(consulta_id):
    """Endpoint para buscar uma consulta específica"""
    try:
        consulta = Consulta.query.get(consulta_id)
        if not consulta:
            return jsonify({'erro': 'Consulta não encontrada'}), 404
        
        return jsonify({
            'consulta': {
                'id': consulta.id,
                'paciente': consulta.paciente.nome,
                'profissional': consulta.profissional.nome,
                'unidade': consulta.unidade.nome,
                'data_hora': consulta.data_hora.isoformat(),
                'tipo': consulta.tipo,
                'status': consulta.status,
                'observacoes': consulta.observacoes,
                'link_telemedicina': consulta.link_telemedicina
            }
        }), 200
        
    except Exception as e:
        return jsonify({'erro': f'Erro interno do servidor: {str(e)}'}), 500

@consultas_bp.route('/<int:consulta_id>', methods=['PUT'])
@jwt_required()
def atualizar_consulta(consulta_id):
    """Endpoint para atualizar dados de uma consulta"""
    try:
        usuario_id = get_jwt_identity()
        consulta = Consulta.query.get(consulta_id)
        if not consulta:
            return jsonify({'erro': 'Consulta não encontrada'}), 404
        
        dados = request.get_json()
        if not dados:
            return jsonify({'erro': 'Dados não fornecidos'}), 400
        
        # Atualiza campos permitidos
        if 'data_hora' in dados:
            try:
                data_hora = datetime.strptime(dados['data_hora'], '%Y-%m-%dT%H:%M:%S').replace(tzinfo=timezone.utc)
                if data_hora < datetime.now(timezone.utc):
                    return jsonify({'erro': 'Data e hora da consulta não podem ser no passado'}), 400
                consulta.data_hora = data_hora
            except ValueError:
                return jsonify({'erro': 'Formato de data/hora inválido. Use YYYY-MM-DDTHH:MM:SS'}), 400
        
        if 'tipo' in dados:
            tipos_validos = ['presencial', 'telemedicina']
            if dados['tipo'] not in tipos_validos:
                return jsonify({'erro': 'Tipo de consulta inválido'}), 400
            consulta.tipo = dados['tipo']
        
        if 'status' in dados:
            statuses_validos = ['agendada', 'realizada', 'cancelada']
            if dados['status'] not in statuses_validos:
                return jsonify({'erro': 'Status de consulta inválido'}), 400
            consulta.status = dados['status']
        
        if 'observacoes' in dados:
            consulta.observacoes = dados['observacoes']
        
        db.session.commit()
        
        registrar_auditoria(
            usuario_id=usuario_id,
            acao='UPDATE',
            tabela='consultas',
            registro_id=consulta.id,
            dados_novos=json.dumps(dados)
        )
        
        return jsonify({
            'mensagem': 'Consulta atualizada com sucesso',
            'consulta': {
                'id': consulta.id,
                'data_hora': consulta.data_hora.isoformat(),
                'tipo': consulta.tipo,
                'status': consulta.status,
                'observacoes': consulta.observacoes
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro interno do servidor: {str(e)}'}), 500

@consultas_bp.route('/<int:consulta_id>', methods=['DELETE'])
@jwt_required()
def excluir_consulta(consulta_id):
    """Endpoint para excluir uma consulta"""
    try:
        usuario_id = get_jwt_identity()
        consulta = Consulta.query.get(consulta_id)
        if not consulta:
            return jsonify({'erro': 'Consulta não encontrada'}), 404
        
        dados_anteriores = json.dumps({
            'paciente_id': consulta.paciente_id,
            'profissional_id': consulta.profissional_id,
            'data_hora': consulta.data_hora.isoformat(),
            'tipo': consulta.tipo,
            'status': consulta.status
        })
        
        db.session.delete(consulta)
        db.session.commit()
        
        registrar_auditoria(
            usuario_id=usuario_id,
            acao='DELETE',
            tabela='consultas',
            registro_id=consulta_id,
            dados_anteriores=dados_anteriores
        )
        
        return jsonify({'mensagem': 'Consulta excluída com sucesso'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro interno do servidor: {str(e)}'}), 500

# Blueprint para receitas (prescrições)
receitas_bp = Blueprint('receitas', __name__)

@receitas_bp.route('/', methods=['POST'])
@jwt_required()
def criar_prescricao():
    """Endpoint para criar uma nova prescrição"""
    try:
        usuario_id = get_jwt_identity()
        dados = request.get_json()
        
        if not dados:
            return jsonify({'erro': 'Dados não fornecidos'}), 400
        
        campos_obrigatorios = ['paciente_id', 'profissional_id', 'medicamentos', 'dosagem']
        for campo in campos_obrigatorios:
            if campo not in dados or not dados[campo]:
                return jsonify({'erro': f'Campo {campo} é obrigatório'}), 400
        
        paciente = Paciente.query.get(dados['paciente_id'])
        if not paciente:
            return jsonify({'erro': 'Paciente não encontrado'}), 404
        
        profissional = Profissional.query.get(dados['profissional_id'])
        if not profissional:
            return jsonify({'erro': 'Profissional não encontrado'}), 404
        
        prescricao = Prescricao(
            paciente_id=paciente.id,
            profissional_id=profissional.id,
            medicamentos=dados['medicamentos'],
            dosagem=dados['dosagem'],
            duracao=dados.get('duracao'),
            observacoes=dados.get('observacoes'),
            status='ativa'
        )
        
        db.session.add(prescricao)
        db.session.commit()
        
        registrar_auditoria(
            usuario_id=usuario_id,
            acao='CREATE',
            tabela='prescricoes',
            registro_id=prescricao.id,
            dados_novos=json.dumps({
                'paciente_id': prescricao.paciente_id,
                'profissional_id': prescricao.profissional_id,
                'medicamentos': prescricao.medicamentos,
                'dosagem': prescricao.dosagem,
                'duracao': prescricao.duracao,
                'status': prescricao.status
            })
        )
        
        return jsonify({
            'mensagem': 'Prescrição criada com sucesso',
            'prescricao': {
                'id': prescricao.id,
                'paciente': paciente.nome,
                'profissional': profissional.nome,
                'medicamentos': prescricao.medicamentos,
                'dosagem': prescricao.dosagem,
                'duracao': prescricao.duracao,
                'status': prescricao.status
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro interno do servidor: {str(e)}'}), 500

@receitas_bp.route('/', methods=['GET'])
@jwt_required()
def listar_prescricoes():
    """Endpoint para listar prescrições com filtros"""
    try:
        paciente_id = request.args.get('paciente_id')
        profissional_id = request.args.get('profissional_id')
        status = request.args.get('status')
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 10)), 100)
        
        query = Prescricao.query.join(Paciente).join(Profissional)
        
        if paciente_id:
            query = query.filter(Prescricao.paciente_id == paciente_id)
        if profissional_id:
            query = query.filter(Prescricao.profissional_id == profissional_id)
        
        if status:
            statuses_validos = ['ativa', 'encerrada']
            if status not in statuses_validos:
                return jsonify({'erro': 'Status de prescrição inválido'}), 400
            query = query.filter(Prescricao.status == status)
        
        query = query.order_by(Prescricao.data_prescricao)
        
        paginacao = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        prescricoes = []
        for prescricao in paginacao.items:
            prescricoes.append({
                'id': prescricao.id,
                'paciente': prescricao.paciente.nome,
                'profissional': prescricao.profissional.nome,
                'medicamentos': prescricao.medicamentos,
                'dosagem': prescricao.dosagem,
                'duracao': prescricao.duracao,
                'status': prescricao.status,
                'data_prescricao': prescricao.data_prescricao.isoformat()
            })
        
        return jsonify({
            'prescricoes': prescricoes,
            'paginacao': {
                'pagina_atual': page,
                'total_paginas': paginacao.pages,
                'total_registros': paginacao.total,
                'registros_por_pagina': per_page,
                'tem_proxima': paginacao.has_next,
                'tem_anterior': paginacao.has_prev
            }
        }), 200
        
    except Exception as e:
        return jsonify({'erro': f'Erro interno do servidor: {str(e)}'}), 500

@receitas_bp.route('/<int:prescricao_id>', methods=['GET'])
@jwt_required()
def buscar_prescricao(prescricao_id):
    """Endpoint para buscar uma prescrição específica"""
    try:
        prescricao = Prescricao.query.get(prescricao_id)
        if not prescricao:
            return jsonify({'erro': 'Prescrição não encontrada'}), 404
        
        return jsonify({
            'prescricao': {
                'id': prescricao.id,
                'paciente': prescricao.paciente.nome,
                'profissional': prescricao.profissional.nome,
                'medicamentos': prescricao.medicamentos,
                'dosagem': prescricao.dosagem,
                'duracao': prescricao.duracao,
                'observacoes': prescricao.observacoes,
                'status': prescricao.status,
                'data_prescricao': prescricao.data_prescricao.isoformat()
            }
        }), 200
        
    except Exception as e:
        return jsonify({'erro': f'Erro interno do servidor: {str(e)}'}), 500

@receitas_bp.route('/<int:prescricao_id>', methods=['PUT'])
@jwt_required()
def atualizar_prescricao(prescricao_id):
    """Endpoint para atualizar dados de uma prescrição"""
    try:
        usuario_id = get_jwt_identity()
        prescricao = Prescricao.query.get(prescricao_id)
        if not prescricao:
            return jsonify({'erro': 'Prescrição não encontrada'}), 404
        
        dados = request.get_json()
        if not dados:
            return jsonify({'erro': 'Dados não fornecidos'}), 400
        
        # Atualiza campos permitidos
        if 'medicamentos' in dados:
            prescricao.medicamentos = dados['medicamentos']
        if 'dosagem' in dados:
            prescricao.dosagem = dados['dosagem']
        if 'duracao' in dados:
            prescricao.duracao = dados['duracao']
        if 'observacoes' in dados:
            prescricao.observacoes = dados['observacoes']
        if 'status' in dados:
            statuses_validos = ['ativa', 'encerrada']
            if dados['status'] not in statuses_validos:
                return jsonify({'erro': 'Status de prescrição inválido'}), 400
            prescricao.status = dados['status']
        
        db.session.commit()
        
        registrar_auditoria(
            usuario_id=usuario_id,
            acao='UPDATE',
            tabela='prescricoes',
            registro_id=prescricao.id,
            dados_novos=json.dumps(dados)
        )
        
        return jsonify({
            'mensagem': 'Prescrição atualizada com sucesso',
            'prescricao': {
                'id': prescricao.id,
                'medicamentos': prescricao.medicamentos,
                'dosagem': prescricao.dosagem,
                'duracao': prescricao.duracao,
                'observacoes': prescricao.observacoes,
                'status': prescricao.status
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro interno do servidor: {str(e)}'}), 500

@receitas_bp.route('/<int:prescricao_id>', methods=['DELETE'])
@jwt_required()
def excluir_prescricao(prescricao_id):
    """Endpoint para excluir uma prescrição"""
    try:
        usuario_id = get_jwt_identity()
        prescricao = Prescricao.query.get(prescricao_id)
        if not prescricao:
            return jsonify({'erro': 'Prescrição não encontrada'}), 404
        
        dados_anteriores = json.dumps({
            'paciente_id': prescricao.paciente_id,
            'profissional_id': prescricao.profissional_id,
            'medicamentos': prescricao.medicamentos,
            'dosagem': prescricao.dosagem,
            'status': prescricao.status
        })
        
        db.session.delete(prescricao)
        db.session.commit()
        
        registrar_auditoria(
            usuario_id=usuario_id,
            acao='DELETE',
            tabela='prescricoes',
            registro_id=prescricao_id,
            dados_anteriores=dados_anteriores
        )
        
        return jsonify({'mensagem': 'Prescrição excluída com sucesso'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': f'Erro interno do servidor: {str(e)}'}), 500

# =============================================================================
# CONFIGURAÇÃO DA APLICAÇÃO FLASK
# =============================================================================

def create_app():
    """Função factory para criar e configurar a aplicação Flask"""
    
    # Criação da instância Flask
    app = Flask(__name__)
    
    # Configurações da aplicação
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'chave-secreta-padrao-vidaplus-2024')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///vidaplus.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Configurações do JWT (JSON Web Tokens)
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-vidaplus-2024')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)  # 24 horas
    app.config['JWT_TOKEN_LOCATION'] = ['headers']
    app.config['JWT_HEADER_NAME'] = 'Authorization'
    app.config['JWT_HEADER_TYPE'] = 'Bearer'
    
    # Inicialização das extensões com a aplicação
    db.init_app(app)
    jwt.init_app(app)
    bcrypt.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Registro dos blueprints na aplicação
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(pacientes_bp, url_prefix='/api/pacientes')
    app.register_blueprint(profissionais_bp, url_prefix='/api/profissionais')
    app.register_blueprint(consultas_bp, url_prefix='/api/consultas')
    app.register_blueprint(receitas_bp, url_prefix='/api/receitas')
    
    # Adicionar os demais blueprints aqui quando implementados
    # app.register_blueprint(administracao_bp, url_prefix='/api/administracao')
    # app.register_blueprint(telemedicina_bp, url_prefix='/api/telemedicina')
    # app.register_blueprint(relatorios_bp, url_prefix='/api/relatorios')
    
    # Rota principal da aplicação
    @app.route('/')
    def home():
        """Rota principal que retorna informações sobre o sistema"""
        return jsonify({
            'sistema': 'VidaPlus - Sistema de Gestão Hospitalar e de Serviços de Saúde',
            'versao': '1.0.0',
            'status': 'ativo',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'endpoints': {
                'autenticacao': '/api/auth',
                'pacientes': '/api/pacientes',
                'profissionais': '/api/profissionais',
                'administracao': '/api/administracao',
                'telemedicina': '/api/telemedicina',
                'relatorios': '/api/relatorios'
            },
            'documentacao': {
                'login': 'POST /api/auth/login',
                'registro': 'POST /api/auth/registro',
                'perfil': 'GET /api/auth/perfil (requer token)',
                'health_check': 'GET /api/health'
            }
        })
    
    # Rota de verificação de saúde da API
    @app.route('/api/health')
    def health_check():
        """Endpoint para verificar se a API está funcionando corretamente"""
        return jsonify({
            'status': 'healthy',
            'message': 'API VidaPlus funcionando corretamente',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'database': 'connected' if db.engine.pool.checkedin() >= 0 else 'disconnected'
        })
    
    # Rota de teste para CORS
    @app.route('/api/test')
    def test_cors():
        """Endpoint de teste para verificar se o CORS está funcionando"""
        return jsonify({
            'message': 'CORS está funcionando corretamente',
            'method': request.method,
            'headers': dict(request.headers),
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
    
    # Rota para recriar o banco de dados (apenas para desenvolvimento)
    @app.route('/api/recreate-db', methods=['POST'])
    def recreate_database():
        """Endpoint para recriar o banco de dados do zero (desenvolvimento)"""
        try:
            print("🗑️ Limpando banco de dados...")
            db.drop_all()
            print("📊 Recriando tabelas...")
            db.create_all()
            print("🌱 Criando dados iniciais...")
            criar_dados_iniciais()
            print("✅ Banco de dados recriado com sucesso!")
            
            return jsonify({
                'message': 'Banco de dados recriado com sucesso',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'status': 'success'
            }), 200
        except Exception as e:
            print(f"❌ Erro ao recriar banco: {e}")
            return jsonify({
                'error': 'Erro ao recriar banco de dados',
                'message': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }), 500
    
    # Manipuladores de erro
    @app.errorhandler(404)
    def not_found(error):
        """Manipulador para erros 404 (página não encontrada)"""
        return jsonify({
            'error': 'Endpoint não encontrado',
            'message': 'A rota solicitada não existe',
            'status_code': 404,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Manipulador para erros 500 (erro interno do servidor)"""
        return jsonify({
            'error': 'Erro interno do servidor',
            'message': 'Ocorreu um erro inesperado',
            'status_code': 500,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 500
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        """Manipulador para erros 405 (método não permitido)"""
        return jsonify({
            'error': 'Método não permitido',
            'message': 'O método HTTP usado não é suportado para este endpoint',
            'status_code': 405,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 405
    
    @app.errorhandler(422)
    def unprocessable_entity(error):
        """Manipulador para erros 422 (entidade não processável)"""
        return jsonify({
            'error': 'Entidade não processável',
            'message': 'Os dados fornecidos não puderam ser processados',
            'status_code': 422,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 422
    
    return app

# Criação da aplicação
app = create_app()

# Importação dos modelos e função de criação de dados iniciais
# Importa os modelos após a criação da aplicação para evitar problemas de contexto
with app.app_context():
    # Importa os modelos dentro do contexto da aplicação
    # Criação das tabelas e dados iniciais quando a aplicação é executada
    """
    Contexto da aplicação para inicialização do banco de dados
    
    Este bloco é executado quando a aplicação é iniciada e:
    1. Cria todas as tabelas do banco de dados baseadas nos modelos
    2. Popula o banco com dados iniciais (usuário admin, unidade padrão)
    3. Garante que o sistema esteja pronto para uso
    """
    try:
        db.create_all()  # Cria todas as tabelas definidas nos modelos
        criar_dados_iniciais()  # Popula o banco com dados iniciais
        print("✅ Banco de dados inicializado com sucesso!")
    except Exception as e:
        print(f"⚠️ Erro ao inicializar banco de dados: {e}")

# Execução da aplicação
if __name__ == '__main__':
    """
    Ponto de entrada da aplicação
    
    Quando este arquivo é executado diretamente (não importado):
    1. A aplicação Flask é iniciada
    2. O servidor de desenvolvimento é iniciado na porta 5000
    3. O modo debug é ativado para facilitar o desenvolvimento
    """
    print("🚀 Iniciando servidor VidaPlus...")
    print("📊 API disponível em: http://localhost:5000")
    print("🔍 Health check: http://localhost:5000/api/health")
    print("📝 Documentação: http://localhost:5000/")
    app.run(debug=True, host='0.0.0.0', port=5000) 