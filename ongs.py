# ongs.py
from flask import jsonify, request, render_template
from funcao import enviando_email, decodificar_token
from main import app
from db import conexao
import threading
import datetime


# ============================================
# ROTA: Listar todas as ONGs (ADMIN)
# ============================================
@app.route('/admin/listar_ongs', methods=['GET'])
def listar_ongs():
    """Lista todas as ONGs cadastradas. Apenas administradores podem acessar."""
    con = conexao()
    cur = con.cursor()

    try:
        if decodificar_token() == False:
            return jsonify({'error': 'Token necessário'}), 401

        if decodificar_token()['tipo'] != 0:
            return jsonify({'error': 'É necessário ser administrador para acessar esta rota'}), 403

        cur.execute("""
            SELECT ID_USUARIOS,
                   NOME,
                   EMAIL,
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
                   DATA_CADASTRO,
                   EMAIL_CONFIRMACAO,
                   MOTIVO_REPROVACAO
            FROM USUARIOS
            WHERE TIPO = 2
            ORDER BY DATA_CADASTRO DESC
        """)

        ongs = cur.fetchall()

        if not ongs:
            return jsonify({
                'message': 'Nenhuma ONG cadastrada',
                'ongs': []
            }), 200

        lista_ongs = []
        for ong in ongs:
            if ong[7] == 0:
                status = 'Pendente'
            elif ong[7] == 1:
                status = 'Aprovada'
            elif ong[7] == 2:
                status = 'Reprovada'
            else:
                status = 'Desconhecido'

            lista_ongs.append({
                'id': ong[0],
                'nome': ong[1],
                'email': ong[2],
                'cpf_cnpj': ong[3],
                'telefone': ong[4],
                'descricao_breve': ong[5],
                'descricao_longa': ong[6],
                'status': status,
                'codigo_aprovacao': ong[7],
                'cod_banco': ong[8],
                'num_agencia': ong[9],
                'num_conta': ong[10],
                'tipo_conta': ong[11],
                'chave_pix': ong[12],
                'categoria': ong[13],
                'ativo': bool(ong[14]),
                'localizacao': ong[15],
                'data_cadastro': ong[16].strftime('%d/%m/%Y %H:%M:%S') if ong[16] else None,
                'email_confirmado': bool(ong[17]),
                'motivo_reprovacao': ong[18] if len(ong) > 18 and ong[18] else None
            })

        return jsonify({
            'message': 'ONGs listadas com sucesso',
            'total': len(lista_ongs),
            'ongs': lista_ongs
        }), 200

    except Exception as e:
        print(f"ERRO listar_ongs: {e}")
        return jsonify({'error': f'Erro ao consultar o banco de dados: {str(e)}'}), 500
    finally:
        cur.close()
        con.close()


# ============================================
# ROTA: Buscar ONG por ID (ADMIN)
# ============================================
@app.route('/admin/buscar_ong', methods=['GET'])
def buscar_ong():
    """Busca uma ONG específica por ID."""
    ong_id = request.args.get('id')

    if not ong_id:
        return jsonify({'error': 'Forneça um ID para busca'}), 400

    con = conexao()
    cur = con.cursor()

    try:
        if decodificar_token() == False:
            return jsonify({'error': 'Token necessário'}), 401

        if decodificar_token()['tipo'] != 0:
            return jsonify({'error': 'É necessário ser administrador para acessar esta rota'}), 403

        cur.execute("""
            SELECT ID_USUARIOS,
                   NOME,
                   EMAIL,
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
                   DATA_CADASTRO,
                   EMAIL_CONFIRMACAO,
                   MOTIVO_REPROVACAO
            FROM USUARIOS
            WHERE TIPO = 2 AND ID_USUARIOS = ?
        """, (ong_id,))

        ong = cur.fetchone()

        if not ong:
            return jsonify({'error': 'ONG não encontrada'}), 404

        if ong[7] == 0:
            status = 'Pendente'
        elif ong[7] == 1:
            status = 'Aprovada'
        elif ong[7] == 2:
            status = 'Reprovada'
        else:
            status = 'Desconhecido'

        return jsonify({
            'message': 'ONG encontrada',
            'ong': {
                'id': ong[0],
                'nome': ong[1],
                'email': ong[2],
                'cpf_cnpj': ong[3],
                'telefone': ong[4],
                'descricao_breve': ong[5],
                'descricao_longa': ong[6],
                'status': status,
                'codigo_aprovacao': ong[7],
                'cod_banco': ong[8],
                'num_agencia': ong[9],
                'num_conta': ong[10],
                'tipo_conta': ong[11],
                'chave_pix': ong[12],
                'categoria': ong[13],
                'ativo': bool(ong[14]),
                'localizacao': ong[15],
                'data_cadastro': ong[16].strftime('%d/%m/%Y %H:%M:%S') if ong[16] else None,
                'email_confirmado': bool(ong[17]),
                'motivo_reprovacao': ong[18] if len(ong) > 18 and ong[18] else None
            }
        }), 200

    except Exception as e:
        print(f"ERRO buscar_ong: {e}")
        return jsonify({'error': f'Erro ao consultar o banco de dados: {str(e)}'}), 500
    finally:
        cur.close()
        con.close()


