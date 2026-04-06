from flask import jsonify, request, make_response, render_template
from funcao import senha_forte, enviando_email, gerar_token, verificar_existente, senha_correspondente, senha_antiga, decodificar_token
from flask_bcrypt import generate_password_hash, check_password_hash
from main import app
from db import conexao
import threading
import os
import datetime
from random import randint


# Criar usuário
@app.route('/criar_usuarios', methods=['POST'])
def criar_usuarios():
    # Pega as informações do body. Utilizamos o request.form.get visto que ele
    # permite colocar um valor para caso o usuário não preencha esse campo
    nome = request.form.get('nome', None)
    email = request.form.get('email', None)
    cpf_cnpj = request.form.get('cpf_cnpj', None)
    telefone = request.form.get('telefone', None)
    descricao_breve = request.form.get('descricao_breve', None)
    descricao_longa = request.form.get('descricao_longa', None)
    cod_banco = request.form.get('cod_banco', None)
    num_agencia = request.form.get('num_agencia', None)
    num_conta = request.form.get('num_conta', None)
    tipo_conta = request.form.get('tipo_conta', None)
    chave_pix = request.form.get('chave_pix', None)
    categoria = request.form.get('categoria', None)
    localizacao = request.form.get('localizacao', None)
    senha = request.form.get('senha')
    confirmar_senha = request.form.get('confirmar_senha')

    # Tipo 0 - ADM
    # Tipo 1 - Doador
    # Tipo 2 - ONG
    tipo = request.form.get('tipo', 1)

    foto_perfil = request.files.get('foto_perfil')

    # Armazena a data e horário que o usuário se cadastrou
    data_cadastro = datetime.datetime.now()

    # Define que o usuário, por padrão, está ativo
    ativo = 1

    # Define que o usuário de ONG, ainda não foi aprovado
    if tipo == 2:
        aprovacao = 0
    else:
        aprovacao = None

    # Define que o usuário, por padrão, não confirmou o e-mail
    email_confirmacao = 0

    # Temos uma função para a conexão com o banco -> Precisamos chamá-la
    con = conexao()

    # Abrir o cursor
    cur = con.cursor()

    try:
        # Verifica se o usuário está logado (decodificar é false)
        # e se ele não é adm (tipo 0)
        if decodificar_token() != False and decodificar_token()['tipo'] != 0:
            return jsonify({'error': 'Você não pode estar logado para criar um novo usuário'})

        # Verifica se o nome está vazio
        if nome == None:
            return jsonify({"error": "Nome é uma informação obrigatória."}), 400

        nome_sem_espacos = nome.strip()
        if nome_sem_espacos == '':
            return jsonify({"error": "Nome é uma informação obrigatória."}), 400

        # Verifica se o CPF/CNPJ está vazio
        if cpf_cnpj == None:
            return jsonify({"error": "CPF/CNPJ é uma informação obrigatória."}), 400

        cpf_cnpj_sem_espacos = cpf_cnpj.strip()
        if cpf_cnpj_sem_espacos == '':
            return jsonify({"error": "CPF/CNPJ é uma informação obrigatória."}), 400

        # Verifica se o email está vazio
        if email == None:
            return jsonify({"error": "E-mail é uma informação obrigatória."}), 400

        email_sem_espacos = email.strip()
        if email_sem_espacos == '':
            return jsonify({"error": "E-mail é uma informação obrigatória."}), 400

        # Verifica se o CPF já está cadastrado
        if verificar_existente(cpf_cnpj, 1) == False:
            return jsonify({"error": "CPF ou CNPJ já cadastrado."}), 400

        # Verifica se o e-mail já está cadastrado
        if verificar_existente(email, 2) == False:
            return jsonify({"error": "E-mail já cadastrado"}), 40

        # Verifica se a senha é forte
        if senha_forte(senha) == False:
            return jsonify({
                               "error": "Senha fraca. A senha deve conter pelo menos 8 caracteres, incluindo letras maiúsculas, minúsculas, números e caracteres especiais."}), 400

        # Verifica se as senhas digitadas correspondem
        if senha_correspondente(senha, confirmar_senha) == False:
            return jsonify({"error": "Senhas não correspondem."}), 400

        # Criptografa a senha
        senha_cripto = generate_password_hash(senha).decode('utf-8')

        # Gera um código de confirmação de e-mail
        codigo_confirmacao = randint(100000, 999999)

        # Define como 0 o número de tentativas de login
        tentativa = 0

        # Insere o usuário no banco de dados
        cur.execute("""INSERT INTO USUARIOS (NOME, EMAIL, SENHA, CPF_CNPJ, TELEFONE,
                                             DESCRICAO_BREVE, DESCRICAO_LONGA,
                                             APROVACAO, COD_BANCO, NUM_AGENCIA, NUM_CONTA,
                                             TIPO_CONTA, CHAVE_PIX, CATEGORIA, ATIVO, LOCALIZACAO,
                                             TIPO, DATA_CADASTRO, EMAIL_CONFIRMACAO, CODIGO_CONFIRMACAO, TENTATIVA)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) RETURNING ID_USUARIOS""",
                    (nome, email, senha_cripto, cpf_cnpj, telefone, descricao_breve,
                     descricao_longa, aprovacao, cod_banco, num_agencia, num_conta, tipo_conta,
                     chave_pix, categoria, ativo, localizacao, tipo, data_cadastro, email_confirmacao,
                     codigo_confirmacao, tentativa))

        # Recupera o ID do usuário recém criado
        codigo_usuarios = cur.fetchone()[0]

        con.commit()

        caminho_imagem_destino = None

        # Verifica se foi enviada uma foto de perfil
        if foto_perfil:
            # Define o nome da imagem com base no ID do usuário
            nome_imagem = f'{codigo_usuarios}.jpeg'

            # Define a pasta de destino
            caminho_imagem_destino = os.path.join(app.config['UPLOAD_FOLDER'], "Usuários")

            # Cria a pasta caso não exista
            os.makedirs(caminho_imagem_destino, exist_ok=True)

            # Define o caminho completo da imagem
            caminho_imagem = os.path.join(caminho_imagem_destino, nome_imagem)

            # Salva a imagem no diretório
            foto_perfil.save(caminho_imagem)

        # Define assunto e mensagem do e-mail
        assunto = 'Código de Confirmação de E-mail'
        mensagem = 'Bem-vindo(a) à Doar +! Para prosseguir, é necessário confirmar seu e-mail'
        codigo = codigo_confirmacao

        # Renderiza o template HTML do e-mail
        html = render_template('template_email.html', mensagem=mensagem, codigo=codigo)

        # Envia o e-mail em uma thread separada
        threading.Thread(target=enviando_email,
                         args=(email, assunto, html)
                         ).start()

        # Retorna sucesso com os dados do usuário
        return jsonify({'message': "Usuário cadastrado com sucesso",
                            'usuario': {
                                'tipo': tipo,
                                'nome': nome,
                                'email': email,
                                'cpf_cnpj': cpf_cnpj,
                                'telefone': telefone,
                                'descricao_breve': descricao_breve,
                                'descricao_longa': descricao_longa,
                                'cod_banco': cod_banco,
                                'num_agencia': num_agencia,
                                'num_conta': num_conta,
                                'tipo_conta': tipo_conta,
                                'chave_pix': chave_pix,
                                'categoria': categoria,
                                'localizacao': localizacao
                            }
                            }), 201
    except Exception as e:
        return jsonify({'message': f'Erro ao consultar o banco de dados: {e}'}), 500
    finally:
        cur.close()
        con.close()


