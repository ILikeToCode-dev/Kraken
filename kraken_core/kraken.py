import logging
import time
import threading
from monitor import KrakenMonitor
from shifter import OracleShifter
from tarpit import TCPTarPit
from flask import Flask, jsonify
from flask_cors import CORS
from logging.handlers import MemoryHandler

# Initialize basic config first
logging.basicConfig(level=logging.INFO, format='%(asctime)s | KRAKEN | %(levelname)s | %(message)s')

class StateLogHandler(logging.Handler):
    def __init__(self, state_dict):
        super().__init__()
        self.state_dict = state_dict

    def emit(self, record):
        log_entry = self.format(record)
        if "logs" not in self.state_dict:
            self.state_dict["logs"] = []
        self.state_dict["logs"].append(log_entry)
        # Keep only the last 100 logs in memory
        if len(self.state_dict["logs"]) > 100:
            self.state_dict["logs"].pop(0)

app = Flask(__name__)
CORS(app)

class KrakenCore:
    def __init__(self):
        self.state = {
            "current_ip": "130.61.12.34", # Starting Mock IP
            "pps": 0,
            "bandwidth": 0,
            "active_traps": 0,
            "rotations": [],
            "status": "SECURE",
            "logs": []
        }
        
        # Attach the custom log handler to root logger
        state_handler = StateLogHandler(self.state)
        state_handler.setFormatter(logging.Formatter('%(asctime)s | KRAKEN | %(levelname)s | %(message)s'))
        logging.getLogger().addHandler(state_handler)

        self.monitor = KrakenMonitor(threshold_pps=2000, interface='eth0') # Set interface
        self.shifter = OracleShifter()
        self.tarpit = TCPTarPit(port=8080)
        
        self.is_shifting = False


    def trigger_shift_protocol(self):
        if self.is_shifting:
            return
            
        self.is_shifting = True
        self.state["status"] = "DEFENDING (SHIFTING)"
        logging.critical(f"RED ALERT: PPS exceeded {self.monitor.threshold_pps}. Initiating IP Shift!")
        
        # 1. Spin up the tarpit (if not already running) to catch ongoing connections
        # IPTables would redirect port 80/443 to 8080 during this transition phase.
        
        # 2. Call OCI SDK to rotate IP
        old_ip = self.state["current_ip"]
        new_ip = self.shifter.shift_ip(vnic_id="ocid1.vnic...", current_public_ip_id="ocid1.publicip...")
        
        if new_ip:
            self.state["current_ip"] = new_ip
            # 3. Update DNS
            self.shifter.update_dns(new_ip)
            
            # Log history
            self.state["rotations"].insert(0, {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "from_ip": old_ip,
                "to_ip": new_ip,
                "trigger_pps": self.state["pps"]
            })
            logging.info(f"SHIFT COMPLETE. New Identity: {new_ip}")
        
        # Cooldown period before allowing another shift
        time.sleep(15) 
        self.state["status"] = "SECURE"
        self.is_shifting = False

    def run_engine(self):
        self.tarpit.start()
        while True:
            pps, mbps, attack = self.monitor.track()
            self.state["pps"] = pps
            self.state["bandwidth"] = mbps
            self.state["active_traps"] = self.tarpit.active_traps
            
            if attack and not self.is_shifting:
                threading.Thread(target=self.trigger_shift_protocol, daemon=True).start()
                
            time.sleep(1)

kraken = KrakenCore()

@app.route('/api/stats')
def get_stats():
    return jsonify(kraken.state)

if __name__ == "__main__":
    # Start the core engine loop in a background thread
    engine_thread = threading.Thread(target=kraken.run_engine, daemon=True)
    engine_thread.start()
    
    # Run Flask Dashboard API
    app.run(host='0.0.0.0', port=5000)