# ============================================
# ROTA: Aprovar ONG (ADMIN)
# ============================================
@app.route('/admin/aprovar_ong/<int:id_usuarios>', methods=['PUT'])
def aprovar_ong(id_usuarios):
    """Aprova uma ONG cadastrada. Apenas administradores."""
    con = conexao()
    cur = con.cursor()

    try:
        if decodificar_token() == False:
            return jsonify({'error': 'Token necessário'}), 401

        if decodificar_token()['tipo'] != 0:
            return jsonify({'error': 'É necessário ser administrador para aprovar ONGs'}), 403

        cur.execute("""
            SELECT ID_USUARIOS, NOME, EMAIL, APROVACAO
            FROM USUARIOS
            WHERE ID_USUARIOS = ? AND TIPO = 2
        """, (id_usuarios,))

        ong = cur.fetchone()

        if not ong:
            return jsonify({'error': 'ONG não encontrada'}), 404

        if ong[3] == 1:
            return jsonify({'message': 'Esta ONG já está aprovada'}), 200

        cur.execute("""
            UPDATE USUARIOS
            SET APROVACAO = 1,
                MOTIVO_REPROVACAO = NULL
            WHERE ID_USUARIOS = ?
        """, (id_usuarios,))

        con.commit()

        # Envia e-mail de aprovação
        assunto = 'ONG Aprovada - Doar +'
        mensagem = f'Parabéns {ong[1]}! Sua ONG foi aprovada na plataforma Doar +. Agora você pode acessar sua conta e começar a receber doações.'

        html = render_template('template_aprovacao.html', nome=ong[1], mensagem=mensagem)

        print(f"DEBUG - Enviando email de APROVAÇÃO para: {ong[2]}")

        def enviar_email_aprovacao():
            try:
                enviando_email(ong[2], assunto, html)
                print(f"DEBUG - Email de aprovação enviado com sucesso para {ong[2]}")
            except Exception as e:
                print(f"ERRO ao enviar email de aprovação: {e}")

        threading.Thread(target=enviar_email_aprovacao).start()

        return jsonify({
            'message': f'ONG {ong[1]} aprovada com sucesso!',
            'id': id_usuarios
        }), 200

    except Exception as e:
        con.rollback()
        print(f"ERRO aprovar_ong: {e}")
        return jsonify({'error': f'Erro ao aprovar ONG: {str(e)}'}), 500
    finally:
        cur.close()
        con.close()


# ============================================
# ROTA: Reprovar ONG (ADMIN)
# ============================================
@app.route('/admin/reprovar_ong/<int:id_usuarios>', methods=['PUT'])
def reprovar_ong(id_usuarios):
    """Reprova uma ONG cadastrada. Apenas administradores."""
    con = conexao()
    cur = con.cursor()

    try:
        if decodificar_token() == False:
            return jsonify({'error': 'Token necessário'}), 401

        if decodificar_token()['tipo'] != 0:
            return jsonify({'error': 'É necessário ser administrador para reprovar ONGs'}), 403

        motivo = request.json.get('motivo', 'Não especificado')
        print(f"DEBUG - Motivo da reprovação: {motivo}")

        cur.execute("""
            SELECT ID_USUARIOS, NOME, EMAIL, APROVACAO
            FROM USUARIOS
            WHERE ID_USUARIOS = ? AND TIPO = 2
        """, (id_usuarios,))

        ong = cur.fetchone()

        if not ong:
            return jsonify({'error': 'ONG não encontrada'}), 404

        if ong[3] == 2:
            return jsonify({'message': 'Esta ONG já está reprovada'}), 200

        cur.execute("""
            UPDATE USUARIOS
            SET APROVACAO = 2,
                MOTIVO_REPROVACAO = ?
            WHERE ID_USUARIOS = ?
        """, (motivo, id_usuarios))

        con.commit()

        # Envia e-mail de reprovação
        assunto = 'Atualização sobre sua ONG - Doar +'
        mensagem = f'Olá {ong[1]}, após análise, sua ONG não foi aprovada na plataforma Doar +.'

        html = render_template(
            'template_reprovacao.html',
            nome=ong[1],
            mensagem=mensagem,
            motivo=motivo
        )

        print(f"DEBUG - Enviando email de REPROVAÇÃO para: {ong[2]}")

        def enviar_email_reprovacao():
            try:
                enviando_email(ong[2], assunto, html)
                print(f"DEBUG - Email de reprovação enviado com sucesso para {ong[2]}")
            except Exception as e:
                print(f"ERRO ao enviar email de reprovação: {e}")

        threading.Thread(target=enviar_email_reprovacao).start()

        return jsonify({
            'message': f'ONG {ong[1]} reprovada',
            'id': id_usuarios,
            'motivo': motivo
        }), 200

    except Exception as e:
        con.rollback()
        print(f"ERRO reprovar_ong: {e}")
        return jsonify({'error': f'Erro ao reprovar ONG: {str(e)}'}), 500
    finally:
        cur.close()
        con.close()


