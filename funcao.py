from flask_bcrypt import generate_password_hash, check_password_hash
from flask import request, current_app, render_template

# Importar o con da main
from db import conexao

# Bibliotecas para envio de e-mail
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Bibliotecas para token
import jwt
import datetime

# Função para verificar existente
def verificar_existente(valor, tipo, id_usuarios = None):
    # Por padrão, o id_usuario é none (quando não passamos na hora de chamar a função)

    con = conexao()
    cur = con.cursor()
    try:

        if tipo == 1:
            if id_usuarios:
                cur.execute("""SELECT 1
                               FROM USUARIOS
                               WHERE CPF_CNPJ = ? AND ID_USUARIOS != ?""", (valor, id_usuarios))

            else:
                cur.execute("""SELECT 1
                           FROM USUARIOS
                           WHERE CPF_CNPJ = ?""", (valor,))

        elif tipo == 2:
            if id_usuarios:
                cur.execute("""SELECT 1
                               FROM USUARIOS
                               WHERE EMAIL = ? AND ID_USUARIOS != ?""", (valor, id_usuarios))

            else:
                cur.execute("""SELECT 1
                           FROM USUARIOS
                           WHERE EMAIL = ?""", (valor, ))

        if not cur.fetchone():
            return True
        return False
    except Exception as e:
        return False
    finally:
        cur.close()
        con.close()

def senha_correspondente(senha, confirmar_senha):
    try:
        if senha == confirmar_senha:
            return True
        return False
    except Exception as e:
        return False


def senha_forte(senha):
    try:
        if len(senha) < 8:
            return False
        criterios = {
            "maiuscula": False,
            "minuscula": False,
            "numero": False,
            "especial": False
        }
        for s in senha:
            if s.isupper():
                criterios["maiuscula"] = True
            elif s.islower():
                criterios["minuscula"] = True
            elif s.isdigit():
                criterios["numero"] = True
            elif s.isalnum() is False:
                criterios["especial"] = True
        if criterios["maiuscula"] == True and criterios["minuscula"] == True and criterios["numero"] == True and criterios["especial"] == True:
            return True
        return False
    except Exception as e:
        return False

def senha_antiga(id_usuarios, nova_senha):
    con = conexao()
    cursor = con.cursor()
    try:
        cursor.execute('SELECT senha FROM usuarios WHERE id_usuarios = ?', (id_usuarios, ))
        senha_atual_hash = cursor.fetchone()[0]

        cursor.execute('SELECT FIRST 2 SENHA_HASH FROM HISTORICO_SENHA WHERE id_usuarios = ? ORDER BY DATA_ALTERACAO',
                   (id_usuarios,))
        ultimas_senhas = cursor.fetchall()

        cursor.execute(
            'SELECT FIRST 1 ID_HISTORICO_SENHA FROM HISTORICO_SENHA WHERE id_usuarios = ? ORDER BY DATA_ALTERACAO ASC',
            (id_usuarios,))
        tem_senha = cursor.fetchone()

        if tem_senha:
            senha_mais_antiga = tem_senha[0]

        for u in ultimas_senhas:
            senha_antiga = u[0]
            if check_password_hash(senha_antiga, nova_senha):
                return False

        if check_password_hash(senha_atual_hash, nova_senha):
            return False

        data_alteracao = datetime.datetime.utcnow()

        cursor.execute("INSERT INTO HISTORICO_SENHA(id_usuarios, SENHA_HASH, data_Alteracao) VALUES(?, ?, ?)",
                       (id_usuarios, senha_atual_hash, data_alteracao))

        cursor.execute('DELETE FROM RECUPERACAO_SENHA WHERE id_usuarios = ?', (id_usuarios,))

        if ultimas_senhas:
            if len(ultimas_senhas) == 2:
                cursor.execute(""" DELETE FROM HISTORICO_SENHA
                                   WHERE ID_HISTORICO_SENHA = ?""",
                               (senha_mais_antiga,))


        con.commit()

        return True

    except Exception as e:
        print(e)
        return False


def enviando_email(destinatario, assunto, html):
    user = 'luisa.michelinr@gmail.com'
    senha = 'hqca hibi tndj trfk'

    msg = MIMEMultipart()
    msg['From'] = user
    msg['To'] = destinatario
    msg['Subject'] = assunto
    msg.attach(MIMEText(html, 'html'))


    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(user, senha)
        server.sendmail(user, [destinatario], msg.as_string())
    finally:
        server.quit()


def gerar_token(tipo, id_usuarios, tempo):
    payload = { 'tipo': tipo,
                'id_usuarios': id_usuarios,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=tempo)
               }
    senha_secreta = current_app.config['SECRET_KEY']
    token = jwt.encode(payload, senha_secreta, algorithm='HS256')

    return token

def decodificar_token():
    try:
        token = request.cookies.get("acess_token")
        if not token:
            return False
        senha_secreta = current_app.config['SECRET_KEY']
        payload = jwt.decode(token, senha_secreta, algorithms=['HS256'])
        return {'tipo': payload['tipo'], 'id_usuarios': payload['id_usuarios']}
    except jwt.ExpiredSignatureError:
        return False
    except jwt.InvalidTokenError:
        return False