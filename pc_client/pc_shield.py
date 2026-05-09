import requests
import time
import platform
import subprocess
import logging

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s | LOCAL SHIELD | %(levelname)s | %(message)s')

# Set this to your NGROK or Oracle VM IP URL
KRAKEN_API_URL = "https://unbridle-bootie-vitality.ngrok-free.dev/api/stats"
POLL_INTERVAL = 5 # Check for new threats every 5 seconds

def block_ip_locally(ip):
    """
    Applies OS-level firewall rules to block the IP from ever touching your personal PC.
    """
    sys_os = platform.system()
    try:
        if sys_os == "Windows":
            # Windows Defender Firewall (Requires Admin/UAC)
            cmd_in = f'netsh advfirewall firewall add rule name="Kraken Block IN {ip}" dir=in action=block remoteip={ip}'
            cmd_out = f'netsh advfirewall firewall add rule name="Kraken Block OUT {ip}" dir=out action=block remoteip={ip}'
            subprocess.run(cmd_in, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(cmd_out, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
        elif sys_os == "Linux":
            # Linux IPTables (Requires sudo)
            cmd = f'sudo iptables -I INPUT 1 -s {ip} -j DROP'
            subprocess.run(cmd, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
        elif sys_os == "Darwin":
            # macOS - Packet Filter (pf)
            logging.warning(f"macOS automatic blocking restricted by SIP. Run: sudo route -n add -host {ip} 127.0.0.1 -reject")
            return

        logging.critical(f"SHIELD ACTIVATED: {ip} is now hard-blocked on your local PC.")
    except subprocess.CalledProcessError:
        logging.error(f"Failed to block {ip}. Did you run this script as Administrator/Root?")
    except Exception as e:
        logging.error(f"Error executing firewall command: {e}")

def main():
    print(f"""
    ===================================================
     KRAKEN LOCAL SHIELD - PC PROTECTION AGENT
    ===================================================
    Targeting Oracle Bait Server: {KRAKEN_API_URL}
    Polling Frequency: {POLL_INTERVAL} seconds
    
    WARNING: Run this script as Administrator (Windows) 
    or Root (Linux) so it can modify your firewall.
    ===================================================
    """)
    
    blocked_ips = set()
    
    while True:
        try:
            # Ngrok requires this header to bypass the warning page
            headers = {"ngrok-skip-browser-warning": "true", "Content-Type": "application/json"}
            
            response = requests.get(KRAKEN_API_URL, headers=headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                tarpitted_ips = data.get("tarpitted_ips", [])
                
                # Check if the Oracle VM caught any new attackers
                for ip in tarpitted_ips:
                    if ip not in blocked_ips:
                        logging.warning(f"NEW THREAT DETECTED BY BAIT SERVER: {ip}")
                        block_ip_locally(ip)
                        blocked_ips.add(ip)
            else:
                logging.warning(f"Bait server returned HTTP {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            logging.error(f"Lost connection to Oracle Bait Server. Retrying in {POLL_INTERVAL}s...")
            
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