@app.route('/editar_usuarios/<int:id_usuarios>', methods=['PUT'])
def editar_usuarios(id_usuarios):
    # Cria a conexão com o banco
    con = conexao()

    # Abre o cursor
    cur = con.cursor()

    try:
        # Verifica se o token existe
        if decodificar_token() == False:
            return jsonify({'error': 'Token necessário'}), 401

        # Verifica se o usuário é o dono da conta ou administrador
        if decodificar_token()['id_usuarios'] != id_usuarios and decodificar_token()['tipo'] != 0:
            return jsonify({'error': 'Token necessário'}), 401

        # Busca os dados atuais do usuário
        cur.execute("""SELECT ID_USUARIOS,
                              NOME,
                              EMAIL,
                              SENHA,
                              CPF_CNPJ,
                              TELEFONE,
                              DESCRICAO_BREVE,
                              DESCRICAO_LONGA,
                              APROVACAO,
                              COD_BANCO,
                              NUM_AGENCIA,
                              NUM_CONTA,
                              TIPO_CONTA,
                              CHAVE_PIX,
                              CATEGORIA,
                              ATIVO,
                              LOCALIZACAO,
                              TIPO,
                              DATA_CADASTRO,
                              EMAIL_CONFIRMACAO,
                              CODIGO_CONFIRMACAO,
                              TENTATIVA
                       FROM USUARIOS
                       WHERE ID_USUARIOS = ?""", (id_usuarios,))

        # Armazena o resultado
        tem_usuario = cur.fetchone()

        # Verifica se o usuário existe
        if tem_usuario == None:
            return jsonify({"error": "Usuário não encontrado"}), 404

        # Pega os dados enviados ou mantém os atuais
        nome = request.form.get('nome', tem_usuario[1])
        email = request.form.get('email', tem_usuario[2])
        cpf_cnpj = request.form.get('cpf_cnpj', tem_usuario[4])
        telefone = request.form.get('telefone', tem_usuario[5])
        descricao_breve = request.form.get('descricao_breve', tem_usuario[6])
        descricao_longa = request.form.get('descricao_longa', tem_usuario[7])
        aprovacao = tem_usuario[8]
        cod_banco = request.form.get('cod_banco', tem_usuario[9])
        num_agencia = request.form.get('num_agencia', tem_usuario[10])
        num_conta = request.form.get('num_conta', tem_usuario[11])
        tipo_conta = request.form.get('tipo_conta', tem_usuario[12])
        chave_pix = request.form.get('chave_pix', tem_usuario[13])
        categoria = request.form.get('categoria', tem_usuario[14])
        ativo = tem_usuario[15]
        localizacao = request.form.get('localizacao', tem_usuario[16])
        senha = request.form.get('senha', None)
        confirmar_senha = request.form.get('confirmar_senha', None)
        foto_perfil = request.files.get('foto_perfil')
        tipo = tem_usuario[17]
        data_cadastro = tem_usuario[18]
        email_confirmacao = tem_usuario[19]
        codigo_confirmacao = tem_usuario[20]
        tentativa = tem_usuario[21]

        # Verifica se o nome está vazio
        nome_sem_espacos = nome.strip()
        if nome_sem_espacos == '':
            return jsonify({"error": "Nome é uma informação obrigatória."}), 400

        # Verifica se o CPF/CNPJ está vazio
        cpf_cnpj_sem_espacos = cpf_cnpj.strip()
        if cpf_cnpj_sem_espacos == '':
            return jsonify({"error": "CPF/CNPJ é uma informação obrigatória."}), 400

        # Verifica se o email está vazio
        email_sem_espacos = email.strip()
        if email_sem_espacos == '':
            return jsonify({"error": "E-mail é uma informação obrigatória."}), 400

        # Verifica se CPF/CNPJ já existe (exceto o próprio usuário)
        if verificar_existente(cpf_cnpj, 1, id_usuarios) == False:
            return jsonify({"error": "CPF ou CNPJ já cadastrado."}), 400

        # Verifica se email já existe (exceto o próprio usuário)
        if verificar_existente(email, 2, id_usuarios) == False:
            return jsonify({"error": "E-mail já cadastrado"}, 400)

        # Verifica se foi enviada uma nova senha
        if senha != None:
            # Valida a força da senha
            if senha_forte(senha) == False:
                return jsonify({
                               "error": "Senha fraca. A senha deve conter pelo menos 8 caracteres, incluindo letras maiúsculas, minúsculas, números e caracteres especiais."}), 400

            # Verifica se as senhas correspondem
            if senha_correspondente(senha, confirmar_senha) == False:
                return jsonify({"error": "Senhas não correspondem."}), 400

            # Verifica se não é uma senha antiga
            if senha_antiga(id_usuarios, senha) == False:
                return jsonify({"error": "A senha nova não pode ser igual às últimas 3 utilizadas"}), 400

            # Criptografa a nova senha
            nova_senha_hash = generate_password_hash(senha).decode('utf-8')
        else:
            # Mantém a senha antiga
            nova_senha_hash = tem_usuario[3]

        # Se o email foi alterado, gera novo código de confirmação
        if email != tem_usuario[2]:
            codigo_confirmacao = randint(100000, 999999)
            email_confirmacao = 0

            # Define dados do e-mail
            assunto = 'Código de Confirmação de E-mail'
            mensagem = 'Percebemos que você alterou seu e-mail, por isso é necessário o confirmar novamente'
            codigo = codigo_confirmacao

            # Renderiza HTML do e-mail
            html = render_template('template_email.html', mensagem=mensagem, codigo=codigo)

            # Envia e-mail em thread separada
            threading.Thread(target=enviando_email,
                             args=(email, assunto, html)
                             ).start()

        # Atualiza os dados do usuário no banco
        cur.execute("""UPDATE USUARIOS
                       SET NOME               = ?,
                           EMAIL              = ?,
                           SENHA = ?,
                           CPF_CNPJ           = ?,
                           TELEFONE           = ?,
                           DESCRICAO_BREVE    = ?,
                           DESCRICAO_LONGA    = ?,
                           APROVACAO          = ?,
                           COD_BANCO          = ?,
                           NUM_AGENCIA        = ?,
                           NUM_CONTA          = ?,
                           TIPO_CONTA         = ?,
                           CHAVE_PIX          = ?,
                           CATEGORIA          = ?,
                           ATIVO             = ?,
                           LOCALIZACAO        = ?,
                           TIPO               = ?,
                           DATA_CADASTRO      = ?,
                           EMAIL_CONFIRMACAO  = ?,
                           CODIGO_CONFIRMACAO = ?,
                           TENTATIVA          = ?
                       WHERE ID_USUARIOS = ?""", (nome, email, nova_senha_hash, cpf_cnpj, telefone, descricao_breve,
                                                  descricao_longa, aprovacao, cod_banco, num_agencia, num_conta,
                                                  tipo_conta,
                                                  chave_pix, categoria, ativo, localizacao, tipo, data_cadastro,
                                                  email_confirmacao,
                                                  codigo_confirmacao, tentativa, id_usuarios))

        # Confirma a alteração no banco
        con.commit()

        # Inicializa o caminho da imagem
        caminho_imagem_destino = None

        # Verifica se foi enviada uma nova foto
        if foto_perfil:
            # Define nome da imagem
            nome_imagem = f'{id_usuarios}.jpeg'

            # Define diretório
            caminho_imagem_destino = os.path.join(app.config['UPLOAD_FOLDER'], "Usuários")

            # Cria diretório se não existir
            os.makedirs(caminho_imagem_destino, exist_ok=True)

            # Define caminho completo
            caminho_imagem = os.path.join(caminho_imagem_destino, nome_imagem)

            # Salva imagem
            foto_perfil.save(caminho_imagem)

        # Retorna sucesso
        return jsonify({'message': "Usuário editado com sucesso",
                        'usuario': {
                            'tipo': tipo,
                            'nome': nome,
                            'email': email,
                            'cpf_cnpj': cpf_cnpj,
                            'telefone': telefone,
                            'descricao_breve': descricao_breve,
                            'descricao_longa': descricao_longa,
                            'cod_banco': cod_banco,
                            'num_agencia': num_agencia,
                            'num_conta': num_conta,
                            'tipo_conta': tipo_conta,
                            'chave_pix': chave_pix,
                            'categoria': categoria,
                            'localizacao': localizacao
                        }
                        }), 201
    except Exception as e:
        return jsonify({'message': f'Erro ao consultar o banco de dados: {e}'}), 500
    finally:
        cur.close()
        con.close()


