# Monitoramento de Caldeira com MQTT
 
Projeto de simulação de um ambiente industrial (caldeira) monitorado por sensores de temperatura que se comunicam via **MQTT**. Os dados passam por um broker (Mosquitto), são processados pelo serviço **CAT** e os eventos gerados são exibidos pelo serviço **Alarms**.
 
**Equipe: ÁRTEMIS MENEZES, DAVID BOANERGES, VINÍCIUS VASCONCELOS, MARIA VITÓRIA DINIZ** 
**Vídeo de demonstração:** 

### Componentes
 
| Componente | Arquivo | Função |
|---|---|---|
| **Sensor simulado** | `sensor.py` | Publica a temperatura periodicamente (padrão: 60 s). É possível executar vários sensores ao mesmo tempo, cada um com seu `--id`. |
| **CAT** (Compute Average Temperature) | `cat.py` | Assina os tópicos dos sensores, calcula a média das leituras dos últimos **120 s** a cada **60 s** e publica eventos. |
| **Alarms** | `alarms.py` | Assina os eventos do CAT e exibe os alarmes em uma interface gráfica (e no console). |
| **Configuração** | `config.py` | Broker, porta, tópicos e limites em um único lugar. |
 
### Tópicos MQTT
 
| Tópico | Publicado por | Assinado por | Conteúdo |
|---|---|---|---|
| `caldeira/sensores/<id>/temperatura` | Sensores | CAT (via wildcard `+`) | `{"sensor_id", "temperatura", "timestamp"}` |
| `caldeira/sensores/<id>/temperatura/status` | Sensores (LWT) | — | `"offline"` caso o sensor caia |
| `caldeira/cat/media` | CAT | Alarms | `{"media", "amostras", "sensores", "timestamp"}` |
| `caldeira/cat/eventos` | CAT | Alarms | `{"tipo", "mensagem", "media", "timestamp"}` |
 
### Regras
 
O CAT publica dois tipos de evento em `caldeira/cat/eventos`:
 
1. **`AUMENTO_REPENTINO`** – quando as duas últimas médias calculadas diferem em **5 °C ou mais**.
2. **`TEMPERATURA_ALTA`** – quando a média calculada ultrapassa **200 °C**.
O serviço **Alarms** monitora esses eventos e publica o alarme na interface gráfica.
 
---
 
## Pré-requisitos
 
- **Python 3.8+** (com Tkinter – já incluso no Python do Windows/macOS; no Linux: `sudo apt install python3-tk`)
- **Mosquitto** (broker MQTT)
- Biblioteca **paho-mqtt**
### Instalando o Mosquitto
 
**Windows**
1. Baixe o instalador em <https://mosquitto.org/download/> (versão Windows 64 bits).
2. Instale com as opções padrão.
3. Abra o `services.msc`, procure **Mosquitto Broker** e clique em *Iniciar* (ou rode `net start mosquitto` em um terminal como administrador).

**Linux (Ubuntu/Debian)**
```bash
sudo apt update
sudo apt install mosquitto mosquitto-clients
sudo systemctl enable --now mosquitto
```
 
**macOS**
```bash
brew install mosquitto
brew services start mosquitto
```
 
### Instalando as dependências Python
 
```bash
git clone <URL-DO-SEU-REPOSITORIO>
cd mqtt-caldeira
python -m venv venv
# Windows:  venv\Scripts\activate
# Linux/Mac: source venv/bin/activate
pip install -r requirements.txt
```
 
---
 
## Como executar
 
Abra **um terminal para cada componente** (com o Mosquitto já em execução):
 
```bash
# 1) Serviço CAT
python cat.py
 
# 2) Serviço Alarms (abre a interface gráfica)
python alarms.py
 
# 3) Sensores (quantos quiser, cada um com ID diferente)
python sensor.py --id S1
python sensor.py --id S2
python sensor.py --id S3
```

### Opções do sensor
 
| Argumento | Padrão | Descrição |
|---|---|---|
| `--id` | aleatório | Identificador único do sensor |
| `--intervalo` | `60` | Segundos entre cada envio |
| `--base` | `30` | Temperatura base da simulação (±2 °C de variação) |
| `--pico-em` | `0` (desligado) | Número do ciclo em que ocorre um pico de +20 °C |
 
### Teste manual com os clientes do Mosquitto
 
```bash
# Observar todo o tráfego do projeto
mosquitto_sub -t "caldeira/#" -v
 
# Simular um sensor enviando temperatura crítica
mosquitto_pub -t caldeira/sensores/TESTE/temperatura \
  -m '{"sensor_id":"TESTE","temperatura":215}'
```
 
---
 
## O que esperar na execução
 
1. Os **sensores** imprimem `Enviado: XX.XX°C` a cada ciclo.
2. O **CAT** imprime cada leitura recebida e, a cada ciclo de cálculo, a média da janela de 120 s.
3. Quando uma regra é violada, o CAT publica um evento e o **Alarms** adiciona uma linha colorida na interface:
   - **Aumento repentino** – variação ≥ 5 °C entre as duas últimas médias
   - **Temperatura alta** – média > 200 °C
---