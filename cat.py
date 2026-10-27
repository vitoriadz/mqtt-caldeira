"""Serviço CAT: média das temperaturas dos últimos 120 s, recalculada a cada 60 s."""
import json
import threading
import time
from collections import deque

from config import (BROKER, PORT, TOPICO_SENSORES, TOPICO_MEDIA, TOPICO_EVENTOS,
                    JANELA_SEGUNDOS, INTERVALO_CALCULO, LIMITE_VARIACAO,
                    LIMITE_TEMP_ALTA, criar_cliente)


class CAT:
    def __init__(self):
        self.leituras = deque()       
        self.lock = threading.Lock()
        self.ultima_media = None
        self.client = criar_cliente("servico_cat")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    # ---------- MQTT ----------
    def on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            print("[CAT] Conectado. Assinando sensores...")
            client.subscribe(TOPICO_SENSORES, qos=1)  
        else:
            print(f"[CAT] Falha na conexão: {rc}")

    def on_message(self, client, userdata, msg):
        try:
            dados = json.loads(msg.payload.decode())
            temp = float(dados["temperatura"])
            sensor = dados.get("sensor_id", "desconhecido")
        except (ValueError, KeyError, json.JSONDecodeError) as e:
            print(f"[CAT] Payload inválido ignorado: {e}")
            return

        with self.lock:
            self.leituras.append((time.time(), temp, sensor))
        print(f"[CAT] {sensor}: {temp}°C")

    # ---------- Cálculo ----------
    def calcular(self):
        agora = time.time()
        with self.lock:
            while self.leituras and agora - self.leituras[0][0] > JANELA_SEGUNDOS:
                self.leituras.popleft()
            temps = [t for _, t, _ in self.leituras]
            sensores = {s for _, _, s in self.leituras}

        if not temps:
            print("[CAT] Sem leituras na janela.")
            return

        media = round(sum(temps) / len(temps), 2)
        print(f"[CAT] 📊 Média ({JANELA_SEGUNDOS}s) = {media}°C | "
              f"{len(temps)} amostras de {len(sensores)} sensor(es)")

        self.client.publish(TOPICO_MEDIA, json.dumps(
            {"media": media, "amostras": len(temps), "sensores": len(sensores), "timestamp": agora}))

        # Evento 1: aumento repentino 
        if self.ultima_media is not None:
            variacao = round(media - self.ultima_media, 2)
            if abs(variacao) >= LIMITE_VARIACAO:
                self.publicar_evento("AUMENTO_REPENTINO", media,
                                     f"Média variou {variacao:+}°C ({self.ultima_media} → {media})")

        # Evento 2: temperatura alta
        if media > LIMITE_TEMP_ALTA:
            self.publicar_evento("TEMPERATURA_ALTA", media,
                                 f"Média {media}°C acima de {LIMITE_TEMP_ALTA}°C")

        self.ultima_media = media

    def publicar_evento(self, tipo, media, detalhe):
        print(f"[CAT] Evento publicado: {tipo}")
        self.client.publish(TOPICO_EVENTOS, json.dumps(
            {"tipo": tipo, "mensagem": detalhe, "media": media, "timestamp": time.time()}), qos=1)

    def run(self):
        self.client.connect(BROKER, PORT, 60)
        self.client.loop_start()
        try:
            while True:
                time.sleep(INTERVALO_CALCULO)
                self.calcular()
        except KeyboardInterrupt:
            pass
        finally:
            self.client.loop_stop()
            self.client.disconnect()


if __name__ == "__main__":
    CAT().run()