# Excluir usuário
@app.route('/deletar_usuarios/<int:id_usuarios>', methods=['DELETE'])
def deletar_usuarios(id_usuarios):
    # Cria a conexão com o banco
    con = conexao()

    # Abre o cursor
    cur = con.cursor()

    try:
        # Verifica se o token existe
        if decodificar_token() == False:
            return jsonify({'error': 'Token necessário'}), 401

        # Verifica se é administrador ou o próprio usuário
        if decodificar_token()['tipo'] != 0 and decodificar_token()['id_usuarios'] != id_usuarios:
            return jsonify({'error': 'É necessário ser administrador para isso'}), 401

        # Verifica se o usuário existe
        cur.execute("""SELECT ID_USUARIOS
                       FROM USUARIOS
                       WHERE ID_USUARIOS = ?""", (id_usuarios,))

        if not cur.fetchone():
            return jsonify({"error": "Usuário não encontrado"}), 404

        # Busca histórico de senhas do usuário
        cur.execute("""SELECT ID_HISTORICO_SENHA
                       FROM HISTORICO_SENHA 
                       WHERE ID_USUARIOS = ?""", (id_usuarios,))

        # Se existir histórico, remove um por um
        if cur.fetchall():
            id_senhas_antigas = cur.fetchall()
            for id in id_senhas_antigas:
                cur.execute("""DELETE FROM HISTORICO_SENHA 
                            where ID_HISTORICO_SENHA = ?""", (id,))
                con.commit()

        # Remove registros de recuperação de senha
        cur.execute("""DELETE FROM RECUPERACAO_SENHA
                    WHERE ID_USUARIOS = ?""", (id_usuarios,))

        con.commit()

        # Remove o usuário da tabela principal
        cur.execute("""DELETE
                       FROM USUARIOS
                       WHERE ID_USUARIOS = ?""", (id_usuarios,))

        con.commit()

        # Retorna sucesso
        return jsonify({"error": "Usuário excluído com sucesso"})

    except Exception as e:
        return jsonify({'message': f'Erro ao consultar o banco de dados: {e}'}), 500
    finally:
        cur.close()
        con.close()


