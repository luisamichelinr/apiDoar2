from flask import jsonify, request, make_response, render_template
from funcao import senha_forte, enviando_email, gerar_token, verificar_existente, senha_correspondente, senha_antiga, decodificar_token
from flask_bcrypt import generate_password_hash, check_password_hash
from main import app
from db import conexao
import threading
import os
import datetime
from random import randint


# Criar projeto
@app.route('/criar_projetos', methods=['POST'])
def criar_projetos():
    titulo = request.form.get('titulo', None)
    descricao = request.form.get('descricao', None)
    categoria = request.form.get('categoria', None)
    tipo_ajuda = request.form.get('tipo_ajuda', None)
    localizacao = request.form.get('localizacao', None)
    status = request.form.get('status', None)
    foto_projeto = request.files.get('foto_projeto')

    # Temos uma função para a conexão com o banco -> Precisamos chamá-la
    con = conexao()

    # Abrir o cursor
    cur = con.cursor()

    try:
        # if decodificar_token() == False:
        #     return jsonify({'error': 'Você precisa estar logado para criar um projeto'})
        #
        # if decodificar_token()['tipo'] == 1:
        #     return jsonify({'error': 'Doadores não podem criar projetos'})

        # Verifica se o título está vazio
        if titulo == None:
            return jsonify({"error": "Título é uma informação obrigatória."}), 400

        titulo_sem_espaços = titulo.strip()
        if titulo_sem_espaços == '':
            return jsonify({"error": "Título é uma informação obrigatória."}), 400

        id_usuarios = 14

        # Insere o usuário no banco de dados
        cur.execute("""INSERT INTO PROJETOS (ID_USUARIOS, TITULO, DESCRICAO, CATEGORIA, 
                                             STATUS, TIPO_AJUDA, LOCALIZACAO)
                       VALUES (?, ?, ?, ?, ?, ?, ?) RETURNING ID_PROJETOS""",
                    (id_usuarios, titulo, descricao, categoria, status, tipo_ajuda, localizacao))

        # Recupera o ID do usuário recém criado
        id_projetos = cur.fetchone()[0]

        con.commit()

        caminho_imagem_destino = None

        # Verifica se foi enviada uma foto de perfil
        if foto_projeto:
            # Define o nome da imagem com base no ID do usuário
            nome_imagem = f'{id_projetos}.jpeg'

            # Define a pasta de destino
            caminho_imagem_destino = os.path.join(app.config['UPLOAD_FOLDER'], "Projetos")

            # Cria a pasta caso não exista
            os.makedirs(caminho_imagem_destino, exist_ok=True)

            # Define o caminho completo da imagem
            caminho_imagem = os.path.join(caminho_imagem_destino, nome_imagem)

            # Salva a imagem no diretório
            foto_projeto.save(caminho_imagem)

        # Retorna sucesso com os dados do projeto
        return jsonify({'message': "Projeto cadastrado com sucesso",
                            'projeto': {
                                'id_usuarios': id_usuarios,
                                'titulo': titulo,
                                'descricao': descricao,
                                'categoria': categoria,
                                'status': status,
                                'tipo_ajuda': tipo_ajuda,
                                'localizacao': localizacao
                            }
                            }), 201
    except Exception as e:
        return jsonify({'message': f'Erro ao consultar o banco de dados: {e}'}), 500
    finally:
        cur.close()
        con.close()


