import socket
import logging
import threading
import time

class TCPTarPit:
    def __init__(self, host='0.0.0.0', port=8080):
        self.host = host
        self.port = port
        self.active_traps = 0
        self.running = False
        
    def start(self):
        self.running = True
        server_thread = threading.Thread(target=self._run_server, daemon=True)
        server_thread.start()
        logging.info(f"Tarpit Blackhole opened on {self.host}:{self.port}")
        
    def stop(self):
        self.running = False

    def _run_server(self):
        # Create a socket that simulates a TCP Tarpit
        # By setting the receive buffer to a highly restricted minimum
        # and slowly acknowledging packets, we simulate an application-layer TARPIT.
        # Note: A true TCP Window=0 is often handled at the kernel level (e.g. iptables TARPIT target),
        # but here we establish the connection and keep it in a zombie state reading 1 byte at a time.
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # Minimum receive buffer
            s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1) 
            s.bind((self.host, self.port))
            s.listen(1024)
            s.settimeout(1.0)
            
            while self.running:
                try:
                    conn, addr = s.accept()
                    self.active_traps += 1
                    t = threading.Thread(target=self._trap_client, args=(conn, addr), daemon=True)
                    t.start()
                except socket.timeout:
                    continue
                except Exception as e:
                    logging.error(f"Tarpit server error: {e}")

    def _trap_client(self, conn, addr):
        # logging.warning(f"ATTACKER TRAPPED IN TAR-PIT: {addr[0]}:{addr[1]}")
        try:
            # We never close the connection. We send bytes at extreme intervals 
            # to keep the attacker's sockets locked up waiting for data.
            conn.sendall(b"HTTP/1.1 200 OK\r\n")
            while self.running:
                time.sleep(5) 
                # Send 1 byte to keep connection alive and reset timeout on attacker end
                conn.sendall(b"X") 
        except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
            pass # Target gave up
        except Exception as e:
             # logging.error(f"Tarpit send error: {e}")
             pass
        finally:
            self.active_traps -= 1
            # logging.info(f"Attacker {addr[0]} released / died.")
            conn.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    tarpit = TCPTarPit(port=8080)
    tarpit.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        tarpit.stop()

# ==============================================================================
# IPTABLES CONFIGURATION GUIDE
# ==============================================================================
# To trap attackers before rotating the IP, run this on the ARM instance:
# 1. Route incoming HTTP/HTTPS traffic to the Python Tarpit port (e.g., 8080)
#    sudo iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 8080
#    sudo iptables -t nat -A PREROUTING -p tcp --dport 443 -j REDIRECT --to-port 8080
#
# Alternatively, to use the built-in Netfilter kernel tarpit (Zero TCP Window):
#    sudo iptables -A INPUT -p tcp -m tcp --dport 80 -j TARPIT
# ==============================================================================