# Ativar usuário
@app.route('/ativar_usuarios/<int:id_usuarios>', methods=['PUT'])
def ativar_usuarios(id_usuarios):
    # Cria conexão com o banco
    con = conexao()

    # Abre o cursor
    cur = con.cursor()

    try:
        # Verifica se o token existe
        if decodificar_token() == False:
            return jsonify({'error': 'Token necessário'}), 401

        # Apenas administrador pode ativar
        if decodificar_token()['tipo'] == 0:
            cur.execute("""UPDATE USUARIOS
                           SET ATIVO = 1
                           WHERE ID_USUARIOS = ?""", (id_usuarios, ))

            # Confirma alteração
            con.commit()

            return jsonify({'message': 'Usuário ativado com sucesso!'})

        return jsonify({'message': 'É necessário ser administrador'})
    finally:
        cur.close()
        con.close()


# Inativar usuário
@app.route('/inativar_usuarios/<int:id_usuarios>', methods=['PUT'])
def inativar_usuarios(id_usuarios):
    # Cria conexão
    con = conexao()

    # Abre cursor
    cur = con.cursor()

    try:
        # Verifica token
        if decodificar_token() == False:
            return jsonify({'error': 'Token necessário'}), 401

        # Verifica permissão
        if decodificar_token()['tipo'] != 0 and decodificar_token()['id_usuarios'] != id_usuarios:
            return jsonify({'error': 'É necessário ser administrador para isso'}), 401

        # Verifica se usuário existe
        cur.execute("""SELECT ID_USUARIOS
                       FROM USUARIOS
                       WHERE ID_USUARIOS = ?""", (id_usuarios,))

        if not cur.fetchone():
            return jsonify({"error": "Usuário não encontrado"}), 404

        # Atualiza status para inativo
        cur.execute("""UPDATE USUARIOS 
                       SET ATIVO  = 0
                       WHERE ID_USUARIOS = ?""", (id_usuarios,))

        # Confirma alteração
        con.commit()

        return jsonify({"message": "Usuário inativado com sucesso"})

    except Exception as e:
        return jsonify({'message': f'Erro ao consultar o banco de dados: {e}'}), 500
    finally:
        cur.close()
        con.close()


