import sys
import psutil
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

console = Console()


def get_available_partitions():
    """Fizikai lemezek és csatolási pontok felderítése."""
    ignored_fs = {"squashfs", "tmpfs", "devtmpfs", "overlay", "iso9660", "nullfs", "autofs"}
    # Kizárandó rendszer- és boot csatolási pontok:
    ignored_mounts = {"/boot", "/boot/efi"}
    
    partitions = []
    seen = set()

    for p in psutil.disk_partitions(all=False):
        if p.fstype.lower() in ignored_fs or p.mountpoint in seen:
            continue
        
        # Boot partíciók átugrása
        if p.mountpoint in ignored_mounts or p.mountpoint.startswith("/boot/"):
            continue

        try:
            usage = psutil.disk_usage(p.mountpoint)
            if usage.total > 0:
                partitions.append((p.mountpoint, usage.total / (1024**3)))
                seen.add(p.mountpoint)
        except Exception:
            continue
    return partitions


def run_configuration():
    console.print(Panel.fit(
        "[bold cyan]Szerver Monitoring - Interaktív Telepítő & Konfiguráció[/bold cyan]\n"
        "[dim]Nyomj Enter-t az alapértelmezett [érték] elfogadásához.[/dim]",
        border_style="cyan"
    ))

    # 1. Küszöbértékek
    console.print("\n[bold yellow]1. Határértékek (Thresholds)[/bold yellow]")
    cpu_th = Prompt.ask("CPU riasztási küszöb (%)", default="85.0")
    ram_th = Prompt.ask("RAM riasztási küszöb (%)", default="90.0")

    # 2. Partíciók kiválasztása
    console.print("\n[bold yellow]2. Merevlemezek és Partíciók[/bold yellow]")
    disk_th = Prompt.ask("Lemez riasztási küszöb (%)", default="90.0")

    parts = get_available_partitions()
    console.print("\nTalált partíciók:")
    for idx, (mount, size) in enumerate(parts, 1):
        console.print(f"  [cyan]{idx}.[/cyan] {mount} [dim]({size:.1f} GB)[/dim]")

    console.print("\n[dim]Írd be a figyelni kívánt számokat vesszővel elválasztva (pl. 1, 2) vagy 'all':[/dim]")
    selection = Prompt.ask("Partíciók kiválasztása", default="all")

    selected_mounts = []
    if selection.strip().lower() == "all":
        selected_mounts = [m[0] for m in parts]
    else:
        try:
            indices = [int(i.strip()) for i in selection.split(",") if i.strip()]
            for idx in indices:
                if 1 <= idx <= len(parts):
                    selected_mounts.append(parts[idx - 1][0])
        except ValueError:
            console.print("[red]Érvénytelen bevitel, minden partíció monitorozva lesz.[/red]")
            selected_mounts = [m[0] for m in parts]

    monitored_disks_str = ",".join(selected_mounts)

    # 3. Docker integráció
    console.print("\n[bold yellow]3. Docker integráció[/bold yellow]")
    enable_docker = Confirm.ask("Szeretnéd monitorozni a Docker konténereket?", default=True)

    # 4. Értesítési csatornák
    console.print("\n[bold yellow]4. Értesítési csatornák (Opcionális)[/bold yellow]")
    
    # Discord
    use_discord = Confirm.ask("Szeretnél Discord értesítéseket?", default=False)
    discord_url = ""
    if use_discord:
        discord_url = Prompt.ask("Discord Webhook URL", default="")

    # Telegram (Külön, garantált bekérés)
    use_telegram = Confirm.ask("Szeretnél Telegram értesítéseket?", default=False)
    telegram_token = ""
    telegram_chat_id = ""
    if use_telegram:
        telegram_token = Prompt.ask("Telegram Bot Token", default="")
        telegram_chat_id = Prompt.ask("Telegram Chat ID", default="")

    # 5. .env mentése
    env_content = f"""# Automatikusan generált konfiguráció
                    CPU_THRESHOLD={cpu_th}
                    RAM_THRESHOLD={ram_th}
                    DISK_THRESHOLD={disk_th}

                    CHECK_INTERVAL=3
                    ALERT_DURATION=30
                    ALERT_COOLDOWN=300

                    # Csak ezek a partíciók lesznek figyelve
                    MONITORED_DISKS={monitored_disks_str}

                    ENABLE_DOCKER={'true' if enable_docker else 'false'}

                    DISCORD_WEBHOOK_URL={discord_url.strip()}
                    TELEGRAM_BOT_TOKEN={telegram_token.strip()}
                    TELEGRAM_CHAT_ID={telegram_chat_id.strip()}
                    """

    with open(".env", "w", encoding="utf-8") as f:
        f.write(env_content)

    console.print("\n[bold green]✔ A beállítások sikeresen mentve a .env fájlba![/bold green]\n")


if __name__ == "__main__":
    try:
        run_configuration()
    except KeyboardInterrupt:
        console.print("\n[dim]Konfiguráció megszakítva.[/dim]")
        sys.exit(0)