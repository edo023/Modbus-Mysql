import json
import time
import struct
import csv
import mysql.connector
from pymodbus.client import ModbusTcpClient
from datetime import datetime

CONFIG_FILE = "modbus_config.json"

def carica_config():
    config_di_default = {
        "devices": [],
        "db": {
            "host": "localhost",
            "user": "root",
            "password": "password",
            "database": "progetto",
            "table": "dati_variabili"
        },
        "ip": "127.0.0.1",
        "port": 502,
        "scan_interval": 5.0,
        "autostart": False
    }

    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
            # Riempie eventuali chiavi mancanti
            for k, v in config_di_default.items():
                if k not in config:
                    config[k] = v
            return config
    except (FileNotFoundError, json.JSONDecodeError):
        salva_config(config_di_default)
        return config_di_default
     

def salva_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

def importa_reg_da_csv(percorso_csv, device):
    try:
        with open(percorso_csv, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            nuove = []
            esistenti = {r['name'] for r in device['registers']}
            for row in reader:
                if 'name' in row and 'address' in row and 'type' in row:
                    if row['name'] not in esistenti:
                        nuove.append({
                            "name": row['name'],
                            "address": int(row['address']),
                            "type": row['type'].lower()
                        })
            if nuove:
                device['registers'].extend(nuove)
                print(f"✅ {len(nuove)} registri importati.")
            else:
                print("⚠️ Nessun nuovo registro valido trovato.")
    except Exception as e:
        print(f"❌ Errore importazione CSV: {e}")

def menu():
    while True:
        print("""
╔════════════════════════════════════╗
║    GATEWAY MODBUS TCP → MySQL      ║
╚════════════════════════════════════╝
1. Avvia comunicazione
2. Impostazioni
3. Esci
""")
        scelta = input("Scegli un'opzione: ")
        if scelta == "1":
            avvia_gateway()
        elif scelta == "2":
            modifica_config()
        elif scelta == "3":
            print("Uscita.")
            break
        else:
            print("❌ Opzione non valida.")

def modifica_config():
    config = carica_config()
    while True:
        print("""
--- Impostazioni ---
1. Configura dispositivi
2. Configurazione gateway
3. Configura database
4. Avvio automatico
5. Torna al menu principale
""")
        scelta = input("Scegli un'opzione: ")
        if scelta == "1":
            for i, d in enumerate(config['devices']):
                tabella = d.get('table', config['db']['table'])
                print(f"{i+1}. ID {d['unit_id']} - {d['name']} (Tabella: {tabella})")
            print("a. Aggiungi dispositivo")
            print("d. Elimina dispositivo")
            print("t. Torna indietro")
            azione = input("Scegli: ")
            if azione == "a":
                nome = input("Nome dispositivo: ")
                unit_id = int(input("ID Modbus: "))
                tabella = input(f"Tabella MySQL [{config['db']['table']}]: ") or config['db']['table']
                config['devices'].append({"name": nome, "unit_id": unit_id, "table": tabella, "registers": []})
            elif azione == "d":
                try:
                    idx = int(input("Indice da rimuovere: ")) - 1
                    config['devices'].pop(idx)
                    print("✅ Dispositivo rimosso.")
                except:
                    print("❌ Errore nella rimozione.")
            elif azione == "t":
                continue
            else:
                try:
                    idx = int(azione) - 1
                    device = config['devices'][idx]
                    while True:
                        print("\nRegistri attuali:")
                        for i, reg in enumerate(device['registers']):
                            print(f"{i+1}. {reg['name']} - {reg['address']} ({reg['type']})")
                        print("""
a. Aggiungi registro
r. Rimuovi registro
i. Importa da CSV
t. Torna indietro
""")
                        sub = input("Scegli: ").lower()
                        if sub == "a":
                            name = input("Nome: ")
                            addr = int(input("Indirizzo: "))
                            tipo = input("Tipo (float32, int16, bool): ").lower()
                            device['registers'].append({"name": name, "address": addr, "type": tipo})
                        elif sub == "r":
                            try:
                                ridx = int(input("Indice: ")) - 1
                                device['registers'].pop(ridx)
                            except:
                                print("Errore rimozione.")
                        elif sub == "i":
                            percorso = input("Percorso CSV [registri.csv]: ") or "registri.csv"
                            importa_reg_da_csv(percorso, device)
                        elif sub == "t":
                            break
                except:
                    print("Indice non valido.")
        elif scelta == "2":
            config['ip'] = input(f"IP [{config['ip']}]: ") or config['ip']
            config['port'] = int(input(f"Porta [{config['port']}]: ") or config['port'])
            config['scan_interval'] = float(input(f"Scan interval (s) [{config['scan_interval']}]: ") or config['scan_interval'])
        elif scelta == "3":
            db = config['db']
            db['host'] = input(f"Host DB [{db['host']}]: ") or db['host']
            db['user'] = input(f"Utente DB [{db['user']}]: ") or db['user']
            db['password'] = input(f"Password DB [*****]: ") or db['password']
            db['database'] = input(f"Database [{db['database']}]: ") or db['database']
            db['table'] = input(f"Tabella default [{db['table']}]: ") or db['table']
        elif scelta == "4":
            attuale = config.get("autostart", False)
            nuova = input(f"Avvio automatico all'accensione del PC (attuale: {attuale}) [s/n]: ").lower()
            if nuova == "s":
                config["autostart"] = True
                abilita_avvio_automatico()
            elif nuova == "n":
                config["autostart"] = False
                disabilita_avvio_automatico()
            else:
                print("❌ Scelta non valida.")
        elif scelta == "5":
            break
        else:
            print("Opzione non valida.")

        salva_config(config)
        print("✅ Configurazione salvata.")

def read_register(client, addr, unit_id, tipo):
    try:
        if tipo == 'float32':
            rr = client.read_holding_registers(addr - 1, count=2, slave=unit_id)
            if rr.isError(): return None
            return struct.unpack('>f', struct.pack('>HH', *rr.registers))[0]

        elif tipo == 'int16':
            rr = client.read_holding_registers(addr - 1, count=1, slave=unit_id)
            if rr.isError(): return None
            return struct.unpack('>h', struct.pack('>H', rr.registers[0]))[0]

        elif tipo == 'uint16':
            rr = client.read_holding_registers(addr - 1, count=1, slave=unit_id)
            if rr.isError(): return None
            return rr.registers[0]

        elif tipo == 'int32':
            rr = client.read_holding_registers(addr - 1, count=2, slave=unit_id)
            if rr.isError(): return None
            return struct.unpack('>i', struct.pack('>HH', *rr.registers))[0]

        elif tipo == 'uint32':
            rr = client.read_holding_registers(addr - 1, count=2, slave=unit_id)
            if rr.isError(): return None
            return struct.unpack('>I', struct.pack('>HH', *rr.registers))[0]

        elif tipo == 'int64':
            rr = client.read_holding_registers(addr - 1, count=4, slave=unit_id)
            if rr.isError(): return None
            return struct.unpack('>q', struct.pack('>HHHH', *rr.registers))[0]

        elif tipo == 'uint64':
            rr = client.read_holding_registers(addr - 1, count=4, slave=unit_id)
            if rr.isError(): return None
            return struct.unpack('>Q', struct.pack('>HHHH', *rr.registers))[0]

        elif tipo == 'ascii':
            rr = client.read_holding_registers(addr - 1, count=4, slave=unit_id)
            if rr.isError(): return None
            return ''.join(chr((w >> 8) & 0xFF) + chr(w & 0xFF) for w in rr.registers).strip()

        elif tipo == 'bitmap':
            rr = client.read_holding_registers(addr - 1, count=1, slave=unit_id)
            if rr.isError(): return None
            return format(rr.registers[0], '016b')

        elif tipo == 'datetime':
            rr = client.read_holding_registers(addr - 1, count=4, slave=unit_id)
            if rr.isError(): return None
            raw = struct.pack('>HHHH', *rr.registers)
            year, month, day, hour, minute, second = struct.unpack('>HBBBBB', raw[:7])
            return f"{year:04d}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}"

        elif tipo == 'bool':
            rr = client.read_coils(addr - 1, count=1, unit=unit_id)
            if rr.isError(): return None
            return rr.bits[0]

        else:
            print(f"Tipo {tipo} non supportato.")
            return None

    except Exception as e:
        print(f"Errore lettura registro {addr} tipo {tipo} da ID {unit_id}: {e}")
        return None

def avvia_gateway():
    config = carica_config()
    db_cfg = config['db']
    client = ModbusTcpClient(config['ip'], port=config['port'])
    if not client.connect():
        print("❌ Connessione Modbus fallita")
        return

    try:
        db = mysql.connector.connect(
            host=db_cfg['host'],
            user=db_cfg['user'],
            password=db_cfg['password'],
            database=db_cfg['database']
        )
        cursor = db.cursor()

        # Creo tabelle per ogni device se non esistono
        for d in config['devices']:
            table_name = d.get('table', db_cfg['table'])
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    timestamp DATETIME,
                    dispositivo_id INT,
                    nome_dispositivo VARCHAR(255),
                    nome_variabile VARCHAR(255),
                    valore FLOAT
                )
            """)
        db.commit()
    except Exception as e:
        print(f"❌ Connessione DB fallita: {e}")
        return

    print("✅ Avvio comunicazione...")
    try:
        while True:
            timestamp = datetime.now()
            for d in config['devices']:
                table_name = d.get('table', db_cfg['table'])
                for reg in d['registers']:
                    val = read_register(client, reg['address'], d['unit_id'], reg['type'])

                    if val is not None:
                        print(f"{d['name']} (ID {d['unit_id']}) - {reg['name']}: {val}")
                        try:
                            cursor.execute(f"""
                                INSERT INTO {table_name} (timestamp, dispositivo_id, nome_dispositivo, nome_variabile, valore)
                                VALUES (%s, %s, %s, %s, %s)
                            """, (timestamp, d['unit_id'], d['name'], reg['name'], val))
                            db.commit()
                        except Exception as e:
                            print(f"Errore inserimento DB: {e}")
                    else:
                        print(f"Errore lettura {reg['name']} da {d['name']}")

            print("-" * 40)
            time.sleep(config['scan_interval'])
    except KeyboardInterrupt:
        print("Interrotto da utente.")
    finally:
        cursor.close()
        db.close()
        client.close()

    
import os
import sys
import shutil

def get_startup_folder():
    return os.path.join(os.getenv('APPDATA'), 'Microsoft\\Windows\\Start Menu\\Programs\\Startup')

def abilita_avvio_automatico():
    nome_script = os.path.basename(sys.argv[0])
    startup_path = os.path.join(get_startup_folder(), "gatewayMod_autostart.bat")

    with open(startup_path, 'w') as f:
        f.write(f'@echo off\npython "{os.path.abspath(nome_script)}"\n')
    print(f"✅ Avvio automatico abilitato. File creato: {startup_path}")

def disabilita_avvio_automatico():
    startup_path = os.path.join(get_startup_folder(), "gatewayMod_autostart.bat")
    if os.path.exists(startup_path):
        os.remove(startup_path)
        print("✅ Avvio automatico disabilitato.")
    else:
        print("⚠️ Nessun file di avvio trovato.")


if __name__ == "__main__":
    config = carica_config()
    if config.get("autostart", False):
        avvia_gateway()
    else:
        menu()