@app.route('/editar_projetos/<int:id_projetos>', methods=['PUT'])
def editar_projetos(id_projetos):
    # Cria a conexão com o banco
    con = conexao()

    # Abre o cursor
    cur = con.cursor()

    try:
        cur.execute("""SELECT ID_USUARIOS, TITULO, DESCRICAO, 
                        CATEGORIA, STATUS, TIPO_AJUDA, LOCALIZACAO
                        FROM PROJETOS WHERE ID_PROJETOS = ?""", (id_projetos,))
        projeto = cur.fetchone()

        # Verifica se o projeto existe
        if projeto == None:
            return jsonify({"error": "Projeto não encontrado"}), 404

        id_usuarios = projeto[0]

        # # Verifica se o usuário é o dono da conta ou administrador
        # if decodificar_token()['id_usuarios'] != id_usuarios and decodificar_token()['tipo'] != 0:
        #     return jsonify({'error': 'É necessário ser a ONG do projeto ou o administrador para editar'}), 401

        # Pega os dados enviados ou mantém os atuais
        titulo = request.form.get('titulo', projeto[1])
        descricao = request.form.get('descricao', projeto[2])
        categoria = request.form.get('categoria', projeto[3])
        status = request.form.get('status', projeto[4])
        tipo_ajuda = request.form.get('tipo_ajuda', projeto[5])
        localizacao = request.form.get('localizacao', projeto[6])
        foto_projeto = request.files.get('foto_projeto')

        # Verifica se o título está vazio
        titulo_sem_espaços = titulo.strip()
        if titulo_sem_espaços == '':
            return jsonify({"error": "Título é uma informação obrigatória."}), 400


        # Atualiza os dados do usuário no banco
        cur.execute("""UPDATE PROJETOS
                       SET TITULO = ?,
                           DESCRICAO = ?,
                           CATEGORIA = ?,
                           STATUS = ?,
                           TIPO_AJUDA = ?,
                           LOCALIZACAO = ?
                       WHERE ID_PROJETOS = ?""", (titulo, descricao, categoria, status,
                                                  tipo_ajuda, localizacao, id_projetos))

        # Confirma a alteração no banco
        con.commit()

        # Inicializa o caminho da imagem
        caminho_imagem_destino = None

        # Verifica se foi enviada uma nova foto
        if foto_projeto:
            # Define nome da imagem
            nome_imagem = f'{id_projetos}.jpeg'

            # Define diretório
            caminho_imagem_destino = os.path.join(app.config['UPLOAD_FOLDER'], "Projetos")

            # Cria diretório se não existir
            os.makedirs(caminho_imagem_destino, exist_ok=True)

            # Define caminho completo
            caminho_imagem = os.path.join(caminho_imagem_destino, nome_imagem)

            # Salva imagem
            foto_projeto.save(caminho_imagem)

        # Retorna sucesso
        return jsonify({'message': "Projeto editado com sucesso",
                        'projeto': {
                                'id_usuarios': id_usuarios,
                                'titulo': titulo,
                                'descricao': descricao,
                                'categoria': categoria,
                                'status': status,
                                'tipo_ajuda': tipo_ajuda,
                                'localizacao': localizacao
                            }
                        }), 201
    except Exception as e:
        return jsonify({'message': f'Erro ao consultar o banco de dados: {e}'}), 500
    finally:
        cur.close()
        con.close()


# Excluir projeto
@app.route('/deletar_projetos/<int:id_projetos>', methods=['DELETE'])
def deletar_projetos(id_projetos):
    # Cria a conexão com o banco
    con = conexao()

    # Abre o cursor
    cur = con.cursor()

    try:
        cur.execute("""SELECT ID_USUARIOS,
                              TITULO,
                              DESCRICAO,
                              CATEGORIA,
                              STATUS,
                              TIPO_AJUDA,
                              LOCALIZACAO
                       FROM PROJETOS
                       WHERE ID_PROJETOS = ?""", (id_projetos,))
        projeto = cur.fetchone()

        # Verifica se o projeto existe
        if projeto == None:
            return jsonify({"error": "Projeto não encontrado"}), 404

        id_usuarios = projeto[0]

        # # Verifica se o usuário é o dono da conta ou administrador
        # if decodificar_token()['id_usuarios'] != id_usuarios and decodificar_token()['tipo'] != 0:
        #     return jsonify({'error': 'É necessário ser a ONG do projeto ou o administrador para editar'}), 401

        # Busca atualizações do projeto
        cur.execute("""SELECT ID_ATUALIZACOES
                       FROM ATUALIZACOES
                       WHERE ID_PROJETOS = ?""", (id_projetos,))

        # Se existir atualizações, remove tudo
        if cur.fetchall:
            cur.execute("DELETE FROM ATUALIZACOES WHERE ID_PROJETOS = ?", (id_projetos,))
            con.commit()

        # Remove o projeto da tabela principal
        cur.execute("""DELETE
                       FROM PROJETOS
                       WHERE ID_PROJETOS = ?""", (id_projetos,))

        con.commit()

        # Retorna sucesso
        return jsonify({"error": "Projeto excluído com sucesso"})

    except Exception as e:
        return jsonify({'message': f'Erro ao consultar o banco de dados: {e}'}), 500
    finally:
        cur.close()
        con.close()