# Listar usuários
@app.route('/listar_usuarios', methods=['GET'])
def listar_usuarios():
    # Cria conexão
    con = conexao()

    # Abre cursor
    cur = con.cursor()

    try:
        # Verifica token
        if decodificar_token() == False:
            return jsonify({'error': 'Token necessário'}), 401

        # Apenas administrador pode listar
        if decodificar_token()['tipo'] != 0:
            return jsonify({'error': 'É necessário ser administrador para isso'}), 401

        # Busca todos os usuários
        cur.execute("""SELECT ID_USUARIOS,
                              NOME,
                              EMAIL,
                              SENHA,
                              CPF_CNPJ,
                              TELEFONE,
                              DESCRICAO_BREVE,
                              DESCRICAO_LONGA,
                              APROVACAO,
                              COD_BANCO,
                              NUM_AGENCIA,
                              NUM_CONTA,
                              TIPO_CONTA,
                              CHAVE_PIX,
                              CATEGORIA,
                              ATIVO,
                              LOCALIZACAO,
                              TIPO,
                              DATA_CADASTRO,
                              EMAIL_CONFIRMACAO,
                              CODIGO_CONFIRMACAO,
                              TENTATIVA
                       FROM USUARIOS""")

        # Armazena resultado
        usuarios = cur.fetchall()

        # Retorna lista se existir
        if usuarios:
            return jsonify({'usuarios': usuarios}), 200
        else:
            return jsonify({
                'error': 'Não foi possível encontrar usuários'
            }), 404

    except Exception as e:
        return jsonify({'message': f'Erro ao consultar o banco de dados: {e}'}), 500
    finally:
        cur.close()
        con.close()


