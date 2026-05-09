import logging
import time
import threading
import os
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

# Suppress Flask request logs
logging.getLogger('werkzeug').setLevel(logging.ERROR)

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
            "logs": [],
            "tarpitted_ips": []
        }
        
        # Attached custom log handler to root logger
        state_handler = StateLogHandler(self.state)
        state_handler.setFormatter(logging.Formatter('%(asctime)s | KRAKEN | %(levelname)s | %(message)s'))
        logging.getLogger().addHandler(state_handler)

        # Lowered threshold to 300 PPS and 10 connections for easier exhibition testing
        self.monitor = KrakenMonitor(threshold_pps=300, max_conn_per_ip=10, interface='eth0') 
        self.shifter = OracleShifter()
        self.tarpit = TCPTarPit(port=8080)
        
        self.is_shifting = False


    def trigger_shift_protocol(self, attacker_ip=None):
        if self.is_shifting:
            return
            
        self.is_shifting = True
        self.state["status"] = "DEFENDING (ACTIVE RESPONSE)"
        
        if attacker_ip:
            logging.critical(f"TARGET ACQUIRED: {attacker_ip} via active connection flood.")
        else:
            logging.critical(f"RED ALERT: Volumetric Attack detected. PPS Exceeded Threshold.")
            
        # --- 1. THE TRAP (IPTABLES) ---
        if attacker_ip and attacker_ip not in self.state.get("tarpitted_ips", []):
            logging.warning(f"Isolating {attacker_ip} -> TCP to Tarpit, DROPPING everything else.")
            try:
                # 1. Force all TCP connections from this IP into the local TCP Port 8080 (Tar-Pit)
                os.system(f"sudo iptables -t nat -I PREROUTING 1 -s {attacker_ip} -p tcp -j REDIRECT --to-port 8080")
                
                # 2. Hard DROP for everything else (UDP/ICMP) to kill raw bandwidth floods
                os.system(f"sudo iptables -I INPUT 1 -s {attacker_ip} -p udp -j DROP")
                os.system(f"sudo iptables -I INPUT 1 -s {attacker_ip} -p icmp -j DROP")
                
                # 3. As a last resort fallback, if we just want to totally blackhole them:
                # uncommenting the below will completely drop their traffic at the kernel level
                # os.system(f"sudo iptables -I INPUT 1 -s {attacker_ip} -j DROP")
                
                if "tarpitted_ips" not in self.state:
                    self.state["tarpitted_ips"] = []
                self.state["tarpitted_ips"].append(attacker_ip)
                logging.info(f"IPTables isolation active. {attacker_ip} is now trapped/blacklisted.")
            except Exception as e:
                logging.error(f"Failed to isolate attacker: {e}")
                
        time.sleep(1)
        
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
            pps, mbps, attack, attacker_ip = self.monitor.track()
            self.state["pps"] = pps
            self.state["bandwidth"] = mbps
            self.state["active_traps"] = self.tarpit.active_traps
            
            # Status update for smaller spikes
            if pps > 100 and not attack and not self.is_shifting:
                self.state["status"] = "ELEVATED TRAFFIC"
            elif not self.is_shifting:
                self.state["status"] = "SECURE"
            
            if attack and not self.is_shifting:
                threading.Thread(target=self.trigger_shift_protocol, args=(attacker_ip,), daemon=True).start()
                
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
