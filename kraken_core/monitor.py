import psutil
import time
import logging

class KrakenMonitor:
    def __init__(self, threshold_pps=2000, interface='eth0'):
        self.threshold_pps = threshold_pps
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
        return counters.get(self.interface, None)

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

        is_under_attack = pps >= self.threshold_pps

        return round(pps, 2), round(mbps_rx, 2), is_under_attack

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    monitor = KrakenMonitor(threshold_pps=2000)
    while True:
        pps, mbps, attack = monitor.track()
        logging.info(f"PPS: {pps} | Bandwidth: {mbps} Mbps | Attack Detected: {attack}")
        time.sleep(1)
