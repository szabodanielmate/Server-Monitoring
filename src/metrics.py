import time
import psutil
from typing import Dict, Any, List

# Opcionális Docker import
try:
    import docker
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False


class MetricsCollector:
    def __init__(self, enable_docker: bool = False):
        self.enable_docker = enable_docker and DOCKER_AVAILABLE
        self.docker_client = None

        if self.enable_docker:
            try:
                self.docker_client = docker.from_env()
                # Gyors ping teszt a socket eléréséhez
                self.docker_client.ping()
            except Exception:
                self.docker_client = None

        # Hálózati sebesség számításához szükséges előző állapotok
        self._last_net_io = psutil.net_io_counters()
        self._last_net_time = time.time()

    def get_system_metrics(self) -> Dict[str, Any]:
        """Lekéri a CPU, RAM, lemez és hálózati adatokat."""
        now = time.time()
        elapsed = max(now - self._last_net_time, 0.001)

        # CPU & Memória
        cpu_percent = psutil.cpu_percent(interval=None)
        virtual_mem = psutil.virtual_memory()

        # Lemezfoglaltság (fő partíció /)
        disk_usage = psutil.disk_usage("/")

        # Hálózati I/O sebesség számítása (KB/s)
        current_net = psutil.net_io_counters()
        bytes_sent_sec = (current_net.bytes_sent - self._last_net_io.bytes_sent) / elapsed
        bytes_recv_sec = (current_net.bytes_recv - self._last_net_io.bytes_recv) / elapsed

        self._last_net_io = current_net
        self._last_net_time = now

        return {
            "cpu_percent": cpu_percent,
            "ram_percent": virtual_mem.percent,
            "ram_used_gb": virtual_mem.used / (1024**3),
            "ram_total_gb": virtual_mem.total / (1024**3),
            "disk_percent": disk_usage.percent,
            "disk_used_gb": disk_usage.used / (1024**3),
            "disk_total_gb": disk_usage.total / (1024**3),
            "net_upload_kbps": bytes_sent_sec / 1024,
            "net_download_kbps": bytes_recv_sec / 1024,
        }

    def get_docker_metrics(self) -> List[Dict[str, str]]:
        """Lekéri a konténerek státuszát, ha elérhető a Docker."""
        if not self.enable_docker or not self.docker_client:
            return []

        containers_data = []
        try:
            containers = self.docker_client.containers.list(all=True)
            for c in containers:
                containers_data.append({
                    "name": c.name,
                    "status": c.status,  # pl: running, exited, paused
                    "image": c.image.tags[0] if c.image.tags else "unknown"
                })
        except Exception:
            # Ha futás közben leáll a Docker socket, ne omoljon össze a script
            pass

        return containers_data