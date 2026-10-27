"""
Uso:
  python sensor.py                       # 1 sensor, envia a cada 60 s
  python sensor.py --id S2 --intervalo 5 # intervalo 
  python sensor.py --id S3 --base 220    # sensor "quente" (dispara temperatura alta)
  python sensor.py --id S4 --pico-em 4   # no 4º envio, salta +20°C
"""
import argparse
import json
import random
import time

from config import BROKER, PORT, TOPICO_SENSOR_FMT, criar_cliente


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", default=f"sensor_{random.randint(100, 999)}")
    ap.add_argument("--intervalo", type=float, default=60.0, help="segundos entre envios")
    ap.add_argument("--base", type=float, default=30.0, help="temperatura base")
    ap.add_argument("--pico-em", type=int, default=0, help="ciclo em que ocorre um pico (+20°C)")
    args = ap.parse_args()

    topico = TOPICO_SENSOR_FMT.format(sensor_id=args.id)
    client = criar_cliente(f"sensor_{args.id}")
    client.will_set(f"{topico}/status", "offline", qos=1, retain=True)
    client.connect(BROKER, PORT, 60)
    client.loop_start()
    print(f"[{args.id}] Conectado a {BROKER}. Publicando em {topico} a cada {args.intervalo}s")

    ciclo = 0
    try:
        while True:
            ciclo += 1
            temp = args.base + random.uniform(-2.0, 2.0)
            if args.pico_em and ciclo == args.pico_em:
                temp += 20
                print(f"[{args.id}] 🔥 Injetando pico de temperatura")
            temp = round(temp, 2)

            payload = {"sensor_id": args.id, "temperatura": temp, "timestamp": time.time()}
            client.publish(topico, json.dumps(payload), qos=1)
            print(f"[{args.id}] Enviado: {temp}°C")
            time.sleep(args.intervalo)
    except KeyboardInterrupt:
        pass
    finally:
        client.loop_stop()
        client.disconnect()
        print(f"[{args.id}] Desconectado.")


if __name__ == "__main__":
    main()