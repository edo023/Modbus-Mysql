🔌 Modbus TCP → MySQL Gateway (Python)
Questo progetto è un gateway industriale sviluppato in Python per acquisire dati da dispositivi Modbus TCP e salvarli in un database MySQL, utile per applicazioni di monitoraggio energetico, supervisione impianti o analisi dati storici.

**IMPORTANTE** è un progetto opensource e in quanto tale si accettano migliorie e suggerimenti.

🚀 Funzionalità principali
Multi-dispositivo: supporta più device Modbus TCP configurabili individualmente (ID, registri, tabella).

Compatibile con diversi tipi di dato: float32, int16, int32, uint32, ascii, bool, datetime ecc.

Salvataggio dati su MySQL: inserimento automatico dei dati letti in tabelle SQL, una per ogni dispositivo.

Configurazione persistente: parametri salvati in un file modbus_config.json, facilmente modificabile.

Interfaccia CLI: menu testuale per configurare dispositivi, database, registri e parametri di scansione.

Importazione da CSV: aggiunta rapida dei registri tramite file registri.csv.

Avvio automatico (opzionale): per sistemi Windows, possibilità di avviare lo script all'accensione del PC.

Gestione errori: robusto contro problemi di connessione o fallimenti MySQL, con messaggi chiari.

🛠️ Requisiti
Python 3.7+

Librerie:

pymodbus

mysql-connector-python

Installazione delle dipendenze:

bash
Copia
Modifica
pip install pymodbus mysql-connector-python
📂 File principali
main.py: script principale con menu e ciclo di acquisizione.

modbus_config.json: file di configurazione persistente.

registri.csv: file CSV opzionale per importare registri.

▶️ Esecuzione
bash
Copia
Modifica
python main.py
Oppure attiva l’avvio automatico da menu per sistemi HMI/PC industriali Windows. (funzione implementata ma non ancora operativa)
