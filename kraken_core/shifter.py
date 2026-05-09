import oci
import requests
import logging
import time

class OracleShifter:
    def __init__(self, config_profile="DEFAULT"):
        # Uses standard ~/.oci/config profile for auth
        try:
            self.config = oci.config.from_file(profile_name=config_profile)
            self.vnic_client = oci.core.VirtualNetworkClient(self.config)
        except Exception as e:
            logging.warning(f"OCI SDK not configured properly (expected in exhibition/local test): {e}")
            self.vnic_client = None

        # Placeholders for DNS updates
        self.cloudflare_api_token = "YOUR_CLOUDFLARE_API_TOKEN"
        self.zone_id = "YOUR_ZONE_ID"
        self.record_id = "YOUR_RECORD_ID"
        self.domain = "kraken.example.com"

    def shift_ip(self, vnic_id, current_public_ip_id):
        """
        Detaches the current public IP and requests a new one from the Oracle pool.
        """
        logging.warning("Initiating OCI Mapped IP Shift Sequence...")
        
        if not self.vnic_client:
            logging.warning("[MOCK] OCI Client unavailable. Simulating IP Shift.")
            time.sleep(2)
            return "192.168.1.100" # Returns mock ip in exhibition test env
            
        try:
            # 1. Detach old IP
            logging.info(f"Detaching Public IP ID: {current_public_ip_id}")
            self.vnic_client.delete_public_ip(current_public_ip_id)
            
            # 2. Allocate and attach new Ephemeral Public IP to the VNIC's private IP
            # (Note: Assumes VNIC has a primary private IP we target)
            vnic = self.vnic_client.get_vnic(vnic_id).data
            
            create_ip_details = oci.core.models.CreatePublicIpDetails(
                compartment_id=self.config["tenancy"],
                lifetime="EPHEMERAL",
                private_ip_id=vnic.private_ip_id
            )
            
            new_ip_response = self.vnic_client.create_public_ip(create_ip_details)
            new_ip_address = new_ip_response.data.ip_address
            logging.info(f"Successfully clamped new Oracle Public IP: {new_ip_address}")
            return new_ip_address
            
        except Exception as e:
            logging.error(f"Error shifting OCI IP: {e}")
            return None

    def update_dns(self, new_ip):
        """
        Instantly loops the new IP to the DNS A-Record via Cloudflare API.
        """
        logging.info(f"Updating DNS A-Record for {self.domain} to {new_ip}...")
        url = f"https://api.cloudflare.com/client/v4/zones/{self.zone_id}/dns_records/{self.record_id}"
        
        headers = {
            "Authorization": f"Bearer {self.cloudflare_api_token}",
            "Content-Type": "application/json"
        }
        
        data = {
            "type": "A",
            "name": self.domain,
            "content": new_ip,
            "ttl": 60,  # 1 min TTL for quick shifts
            "proxied": False  # Keep raw IP exposed for the tar-pit demonstration if desired
        }
        
        # Uncomment in production
        # response = requests.put(url, headers=headers, json=data)
        # if response.status_code == 200:
        #     logging.info("DNS Update successful.")
        # else:
        #     logging.error(f"DNS Update failed: {response.text}")
        logging.info("[MOCK] DNS forcefully updated and propagated.")