# ============================================
# ROTA: Bloquear/Desbloquear ONG (ADMIN)
# ============================================
@app.route('/admin/bloquear_ong/<int:id_usuarios>', methods=['PUT'])
def bloquear_ong(id_usuarios):
    """Bloqueia ou desbloqueia uma ONG. Apenas administradores."""
    con = conexao()
    cur = con.cursor()

    try:
        if decodificar_token() == False:
            return jsonify({'error': 'Token necessário'}), 401

        if decodificar_token()['tipo'] != 0:
            return jsonify({'error': 'É necessário ser administrador para bloquear ONGs'}), 403

        acao = request.json.get('acao', 'bloquear')

        cur.execute("""
            SELECT ID_USUARIOS, NOME, EMAIL, ATIVO
            FROM USUARIOS
            WHERE ID_USUARIOS = ? AND TIPO = 2
        """, (id_usuarios,))

        ong = cur.fetchone()

        if not ong:
            return jsonify({'error': 'ONG não encontrada'}), 404

        if acao == 'bloquear':
            novo_status = 0
            mensagem_status = 'bloqueada'
        else:
            novo_status = 1
            mensagem_status = 'desbloqueada'

        cur.execute("""
            UPDATE USUARIOS
            SET ATIVO = ?
            WHERE ID_USUARIOS = ?
        """, (novo_status, id_usuarios))

        con.commit()

        return jsonify({
            'message': f'ONG {ong[1]} {mensagem_status} com sucesso!',
            'id': id_usuarios,
            'status': mensagem_status
        }), 200

    except Exception as e:
        con.rollback()
        print(f"ERRO bloquear_ong: {e}")
        return jsonify({'error': f'Erro ao bloquear/desbloquear ONG: {str(e)}'}), 500
    finally:
        cur.close()
        con.close()


# ============================================
# ROTA: Deletar ONG (ADMIN)
# ============================================
@app.route('/admin/deletar_ong/<int:id_usuarios>', methods=['DELETE'])
def deletar_ong(id_usuarios):
    """Deleta uma ONG apenas se estiver bloqueada ou reprovada."""
    con = conexao()
    cur = con.cursor()

    try:
        if decodificar_token() == False:
            return jsonify({'error': 'Token necessário'}), 401

        if decodificar_token()['tipo'] != 0:
            return jsonify({'error': 'É necessário ser administrador para deletar ONGs'}), 403

        cur.execute("""
            SELECT ID_USUARIOS, NOME, EMAIL, ATIVO, APROVACAO
            FROM USUARIOS
            WHERE ID_USUARIOS = ? AND TIPO = 2
        """, (id_usuarios,))

        ong = cur.fetchone()

        if not ong:
            return jsonify({'error': 'ONG não encontrada'}), 404

        if ong[3] == 1 and ong[4] != 2:
            return jsonify({
                'error': 'Esta ONG não pode ser deletada. Apenas ONGs bloqueadas ou reprovadas podem ser removidas.',
                'status_atual': {
                    'ativo': bool(ong[3]),
                    'aprovacao': ong[4]
                }
            }), 403

        cur.execute("DELETE FROM HISTORICO_SENHA WHERE ID_USUARIOS = ?", (id_usuarios,))
        cur.execute("DELETE FROM RECUPERACAO_SENHA WHERE ID_USUARIOS = ?", (id_usuarios,))
        cur.execute("DELETE FROM USUARIOS WHERE ID_USUARIOS = ?", (id_usuarios,))

        con.commit()

        return jsonify({
            'message': f'ONG {ong[1]} deletada com sucesso!',
            'id': id_usuarios
        }), 200

    except Exception as e:
        con.rollback()
        print(f"ERRO deletar_ong: {e}")
        return jsonify({'error': f'Erro ao deletar ONG: {str(e)}'}), 500
    finally:
        cur.close()
        con.close()


