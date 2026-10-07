import os
import time
import psutil
from typing import Dict, Any, List

from src.config import Config

try:
    import docker
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False


class MetricsCollector:
    # Figyelmen kívül hagyandó virtuális, belső és ideiglenes fájlrendszerek
    IGNORED_FS_TYPES = {
        "squashfs", "tmpfs", "devtmpfs", "overlay", "iso9660",
        "nullfs", "autofs", "proc", "sysfs", "devpts"
    }

    # Statikus, kis méretű rendszerkötetek, amiket alapból nem érdemes figyelni
    IGNORED_MOUNTS = {"/boot", "/boot/efi"}

    def __init__(self, enable_docker: bool = False):
        self.enable_docker = enable_docker and DOCKER_AVAILABLE
        self.docker_client = None

        if self.enable_docker:
            try:
                self.docker_client = docker.from_env()
                self.docker_client.ping()
            except Exception:
                self.docker_client = None

        # Hálózati I/O sebesség követése
        self._last_net_io = psutil.net_io_counters()
        self._last_net_time = time.time()

    def _get_disks_metrics(self) -> List[Dict[str, Any]]:
        """Automatikusan felderíti az összes valós merevlemezt és partíciót, szűrve a konfigurációra."""
        disks = []
        seen_mounts = set()

        try:
            partitions = psutil.disk_partitions(all=False)
        except Exception:
            partitions = []

        # Tisztított, normalizált engedélyezési lista (pl. "c:\" és "C:" összehasonlításhoz)
        monitored = [m.strip().rstrip("\\/").lower() for m in Config.MONITORED_DISKS]

        for p in partitions:
            # 1. Virtuális fájlrendszerek és belső snapshotok szűrése
            if p.fstype.lower() in self.IGNORED_FS_TYPES:
                continue

            if "/System/Volumes/Update" in p.mountpoint or "/System/Volumes/VM" in p.mountpoint:
                continue

            # 2. Boot partíciók kihagyása (kivéve ha a felhasználó a .env-ben kifejezetten kérte)
            normalized_mount = p.mountpoint.strip().rstrip("\\/").lower()
            normalized_device = p.device.strip().rstrip("\\/").lower()

            if not monitored:
                if p.mountpoint in self.IGNORED_MOUNTS or p.mountpoint.startswith("/boot/"):
                    continue

            # 3. .env szűrés alkalmazása (ha van beállítva lista a MONITORED_DISKS-ben)
            if monitored:
                if normalized_mount not in monitored and normalized_device not in monitored:
                    continue

            # Duplikációk kiszűrése
            if p.mountpoint in seen_mounts:
                continue

            try:
                usage = psutil.disk_usage(p.mountpoint)
                if usage.total == 0:
                    continue

                seen_mounts.add(p.mountpoint)
                disks.append({
                    "device": p.device,
                    "mount": p.mountpoint,
                    "fstype": p.fstype,
                    "percent": usage.percent,
                    "used_gb": usage.used / (1024**3),
                    "total_gb": usage.total / (1024**3),
                })
            except (PermissionError, FileNotFoundError):
                continue

        # Fallback gyökérkönyvtár, ha a szűrés után véletlenül semmi nem maradt volna
        if not disks and not monitored:
            try:
                usage = psutil.disk_usage("/")
                disks.append({
                    "device": "root",
                    "mount": "/",
                    "fstype": "unknown",
                    "percent": usage.percent,
                    "used_gb": usage.used / (1024**3),
                    "total_gb": usage.total / (1024**3),
                })
            except Exception:
                pass

        return disks

    def get_system_metrics(self) -> Dict[str, Any]:
        """Lekéri a CPU, RAM, lemezek és hálózati sebesség adatait."""
        now = time.time()
        elapsed = max(now - self._last_net_time, 0.001)

        cpu_percent = psutil.cpu_percent(interval=None)
        virtual_mem = psutil.virtual_memory()
        disks = self._get_disks_metrics()

        # Hálózati sebesség számítása (Megabit/s)
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
            "disks": disks,
            "net_upload_mbps": (bytes_sent_sec * 8) / (1024 * 1024),
            "net_download_mbps": (bytes_recv_sec * 8) / (1024 * 1024),
        }

    def get_docker_metrics(self) -> List[Dict[str, str]]:
        """Lekéri a konténerek státuszát és a beépített Healthcheck állapotukat."""
        if not self.enable_docker or not self.docker_client:
            return []

        containers_data = []
        try:
            containers = self.docker_client.containers.list(all=True)
            for c in containers:
                raw_status = c.status.lower()

                # Healthcheck státusz kiolvasása a konténer attribútumaiból
                health_info = c.attrs.get("State", {}).get("Health", {})
                health_status = health_info.get("Status", "").lower()

                image_name = c.image.tags[0] if c.image.tags else "unknown"

                containers_data.append({
                    "name": c.name,
                    "status": raw_status,
                    "health": health_status if health_status else "-",
                    "image": image_name
                })
        except Exception:
            pass

        return containers_data