@app.route('/projetos_ong/<int:id_usuarios>', methods=['GET'])
def projetos_ong(id_usuarios):
    # Cria a conexão com o banco
    con = conexao()

    # Abre o cursor
    cur = con.cursor()

    try:
        if decodificar_token()['tipo'] == 0:
            cur.execute("""SELECT ID_PROJETOS,
                                  TITULO
                           FROM PROJETOS""")
            projetos = cur.fetchall()

        else:
            cur.execute("""SELECT ID_PROJETOS,
                                  TITULO
                           FROM PROJETOS
                           WHERE ID_USUARIOS = ?""", (id_usuarios,))
            projetos = cur.fetchall()

        # Verifica se o projeto existe
        if projetos == None:
            return jsonify({"error": "Essa ONG não tem nenhum projeto"}), 404

        dic_projetos = []
        for p in projetos:
            dic_projetos.append({
                'id_projetos': p[0],
                'titulo': p[1]
            })

        return jsonify({'message': "Projeto(s) encontrado(s) com sucesso",
                        'projetos': dic_projetos
                        }), 201


    except Exception as e:
        return jsonify({'message': f'Erro ao consultar o banco de dados: {e}'}), 500
    finally:
        cur.close()
        con.close()

@app.route('/ver_projetos/<int:id_projetos>', methods=['GET'])
def ver_projetos(id_projetos):
    # Cria a conexão com o banco
    con = conexao()

    # Abre o cursor
    cur = con.cursor()

    try:
        cur.execute("""SELECT ID_USUARIOS,
                              TITULO,
                              DESCRICAO,
                              CATEGORIA,
                              STATUS,
                              TIPO_AJUDA,
                              LOCALIZACAO
                       FROM PROJETOS
                       WHERE ID_PROJETOS = ?""", (id_projetos,))
        projeto = cur.fetchone()

        # Verifica se o projeto existe
        if projeto == None:
            return jsonify({"error": "Projeto não encontrado"}), 404

        cur.execute("""SELECT ID_ATUALIZACOES, TITULO, TEXTO 
                       FROM ATUALIZACOES WHERE ID_PROJETOS = ?""", (id_projetos, ))
        atualizacoes = cur.fetchall()

        dic_atualizacoes = []
        for a in atualizacoes:
            dic_atualizacoes.append({
                'id_atualizacoes': a[0],
                'titulo': a[1],
                'texto': a[2]
            })

        return jsonify({'message': "Projeto encontrado com sucesso",
                        'projeto': {
                            'id_usuarios': projeto[0],
                            'titulo': projeto[1],
                            'descricao': projeto[2],
                            'categoria': projeto[3],
                            'status': projeto[4],
                            'tipo_ajuda': projeto[5],
                            'localizacao': projeto[6],
                        },
                        'atualizacoes': dic_atualizacoes
                        }), 201


    except Exception as e:
        return jsonify({'message': f'Erro ao consultar o banco de dados: {e}'}), 500
    finally:
        cur.close()
        con.close()

