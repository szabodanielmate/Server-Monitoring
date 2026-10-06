import time
import sys
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text

from src.config import Config
from src.metrics import MetricsCollector
from src.logger import setup_logger
from src.notifier import AlertNotifier

logger = setup_logger()
collector = MetricsCollector(enable_docker=Config.ENABLE_DOCKER)
notifier = AlertNotifier()


def generate_layout(metrics: dict, containers: list) -> Layout:
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main"),
        Layout(name="footer", size=3)
    )

    # 1. Fejléc
    header_text = Text(
        f"🖥️  SZERVER MONITORING  |  Frissítés: {Config.CHECK_INTERVAL} mp  |  Idő: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        style="bold cyan",
        justify="center"
    )
    layout["header"].update(Panel(header_text, style="cyan"))

    # 2. Hardver metrikák táblázat
    sys_table = Table(title="Rendszer Erőforrások", expand=True)
    sys_table.add_column("Komponens", style="bold white")
    sys_table.add_column("Érték / Használat", justify="right")
    sys_table.add_column("Státusz", justify="center")

    def status_badge(val: float, thresh: float):
        if val >= thresh:
            return Text("KRITIKUS", style="bold red")
        elif val >= thresh * 0.8:
            return Text("FIGYELEM", style="bold yellow")
        return Text("OK", style="bold green")

    # CPU sor
    sys_table.add_row(
        "CPU",
        f"{metrics['cpu_percent']:.1f}%",
        status_badge(metrics['cpu_percent'], Config.CPU_THRESHOLD)
    )

    # RAM sor
    sys_table.add_row(
        "RAM",
        f"{metrics['ram_percent']:.1f}% ({metrics['ram_used_gb']:.2f} / {metrics['ram_total_gb']:.2f} GB)",
        status_badge(metrics['ram_percent'], Config.RAM_THRESHOLD)
    )

    # Lemez sor
    sys_table.add_row(
        "Lemez (/)",
        f"{metrics['disk_percent']:.1f}% ({metrics['disk_used_gb']:.1f} / {metrics['disk_total_gb']:.1f} GB)",
        status_badge(metrics['disk_percent'], Config.DISK_THRESHOLD)
    )

    # Hálózat sor
    sys_table.add_row(
        "Hálózat (Fel / Le)",
        f"⬆ {metrics['net_upload_kbps']:.1f} KB/s  |  ⬇ {metrics['net_download_kbps']:.1f} KB/s",
        Text("AKTÍV", style="blue")
    )

    # Ha a Docker be van kapcsolva és vannak adatok
    if Config.ENABLE_DOCKER:
        layout["main"].split_row(
            Layout(name="system_metrics", ratio=1),
            Layout(name="docker_metrics", ratio=1)
        )
        layout["system_metrics"].update(Panel(sys_table, border_style="blue"))

        doc_table = Table(title="Docker Konténerek", expand=True)
        doc_table.add_column("Konténer", style="bold white")
        doc_table.add_column("Állapot", justify="center")
        doc_table.add_column("Image", style="dim")

        if containers:
            for c in containers:
                color = "green" if c["status"] == "running" else "red"
                doc_table.add_row(c["name"], Text(c["status"], style=color), c["image"])
        else:
            doc_table.add_row("-", Text("Nincs futó konténer / nem elérhető", style="dim"), "-")

        layout["docker_metrics"].update(Panel(doc_table, border_style="magenta"))
    else:
        layout["main"].update(Panel(sys_table, border_style="blue"))

    # 3. Lábléc
    footer_text = Text(
        f"Logfájl: {Config.LOG_FILE_PATH.name}  |  Kilépéshez: Ctrl + C",
        style="dim white",
        justify="center"
    )
    layout["footer"].update(Panel(footer_text, style="dim"))

    return layout


def check_and_alert(metrics: dict):
    """Ellenőrzi a határértékeket és triggereli a notifiert."""
    if metrics["cpu_percent"] >= Config.CPU_THRESHOLD:
        notifier.send_alert("CPU", metrics["cpu_percent"], Config.CPU_THRESHOLD)

    if metrics["ram_percent"] >= Config.RAM_THRESHOLD:
        notifier.send_alert("RAM", metrics["ram_percent"], Config.RAM_THRESHOLD)

    if metrics["disk_percent"] >= Config.DISK_THRESHOLD:
        notifier.send_alert("Lemez", metrics["disk_percent"], Config.DISK_THRESHOLD)


def main():
    logger.info("Szerver monitoring elindítva.")
    try:
        with Live(refresh_per_second=2, screen=True) as live:
            while True:
                # 1. Metrikák begyűjtése
                metrics = collector.get_system_metrics()
                containers = collector.get_docker_metrics() if Config.ENABLE_DOCKER else []

                # 2. Határérték-ellenőrzés & riasztások
                check_and_alert(metrics)

                # 3. Kijelző frissítése
                live.update(generate_layout(metrics, containers))

                # 4. Várakozás a következő ciklusig
                time.sleep(Config.CHECK_INTERVAL)

    except KeyboardInterrupt:
        logger.info("Szerver monitoring leállítva (Ctrl + C).")
        print("\n\nMonitoring leállítva. Szép napot!\n")
        sys.exit(0)


if __name__ == "__main__":
    main()