# Buscar usuários por CPF/CNPJ
@app.route('/buscar_usuarios', methods=['GET'])
def buscar_usuarios():
    # Pega valor de busca
    cpf_cnpj = request.json.get('cpf_cnpj')

    # Cria conexão
    con = conexao()

    # Abre cursor
    cur = con.cursor()

    try:
        # Verifica token
        if decodificar_token() == False:
            return jsonify({'error': 'Token necessário'}), 401

        # Apenas administrador pode buscar
        if decodificar_token()['tipo'] != 0:
            return jsonify({'error': 'É necessário ser administrador para isso'}), 401

        # Adiciona o % antes e depois pra poder buscar mesmo se não for o valor completo
        valor_busca = f"%{cpf_cnpj}%"

        # Executa consulta
        cur.execute("""SELECT ID_USUARIOS,
                              NOME,
                              EMAIL,
                              SENHA,
                              CPF_CNPJ,
                              TELEFONE,
                              DESCRICAO_BREVE,
                              DESCRICAO_LONGA,
                              APROVACAO,
                              COD_BANCO,
                              NUM_AGENCIA,
                              NUM_CONTA,
                              TIPO_CONTA,
                              CHAVE_PIX,
                              CATEGORIA,
                              ATIVO,
                              LOCALIZACAO,
                              TIPO,
                              DATA_CADASTRO,
                              EMAIL_CONFIRMACAO,
                              CODIGO_CONFIRMACAO,
                              TENTATIVA
                       FROM USUARIOS
                       WHERE cpf_cnpj LIKE ?""", (valor_busca,))

        # Armazena resultado
        usuarios = cur.fetchall()

        # Retorna resultado
        if usuarios:
            return jsonify({'usuarios': usuarios}), 200
        else:
            return jsonify({
                'error': 'Não foi possível encontrar usuários com esse cpf/cnpj'
            }), 404

    except Exception as e:
        return jsonify({'message': f'Erro ao consultar o banco de dados: {e}'}), 500
    finally:
        cur.close()
        con.close()


# Login
# Login
@app.route('/login', methods=['POST'])
def login():
    # Pega os dados do formulário
    cpf_cnpj = request.json.get('cpf_cnpj')
    senha = request.json.get('senha')

    # Cria conexão com o banco
    con = conexao()

    # Abre cursor
    cur = con.cursor()

    try:
        # Verifica se já está logado
        if decodificar_token() != False:
            return jsonify({'error': 'É necessário estar deslogado para logar'}), 401

        # Busca o usuário pelo CPF/CNPJ
        cur.execute("""SELECT ID_USUARIOS,
                              TIPO,
                              NOME,
                              CPF_CNPJ,
                              SENHA,
                              TENTATIVA,
                              EMAIL_CONFIRMACAO,
                              ATIVO
                       FROM USUARIOS
                       WHERE CPF_CNPJ = ?""", (cpf_cnpj,))

        usuario = cur.fetchone()

        # Verifica se o usuário existe
        if not usuario:
            return jsonify({"error": "Usuário não encontrado"}), 404

        # Atribui valores
        id_usuarios = usuario[0]
        tipo = usuario[1]
        nome = usuario[2]
        senha_hash = usuario[4]
        tentativa = usuario[5]
        email_confirmacao = usuario[6]
        ativo = usuario[7]

        # Verifica se o usuário está bloqueado por tentativas
        if tentativa > 3 and tipo != 0:
            return jsonify(
                {"error": "Esse usuário está bloqueado! Entre em contato com o administrador"}
            ), 400

        # Verifica se o usuário está ativo
        if ativo == 0:
            return jsonify(
                {"error": "Esse usuário está inativado"}
            ), 400

        # Verifica se o e-mail foi confirmado
        if email_confirmacao == 0:
            return jsonify(
                {"error": "Verifique o e-mail antes de logar!"}
            ), 400

        # Verifica se a senha está correta
        if check_password_hash(senha_hash, senha):
            id_usuarios = usuario[0]

            # Se havia tentativas anteriores, zera
            if tentativa > 0:
                cur.execute("""UPDATE USUARIOS
                               SET TENTATIVA = 0
                               WHERE ID_USUARIOS = ?""", (id_usuarios,))
                con.commit()

            # Gera token de autenticação
            token = gerar_token(tipo, id_usuarios, 10)

            # Cria resposta com cookie
            resp = make_response(jsonify({'message': f'Bem-vindo {nome}!'}))

            # Define cookie com token
            resp.set_cookie('acess_token', token,
                            httponly=True,
                            secure=False,
                            samesite='Lax',
                            path="/",
                            max_age=3600)

            return resp

        # Se senha estiver incorreta, incrementa tentativas (exceto admin)
        if tipo != 0:
            tentativa = tentativa + 1
            cur.execute("""UPDATE USUARIOS
                           SET TENTATIVA = ?
                           WHERE ID_USUARIOS = ?""", (tentativa, id_usuarios))
            con.commit()

        return jsonify({"error": "Senha incorreta"}), 400

    except Exception as e:
        return jsonify({'message': f'Erro ao consultar o banco de dados: {e}'}), 500
    finally:
        cur.close()
        con.close()