# Criar atualização
@app.route('/criar_atualizacoes', methods=['POST'])
def criar_atualizacoes():
    titulo = request.form.get('titulo', None)
    texto = request.form.get('texto', None)
    id_projetos = request.form.get('projeto', None)
    foto_atualizacao = request.files.get('foto_atualizacao')

    # Temos uma função para a conexão com o banco -> Precisamos chamá-la
    con = conexao()

    # Abrir o cursor
    cur = con.cursor()

    try:
        # if decodificar_token() == False:
        #     return jsonify({'error': 'Você precisa estar logado para criar um projeto'})
        #
        # if decodificar_token()['tipo'] == 1:
        #     return jsonify({'error': 'Doadores não podem criar projetos'})

        if id_projetos == None:
            return jsonify({"error": "Projeto é uma informação obrigatória."}), 400

        cur.execute("""SELECT ID_USUARIOS
                       FROM PROJETOS
                       WHERE ID_PROJETOS = ?""", (id_projetos,))
        projeto = cur.fetchone()

        if projeto == None:
            return jsonify({"error": "Projeto não encontrado"}), 404

        id_usuarios = projeto[0]

        # if decodificar_token()['id_usuarios'] != id_usuarios and decodificar_token()['tipo'] != 0:
        #     return jsonify({'error': 'É necessário ser a ONG do projeto ou o administrador para criar atualizações'}), 401

        # Verifica se o título está vazio
        if titulo == None:
            return jsonify({"error": "Título é uma informação obrigatória."}), 400

        titulo_sem_espaços = titulo.strip()
        if titulo_sem_espaços == '':
            return jsonify({"error": "Título é uma informação obrigatória."}), 400

        # Insere o usuário no banco de dados
        cur.execute("""INSERT INTO ATUALIZACOES (ID_PROJETOS, TITULO, TEXTO)
                       VALUES (?, ?, ?) RETURNING ID_ATUALIZACOES""",
                    (id_projetos, titulo, texto))

        # Recupera o ID do usuário recém criado
        id_atualizacoes = cur.fetchone()[0]

        con.commit()

        caminho_imagem_destino = None

        # Verifica se foi enviada uma foto de perfil
        if foto_atualizacao:
            # Define o nome da imagem com base no ID do usuário
            nome_imagem = f'{id_atualizacoes}.jpeg'

            # Define a pasta de destino
            caminho_imagem_destino = os.path.join(app.config['UPLOAD_FOLDER'], "Atualizações")

            # Cria a pasta caso não exista
            os.makedirs(caminho_imagem_destino, exist_ok=True)

            # Define o caminho completo da imagem
            caminho_imagem = os.path.join(caminho_imagem_destino, nome_imagem)

            # Salva a imagem no diretório
            foto_atualizacao.save(caminho_imagem)

        # Retorna sucesso com os dados do projeto
        return jsonify({'message': "Atualização cadastrada com sucesso",
                            'atualizacao': {
                                'id_projeto': id_projetos,
                                'titulo': titulo,
                                'texto': texto
                            }
                            }), 201
    except Exception as e:
        return jsonify({'message': f'Erro ao consultar o banco de dados: {e}'}), 500
    finally:
        cur.close()
        con.close()

@app.route('/editar_atualizacoes/<int:id_atualizacoes>', methods=['PUT'])
def editar_atualizacoes(id_atualizacoes):
    # Cria a conexão com o banco
    con = conexao()

    # Abre o cursor
    cur = con.cursor()

    try:
        cur.execute("""SELECT ID_PROJETOS, TITULO, TEXTO
                        FROM ATUALIZACOES WHERE ID_ATUALIZACOES = ?""", (id_atualizacoes,))
        atualizacao = cur.fetchone()

        # Verifica se a atualização existe
        if atualizacao == None:
            return jsonify({"error": "Atualização não encontrado"}), 404

        id_projetos = atualizacao[0]

        cur.execute("""SELECT ID_USUARIOS FROM PROJETOS
                       WHERE ID_PROJETOS = ?""", (id_projetos,))
        projeto = cur.fetchone()

        if projeto == None:
            return jsonify({"error": "Projeto não encontrado"}), 404

        id_usuarios = projeto[0]

        # # Verifica se o usuário é o dono da conta ou administrador
        # if decodificar_token()['id_usuarios'] != id_usuarios and decodificar_token()['tipo'] != 0:
        #     return jsonify({'error': 'É necessário ser a ONG do projeto ou o administrador para editar'}), 401

        # Pega os dados enviados ou mantém os atuais
        id_projetos = request.form.get('projeto', atualizacao[0])
        titulo = request.form.get('titulo', atualizacao[1])
        texto = request.form.get('texto', atualizacao[2])
        foto_atualizacao = request.files.get('foto_atualizacao')

        # Verifica se o título está vazio
        titulo_sem_espaços = titulo.strip()
        if titulo_sem_espaços == '':
            return jsonify({"error": "Título é uma informação obrigatória."}), 400


        # Atualiza os dados do usuário no banco
        cur.execute("""UPDATE ATUALIZACOES
                       SET ID_PROJETOS = ?,
                           TITULO = ?,
                           TEXTO = ?
                       WHERE ID_ATUALIZACOES = ?""",
                    (id_projetos, titulo, texto, id_atualizacoes))

        # Confirma a alteração no banco
        con.commit()

        # Inicializa o caminho da imagem
        caminho_imagem_destino = None

        # Verifica se foi enviada uma nova foto
        if foto_atualizacao:
            # Define nome da imagem
            nome_imagem = f'{id_atualizacoes}.jpeg'

            # Define diretório
            caminho_imagem_destino = os.path.join(app.config['UPLOAD_FOLDER'], "Atualizações")

            # Cria diretório se não existir
            os.makedirs(caminho_imagem_destino, exist_ok=True)

            # Define caminho completo
            caminho_imagem = os.path.join(caminho_imagem_destino, nome_imagem)

            # Salva imagem
            foto_atualizacao.save(caminho_imagem)

        # Retorna sucesso
        return jsonify({'message': "Projeto editado com sucesso",
                        'projeto': {
                                'id_projeto': id_projetos,
                                'titulo': titulo,
                                'localizacao': texto
                            }
                        }), 201
    except Exception as e:
        return jsonify({'message': f'Erro ao consultar o banco de dados: {e}'}), 500
    finally:
        cur.close()
        con.close()


