import smtplib

correo = 'losamistosos12@gmail.com'
contrasena = 'rjabjxiabmcscpic'

try:
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.ehlo()
    server.starttls()
    server.login(correo, contrasena)
    print('✅ Conexión exitosa')
    server.quit()
except Exception as e:
    print(f'❌ Error: {e}')