# Logout
@app.route('/logout', methods=['POST'])
def logout():
    try:
        # Verifica se já está deslogado
        if decodificar_token() == False:
            return jsonify({'message': 'Você já está deslogado!'})

        # Cria resposta
        resp = make_response(jsonify({'message': f'Você deslogou!'}))

        # Remove o cookie do token
        resp.set_cookie(
            'acess_token',
            '',  # cookie vazio
            httponly=True,
            secure=False,
            samesite='Lax',
            path="/",
            max_age=0  # expira imediatamente
        )

        return resp

    except Exception as e:
        return jsonify({'message': f'Erro ao consultar o banco de dados: {e}'}), 500


# Desbloquear usuário
@app.route('/desbloquear_usuarios/<int:id_usuarios>', methods=['PUT'])
def desbloquear_usuarios(id_usuarios):
    # Cria conexão
    con = conexao()

    # Abre cursor
    cur = con.cursor()

    try:
        # Verifica token
        if decodificar_token() == False:
            return jsonify({'error': 'Token necessário'}), 401

        # Apenas administrador pode desbloquear
        if decodificar_token()['tipo'] == 0:
            tentativa = 0

            # Zera tentativas
            cur.execute("""UPDATE USUARIOS
                           SET TENTATIVA = ?
                           WHERE ID_USUARIOS = ?""", (tentativa, id_usuarios))

            con.commit()

            return jsonify({'message': 'Usuário desbloqueado com sucesso!'})

        return jsonify({'error': 'É necessário ser administrador'})
    finally:
        cur.close()
        con.close()


# Confirmar e-mail
@app.route('/confirmar_email', methods=['POST'])
def confirmar_email():
    # Pega código digitado
    codigo_digitado = (request.json.get('codigo_digitado'))

    # Cria conexão
    con = conexao()

    # Abre cursor
    cursor = con.cursor()

    # Verifica se código foi enviado
    if not codigo_digitado:
        return jsonify({'error': 'Preencha o código de confirmação'}), 400

    try:
        # Busca usuário pelo código
        cursor.execute('SELECT id_usuarios FROM usuarios WHERE codigo_confirmacao = ?', (str(codigo_digitado, ),))
        usuario = cursor.fetchone()

        # Verifica se código é válido
        if not usuario:
            return jsonify({'error': 'Código incorreto'}), 404

        id_usuarios = usuario[0]

        # Atualiza confirmação de e-mail
        cursor.execute('UPDATE usuarios SET email_confirmacao = 1, codigo_confirmacao = NULL WHERE id_usuarios = ?',
                       (id_usuarios, ))

        con.commit()

        return jsonify({'message': 'Email confirmado com sucesso!'}), 200

    except Exception as e:
        return jsonify({'error': f'Erro: {e}'})
    finally:
        cursor.close()
        con.close()