# Excluir atualização
@app.route('/deletar_atualizacoes/<int:id_atualizacoes>', methods=['DELETE'])
def deletar_atualizacoes(id_atualizacoes):
    # Cria a conexão com o banco
    con = conexao()

    # Abre o cursor
    cur = con.cursor()

    try:
        cur.execute("""SELECT ID_PROJETOS, TITULO, TEXTO
                       FROM ATUALIZACOES
                       WHERE ID_ATUALIZACOES = ?""", (id_atualizacoes,))
        atualizacao = cur.fetchone()

        # Verifica se a atualização existe
        if atualizacao == None:
            return jsonify({"error": "Atualização não encontrado"}), 404

        id_projetos = atualizacao[0]

        cur.execute("""SELECT ID_USUARIOS
                       FROM PROJETOS
                       WHERE ID_PROJETOS = ?""", (id_projetos,))
        projeto = cur.fetchone()

        if projeto == None:
            return jsonify({"error": "Projeto não encontrado"}), 404

        id_usuarios = projeto[0]

        # # Verifica se o usuário é o dono da conta ou administrador
        # if decodificar_token()['id_usuarios'] != id_usuarios and decodificar_token()['tipo'] != 0:
        #     return jsonify({'error': 'É necessário ser a ONG do projeto ou o administrador para editar'}), 401

        cur.execute("DELETE FROM ATUALIZACOES WHERE ID_ATUALIZACOES = ?", (id_atualizacoes,))
        con.commit()

        # Retorna sucesso
        return jsonify({"message": "Atualização excluída com sucesso"})

    except Exception as e:
        return jsonify({'error': f'Erro ao consultar o banco de dados: {e}'}), 500
    finally:
        cur.close()
        con.close()

@app.route('/listar_atualizacoes', methods=['GET'])
def listar_atualizacoes():
    # Cria a conexão com o banco
    con = conexao()

    # Abre o cursor
    cur = con.cursor()

    try:
        cur.execute("""SELECT ID_ATUALIZACOES, ID_PROJETOS, TITULO, TEXTO
                       FROM ATUALIZACOES""")
        atualizacoes = cur.fetchall()

        dic_atualizacoes = []
        for a in atualizacoes:
            dic_atualizacoes.append({
                'id_atualizacoes': a[0],
                'id_projeto': a[1],
                'titulo': a[2],
                'texto': a[3]
            })

        return jsonify({'atualizacoes': dic_atualizacoes}), 201

    except Exception as e:
        return jsonify({'error': f'Erro ao consultar o banco de dados: {e}'}), 500
    finally:
        cur.close()
        con.close()
