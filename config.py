import paho.mqtt.client as mqtt

BROKER = "localhost"          
PORT = 1883
PREFIXO = "caldeira"          
TOPICO_SENSORES = f"{PREFIXO}/sensores/+/temperatura"    
TOPICO_SENSOR_FMT = f"{PREFIXO}/sensores/{{sensor_id}}/temperatura"
TOPICO_MEDIA = f"{PREFIXO}/cat/media"
TOPICO_EVENTOS = f"{PREFIXO}/cat/eventos"

JANELA_SEGUNDOS = 120
INTERVALO_CALCULO = 60        
LIMITE_VARIACAO = 5.0
LIMITE_TEMP_ALTA = 200.0


def criar_cliente(client_id: str) -> mqtt.Client:
    """Cria cliente compatível com paho-mqtt 1.x e 2.x."""
    try:
        return mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id)
    except AttributeError:
        return mqtt.Client(client_id=client_id)