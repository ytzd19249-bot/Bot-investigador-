import requests

# Token del bot (el suyo de BotFather)
BOT_TOKEN = "8255571596:AAEvqpVQR__FYQUerAVZtEWXNWu1ZtHT3r8"

# Username del canal público
CHANNEL_ID = "@infoventas2025"

# Función para enviar mensajes al canal
def send_message_to_channel(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHANNEL_ID, "text": text}
    response = requests.post(url, data=data)
    print(response.json())  # Para ver en logs la respuesta de Telegram
    return response.json()

# Ejemplo de uso
if __name__ == "__main__":
    resultado_investigacion = (
        "🔎 Nuevo producto investigado:\n"
        "Nombre: Ejemplo\n"
        "Precio: $25\n"
        "Link: https://amazon.com/ejemplo"
    )
    send_message_to_channel(resultado_investigacion)