# ============================================
# ROTA: Editar perfil da ONG (PRÓPRIA ONG)
# ============================================
@app.route('/ong/editar_perfil/<int:id_usuarios>', methods=['PUT'])
def editar_perfil_ong(id_usuarios):
    """Edita o perfil da ONG. A própria ONG pode editar seus dados."""
    con = conexao()
    cur = con.cursor()

    try:
        token_data = decodificar_token()
        if token_data == False:
            return jsonify({'error': 'Token necessário'}), 401

        if token_data['id_usuarios'] != id_usuarios:
            return jsonify({'error': 'Você só pode editar seu próprio perfil'}), 403

        if token_data['tipo'] != 2:
            return jsonify({'error': 'Apenas ONGs podem acessar esta rota'}), 403

        cur.execute("""
            SELECT *
            FROM USUARIOS
            WHERE ID_USUARIOS = ? AND TIPO = 2
        """, (id_usuarios,))

        ong_atual = cur.fetchone()
        if not ong_atual:
            return jsonify({'error': 'ONG não encontrada'}), 404

        nome = request.form.get('nome', ong_atual[1])
        email = request.form.get('email', ong_atual[2])
        cpf_cnpj = request.form.get('cpf_cnpj', ong_atual[4])
        telefone = request.form.get('telefone', ong_atual[5])
        descricao_breve = request.form.get('descricao_breve', ong_atual[6])
        descricao_longa = request.form.get('descricao_longa', ong_atual[7])
        cod_banco = request.form.get('cod_banco', ong_atual[9])
        num_agencia = request.form.get('num_agencia', ong_atual[10])
        num_conta = request.form.get('num_conta', ong_atual[11])
        tipo_conta = request.form.get('tipo_conta', ong_atual[12])
        chave_pix = request.form.get('chave_pix', ong_atual[13])
        categoria = request.form.get('categoria', ong_atual[14])
        localizacao = request.form.get('localizacao', ong_atual[16])
        senha = request.form.get('senha', None)
        confirmar_senha = request.form.get('confirmar_senha', None)

        if not nome or not nome.strip():
            return jsonify({'error': 'Nome é obrigatório'}), 400

        if not email or not email.strip():
            return jsonify({'error': 'Email é obrigatório'}), 400

        if not cpf_cnpj or not cpf_cnpj.strip():
            return jsonify({'error': 'CPF/CNPJ é obrigatório'}), 400

        from flask_bcrypt import generate_password_hash
        from funcao import senha_forte, senha_correspondente, senha_antiga, verificar_existente

        nova_senha_hash = ong_atual[3]
        if senha:
            if not senha_forte(senha):
                return jsonify({'error': 'Senha fraca'}), 400

            if not senha_correspondente(senha, confirmar_senha):
                return jsonify({'error': 'Senhas não correspondem'}), 400

            if not senha_antiga(id_usuarios, senha):
                return jsonify({'error': 'A nova senha não pode ser igual às últimas 3 utilizadas'}), 400

            nova_senha_hash = generate_password_hash(senha).decode('utf-8')

        email_confirmacao = ong_atual[19]
        codigo_confirmacao = ong_atual[20]

        cur.execute("""
            UPDATE USUARIOS
            SET NOME = ?,
                EMAIL = ?,
                SENHA = ?,
                CPF_CNPJ = ?,
                TELEFONE = ?,
                DESCRICAO_BREVE = ?,
                DESCRICAO_LONGA = ?,
                COD_BANCO = ?,
                NUM_AGENCIA = ?,
                NUM_CONTA = ?,
                TIPO_CONTA = ?,
                CHAVE_PIX = ?,
                CATEGORIA = ?,
                LOCALIZACAO = ?,
                EMAIL_CONFIRMACAO = ?,
                CODIGO_CONFIRMACAO = ?
            WHERE ID_USUARIOS = ?
        """, (
            nome, email, nova_senha_hash, cpf_cnpj, telefone,
            descricao_breve, descricao_longa, cod_banco, num_agencia,
            num_conta, tipo_conta, chave_pix, categoria, localizacao,
            email_confirmacao, codigo_confirmacao, id_usuarios
        ))

        con.commit()

        return jsonify({
            'message': 'Perfil atualizado com sucesso',
            'usuario': {
                'id': id_usuarios,
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
        }), 200

    except Exception as e:
        con.rollback()
        print(f"ERRO editar_perfil_ong: {e}")
        return jsonify({'error': f'Erro ao editar perfil: {str(e)}'}), 500
    finally:
        cur.close()
        con.close()