"""Serviço Alarms: assina os eventos do CAT e exibe alarmes (GUI Tkinter + console)."""
import json
import time
import tkinter as tk
from tkinter import ttk

from config import BROKER, PORT, TOPICO_EVENTOS, TOPICO_MEDIA, criar_cliente

CORES = {"TEMPERATURA_ALTA": "#ff5555", "AUMENTO_REPENTINO": "#ffb86c"}
ROTULOS = {"TEMPERATURA_ALTA": "🔥 Temperatura alta", "AUMENTO_REPENTINO": "⚠️ Aumento repentino"}


class AlarmsGUI:
    def __init__(self, root):
        self.root = root
        root.title("Painel de Alarmes - Caldeira")
        root.geometry("760x440")
        root.configure(bg="#1e1e2e")

        tk.Label(root, text="🚨 Monitoramento de Alarmes", font=("Helvetica", 16, "bold"),
                 fg="#f38ba8", bg="#1e1e2e").pack(pady=8)

        self.lbl_media = tk.Label(root, text="Média atual: --", font=("Helvetica", 12),
                                  fg="#cdd6f4", bg="#1e1e2e")
        self.lbl_media.pack()

        cols = ("Hora", "Tipo", "Detalhes", "Média")
        self.tree = ttk.Treeview(root, columns=cols, show="headings", height=14)
        for c, w in zip(cols, (80, 170, 400, 80)):
            self.tree.heading(c, text=c)
            self.tree.column(c, width=w)
        for tipo, cor in CORES.items():
            self.tree.tag_configure(tipo, background=cor, foreground="black")
        self.tree.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.client = criar_cliente("servico_alarms")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(BROKER, PORT, 60)
        self.client.loop_start()               
        root.protocol("WM_DELETE_WINDOW", self.fechar)

    def on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            print("[Alarms] Conectado.")
            client.subscribe([(TOPICO_EVENTOS, 1), (TOPICO_MEDIA, 0)])

    def on_message(self, client, userdata, msg):
        try:
            d = json.loads(msg.payload.decode())
        except json.JSONDecodeError:
            return
        if msg.topic == TOPICO_MEDIA:
            self.root.after(0, lambda: self.lbl_media.config(
                text=f"Média atual: {d['media']}°C ({d['amostras']} amostras)"))
        else:
            print(f"[Alarms] 🚨 {d['tipo']}: {d['mensagem']}")
            self.root.after(0, self.adicionar, d)

    def adicionar(self, d):
        hora = time.strftime("%H:%M:%S")
        self.tree.insert("", 0, values=(hora, ROTULOS.get(d["tipo"], d["tipo"]),
                                        d["mensagem"], f"{d['media']}°C"), tags=(d["tipo"],))

    def fechar(self):
        self.client.loop_stop()
        self.client.disconnect()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    AlarmsGUI(root)
    root.mainloop()