# Esqueci senha
@app.route('/esqueci_senha', methods=['POST'])
def esqueci_senha():
    # Pega e-mail
    email = request.json.get('email')

    # Verifica se foi enviado
    if not email:
        return jsonify({'message': "Por favor, envie o e-mail."}), 400

    # Cria conexão
    con = conexao()

    # Abre cursor
    cursor = con.cursor()

    try:
        # Busca usuário e verifica se está ativo
        cursor.execute("SELECT id_usuarios, NOME, ATIVO FROM usuarios WHERE EMAIL = ?", (email,))
        usuario = cursor.fetchone()

        # Verifica se usuário existe
        if not usuario:
            return jsonify({'message': "Usuário não encontrado"}), 404

        id_usuarios = usuario[0]
        nome = usuario[1]
        ativo = usuario[2]

        # Verifica se está ativo
        if ativo == 0:
            return jsonify({"error": "Esse usuário está inativado"}), 403

        # Busca código de recuperação existente
        cursor.execute("""SELECT CODIGO, DATA_EXPIRACAO
                          FROM RECUPERACAO_SENHA
                          WHERE ID_usuarios = ?""", (id_usuarios,))

        # Armazena resultado
        dados_recuperacao = cursor.fetchone()

        # Se já existir código válido, reutiliza
        if dados_recuperacao and dados_recuperacao[1] > datetime.datetime.now():
            codigo = dados_recuperacao[0]

            assunto = 'Código de Recuperação de Senha'
            mensagem = 'Recebemos uma solicitação para recuperar sua senha'

            html = render_template('template_email.html', mensagem=mensagem, codigo=codigo)

            # Reenvia código
            threading.Thread(target=enviando_email,
                             args=(email, assunto, html)
                             ).start()

            return jsonify({
                'message': "Percebemos que seu código ainda está ativo, por isso ele foi reenviado para o e-mail!"}), 200

        # Remove códigos antigos
        cursor.execute("DELETE FROM RECUPERACAO_SENHA WHERE id_usuarios = ?", (id_usuarios,))

        # Gera novo código
        codigo = randint(100000, 999999)

        # Define validade (30 minutos)
        validade = datetime.datetime.now() + datetime.timedelta(minutes=30)

        # Insere novo código
        cursor.execute("""
                       INSERT INTO RECUPERACAO_SENHA (id_usuarios, CODIGO, DATA_EXPIRACAO)
                       VALUES (?, ?, ?)
                       """, (id_usuarios, codigo, validade))

        con.commit()

        # Prepara envio de e-mail
        assunto = 'Código de Recuperação de Senha'
        mensagem = 'Recebemos uma solicitação para recuperar sua senha'

        html = render_template('template_email.html', mensagem=mensagem, codigo=codigo)

        # Envia e-mail
        threading.Thread(target=enviando_email,
                         args=(email, assunto, html)
                         ).start()

        return jsonify({'message': "Código enviado para o e-mail!"}), 200

    except Exception as e:
        con.rollback()
        return jsonify({'message': f"Erro interno: {e}"}), 500
    finally:
        cursor.close()
        con.close()


# Verificar código de recuperação
@app.route('/verificar_codigo', methods=['POST'])
def verificar_codigo():
    # Pega código digitado
    codigo_digitado = request.json.get('codigo_digitado')

    # Verifica se foi enviado
    if not codigo_digitado:
        return jsonify({'error': 'Preencha o código'}), 400

    # Cria conexão
    con = conexao()

    # Abre cursor
    cursor = con.cursor()

    try:
        # Busca código no banco
        cursor.execute('SELECT id_usuarios, data_expiracao FROM RECUPERACAO_SENHA WHERE codigo = ?', (codigo_digitado,))
        recuperacao = cursor.fetchone()

        # Verifica se código existe
        if not recuperacao:
            return jsonify({'error': 'Código incorreto!'}), 404

        id_usuarios = recuperacao[0]
        data_expiracao = recuperacao[1]

        # Verifica se código expirou
        if datetime.datetime.now() > data_expiracao:
            cursor.execute("DELETE FROM RECUPERACAO_SENHA WHERE id_usuarios = ?", (id_usuarios,))
            con.commit()
            return jsonify({'message': "Este código expirou. Solicite um novo."}), 400

        # Busca tipo do usuário
        cursor.execute("SELECT TIPO FROM USUARIOS WHERE ID_USUARIOS = ?", (id_usuarios,))
        tipo = cursor.fetchone()[0]

        # Gera token temporário
        token = gerar_token(tipo, id_usuarios, 5)

        # Cria resposta com cookie
        resp = make_response(jsonify({'message': f'Bem-vindo {nome}!'}))

        # Define cookie com token
        resp.set_cookie('acess_token', token,
                        httponly=True,
                        secure=False,
                        samesite='Lax',
                        path="/",
                        max_age=3600)

        return jsonify({'message': "Código correto! Você tem 5 minutos para alterar sua senha"}), 200

    except Exception as e:
        return jsonify({'error': f'Erro: {e}'}), 500
    finally:
        cursor.close()
        con.close()
