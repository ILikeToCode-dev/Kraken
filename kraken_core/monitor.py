import psutil
import time
import logging
from collections import defaultdict

class KrakenMonitor:
    def __init__(self, threshold_pps=500, max_conn_per_ip=20, interface='eth0'):
        self.threshold_pps = threshold_pps
        self.max_conn_per_ip = max_conn_per_ip
        self.interface = interface
        self.last_packets = 0
        self.last_bytes_recv = 0
        self.last_time = time.time()
        
        # Initialize
        counters = self._get_counters()
        if counters:
            self.last_packets = counters.packets_recv
            self.last_bytes_recv = counters.bytes_recv

    def _get_counters(self):
        counters = psutil.net_io_counters(pernic=True)
        if self.interface in counters:
            return counters[self.interface]
        # Fallback if eth0 is missing (like enp0s3 on some Oracle instances)
        total_recv = sum(c.packets_recv for n, c in counters.items() if n != 'lo')
        total_bytes = sum(c.bytes_recv for n, c in counters.items() if n != 'lo')
        class DummyCounter:
            def __init__(self, p, b):
                self.packets_recv = p
                self.bytes_recv = b
        return DummyCounter(total_recv, total_bytes)

    def track(self):
        """
        Calculates PPS (Packets Per Second) and Bandwidth.
        Returns (pps, mbps_rx, is_under_attack)
        """
        counters = self._get_counters()
        current_time = time.time()
        
        if not counters:
            logging.error(f"Interface {self.interface} not found.")
            return 0, 0.0, False

        elapsed = current_time - self.last_time
        if elapsed == 0:
            return 0, 0.0, False
            
        packets_recv = counters.packets_recv
        bytes_recv = counters.bytes_recv

        pps = (packets_recv - self.last_packets) / elapsed
        bps_rx = (bytes_recv - self.last_bytes_recv) / elapsed
        mbps_rx = bps_rx * 8 / 1_000_000

        self.last_packets = packets_recv
        self.last_bytes_recv = bytes_recv
        self.last_time = current_time

        # APP-LAYER ATTACK DETECTION (Active Connection Count & Traffic Source)
        attacker_ip = None
        try:
            conns = psutil.net_connections(kind='tcp')
            ip_counts = defaultdict(int)
            for c in conns:
                if c.raddr:
                    ip = c.raddr.ip
                    # Ignore local loops and ngrok
                    if ip not in ('127.0.0.1', '::1', '0.0.0.0'):
                        ip_counts[ip] += 1
            
            if ip_counts:
                # Find the IP with the most active connections
                top_ip, count = max(ip_counts.items(), key=lambda x: x[1])
                
                # If they have too many parallel connections, tag them
                if count >= self.max_conn_per_ip:
                    attacker_ip = top_ip
                # Or, if we are under a volumetric flood, just tag the top IP anyway
                elif pps >= self.threshold_pps:
                    attacker_ip = top_ip
        except Exception:
            pass

        is_under_attack = pps >= self.threshold_pps or attacker_ip is not None

        return round(pps, 2), round(mbps_rx, 2), is_under_attack, attacker_ip

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    monitor = KrakenMonitor(threshold_pps=2000)
    while True:
        pps, mbps, attack, attacker_ip = monitor.track()
        logging.info(f"PPS: {pps} | Bandwidth: {mbps} Mbps | Attack Detected: {attack} | Attacker IP: {attacker_ip}")
        time.sleep(1)
