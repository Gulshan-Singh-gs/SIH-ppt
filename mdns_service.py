"""
mdns_service.py
Local Service Discovery using mDNS / Zeroconf
SIH PSC26117 — Sovereign On-Premise Agentic AI Workbench.

Key Responsibilities:
1. Advertises Sovereign AI Workbench over mDNS as `_http._tcp.local.`
   with friendly hostname `ai-workbench.local.` (or configurable).
2. Graceful fallback: If zeroconf is unavailable, network changes occur,
   or port/name collisions occur, it falls back cleanly without failing application startup.
3. Exposes only safe metadata: service name, version, host, port. Zero secret/token leakage.
4. Clean lifecycle management: unregisters cleanly on shutdown.
"""

import socket
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger("SovereignMDNS")

try:
    from zeroconf import Zeroconf, ServiceInfo, NonUniqueNameException
    ZEROCONF_AVAILABLE = True
except ImportError:
    ZEROCONF_AVAILABLE = False
    Zeroconf = None
    ServiceInfo = None


class MDNSServiceManager:
    """
    Manages mDNS advertisement lifecycle using Zeroconf.
    """

    def __init__(
        self,
        service_name: str = "Sovereign AI Workbench",
        hostname: str = "ai-workbench",
        service_type: str = "_http._tcp.local.",
        port: int = 8001
    ):
        self.service_name = service_name
        self.hostname = hostname
        self.service_type = service_type
        self.port = port
        self.zeroconf: Optional[Zeroconf] = None
        self.service_info: Optional[ServiceInfo] = None
        self.is_registered: bool = False
        self.registered_name: str = ""
        self.last_error: Optional[str] = None

    def start(self, host_ip: str, port: int) -> bool:
        """
        Registers the mDNS service advertisement.
        Returns True if successfully advertised, False if zeroconf is unavailable or failed.
        """
        self.port = port
        if not ZEROCONF_AVAILABLE:
            self.last_error = "Zeroconf library not installed or unavailable."
            logger.info("mDNS discovery disabled: Zeroconf library not available.")
            return False

        try:
            self.zeroconf = Zeroconf()
            # Convert IP to packed bytes
            ip_bytes = socket.inet_aton(host_ip)

            # Metadata properties (zero credentials or sensitive tokens)
            properties: Dict[str, Any] = {
                "name": self.service_name,
                "version": "1.0.0",
                "mode": "Sovereign_Local_Network",
                "app": "SIH_PSC26117"
            }

            # Handle server hostname format: "ai-workbench.local."
            clean_host = self.hostname.rstrip(".")
            server_domain = f"{clean_host}.local."

            # Construct unique service name
            reg_name = f"{self.service_name}.{self.service_type}"
            self.registered_name = reg_name

            self.service_info = ServiceInfo(
                type_=self.service_type,
                name=reg_name,
                addresses=[ip_bytes],
                port=self.port,
                properties=properties,
                server=server_domain
            )

            self.zeroconf.register_service(self.service_info)
            self.is_registered = True
            self.last_error = None
            logger.info(f"mDNS Service advertised: {reg_name} at {server_domain}:{self.port} ({host_ip})")
            return True

        except Exception as e:
            self.is_registered = False
            self.last_error = str(e)
            logger.warning(f"mDNS registration failed (continuing with direct IP): {e}")
            if self.zeroconf:
                try:
                    self.zeroconf.close()
                except Exception:
                    pass
                self.zeroconf = None
            return False

    def stop(self):
        """Unregisters mDNS service and cleans up Zeroconf sockets."""
        if not self.zeroconf or not self.is_registered:
            return

        try:
            if self.service_info:
                logger.info(f"Unregistering mDNS service: {self.registered_name}")
                self.zeroconf.unregister_service(self.service_info)
            self.zeroconf.close()
        except Exception as e:
            logger.warning(f"Error while unregistering mDNS service: {e}")
        finally:
            self.zeroconf = None
            self.service_info = None
            self.is_registered = False

    def get_status(self) -> Dict[str, Any]:
        return {
            "available": ZEROCONF_AVAILABLE,
            "registered": self.is_registered,
            "hostname": f"{self.hostname}.local",
            "service_name": self.registered_name or self.service_name,
            "port": self.port,
            "error": self.last_error
        }


mdns_mgr = MDNSServiceManager()
