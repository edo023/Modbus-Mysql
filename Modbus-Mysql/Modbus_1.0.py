from pymodbus.client import ModbusTcpClient
import struct
import time
import mysql.connector
from datetime import datetime

# Configurazioni Modbus
IP = '192.168.10.10'
PORT = 502
SCAN_INTERVAL = 10

# Configurazioni MySQL
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'password',
    'database': 'energia'
}

# Mappa ID dispositivi e nomi
DISPOSITIVI = {
    100: "iPC ATV",
    101: "Motion",
    102: "Motor Management",
    103: "iPC Motion",
    104: "Luci",
    105: "Quadro Generale"
}

def read_float32(client, addr, unit_id):
    rr = client.read_holding_registers(addr-1, count=2, slave=unit_id)
    if rr.isError():
        return None
    try:
        return struct.unpack('>f', struct.pack('>HH', rr.registers[0], rr.registers[1]))[0]
    except Exception as e:
        print(f"Errore decodifica float32 registro {addr}: {e}")
        return None

def salva_su_db(cursor, timestamp, id_disp, nome, potenza):
    cursor.execute("""
        INSERT INTO letture_potenza (timestamp, dispositivo_id, nome_dispositivo, potenza_attiva)
        VALUES (%s, %s, %s, %s)
    """, (timestamp, id_disp, nome, potenza))

def main():
    client = ModbusTcpClient(IP, port=PORT)
    if not client.connect():
        print("Errore di connessione Modbus.")
        return

    db = mysql.connector.connect(**DB_CONFIG)
    cursor = db.cursor()

    print("Inizio scansione dispositivi...")

    try:
        while True:
            timestamp = datetime.now()
            for unit_id, nome_disp in DISPOSITIVI.items():
                val = read_float32(client, 3060, unit_id)
                if val is None:
                    print(f"{nome_disp} (ID {unit_id}): Errore lettura")
                else:
                    print(f"{nome_disp} (ID {unit_id}): {val:.2f} W")
                    salva_su_db(cursor, timestamp, unit_id, nome_disp, val)
            db.commit()
            print("-" * 40)
            time.sleep(SCAN_INTERVAL)

    except KeyboardInterrupt:
        print("Interrotto da utente.")
    finally:
        cursor.close()
        db.close()
        client.close()

if __name__ == '__main__':
    main()
