from pymodbus.client import ModbusTcpClient
import struct
import time

# Configurazioni
IP = '192.168.10.10'
PORT = 502
SCAN_INTERVAL = 10  # secondi

# Dispositivi con ID Modbus e nomi
DEVICES = {
    100: 'iPC ATV',
    101: 'Motion',
    102: 'Motor Management',
    103: 'iPC Motion',
    104: 'Luci',
    105: 'Quadro Generale',
}

# Registro da leggere
REGISTERS = [
    {'name': 'Potenza attiva totale', 'address': 3060, 'type': 'float32'}
]

# Funzione per leggere Float32
def read_float32(client, addr, unit_id):
    rr = client.read_holding_registers(addr - 1, count=2, slave=unit_id)
    if rr.isError():
        return None
    try:
        return struct.unpack('>f', struct.pack('>HH', rr.registers[0], rr.registers[1]))[0]
    except Exception as e:
        print(f"Errore decodifica float32 registro {addr} da ID {unit_id}: {e}")
        return None

# Funzione principale
def main():
    client = ModbusTcpClient(IP, port=PORT)
    if not client.connect():
        print("Errore di connessione al server Modbus")
        return

    print(f"Connessione al server Modbus {IP}:{PORT} stabilita.")
    print(f"Avvio scanning ogni {SCAN_INTERVAL} secondi...\n")

    try:
        while True:
            for unit_id, name in DEVICES.items():
                print(f"--- Dispositivo {unit_id} ({name}) ---")
                for reg in REGISTERS:
                    if reg['type'] == 'float32':
                        val = read_float32(client, reg['address'], unit_id)
                    else:
                        val = None
                        print(f"Tipo registro non supportato: {reg['type']}")

                    if val is None:
                        print(f"{reg['name']} (registro {reg['address']}): Errore lettura")
                    else:
                        print(f"{reg['name']} (registro {reg['address']}): {val:.2f} W")

                print("-" * 40)

            time.sleep(SCAN_INTERVAL)

    except KeyboardInterrupt:
        print("\nInterrotto da utente. Chiusura connessione.")
    finally:
        client.close()

if __name__ == '__main__':
    main()
