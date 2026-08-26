import psutil
import platform
import subprocess
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from modules.utils import format_bytes, is_windows

console = Console()


class NetworkInfo:
    def __init__(self):
        pass

    def interfaces(self):
        stats = psutil.net_if_stats()
        addrs = psutil.net_if_addrs()
        table = Table(title="Interfaces de Red", show_header=True, header_style="bold cyan")
        table.add_column("Interfaz", style="bold")
        table.add_column("Estado")
        table.add_column("Velocidad")
        table.add_column("MTU", justify="right")
        table.add_column("Direcciones")

        for name, stat in stats.items():
            status = "[green]UP[/green]" if stat.isup else "[red]DOWN[/red]"
            speed = f"{stat.speed} Mbps" if stat.speed > 0 else "N/A"
            addr_list = addrs.get(name, [])
            addr_str = "\n".join(
                f"[dim]{a.family.name}:[/dim] {a.address}" for a in addr_list
            )
            table.add_row(name, status, speed, str(stat.mtu), addr_str)

        console.print(table)

    def interfaces_simple(self):
        addrs = psutil.net_if_addrs()
        table = Table(title="Interfaces de Red", show_header=True, header_style="bold cyan")
        table.add_column("Interfaz", style="bold")
        table.add_column("Direcciones")

        for name, addr_list in addrs.items():
            addr_str = ", ".join(
                a.address for a in addr_list
                if a.family.name in ('AF_INET', 'AF_INET6')
            )
            if addr_str:
                table.add_row(name, addr_str)

        console.print(table)

    def gateway_info(self):
        if is_windows():
            self._gateway_windows()
        else:
            self._gateway_linux()

    def _gateway_linux(self):
        try:
            result = subprocess.run(
                ['ip', 'route', 'show', 'default'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                console.print(Panel(
                    result.stdout.strip(),
                    title="Puerta de Enlace", border_style="cyan"
                ))
            else:
                console.print("[yellow]No se encontraron puertas de enlace.[/yellow]")
        except FileNotFoundError:
            console.print("[red]Comando 'ip' no encontrado.[/red]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

    def _gateway_windows(self):
        try:
            result = subprocess.run(['ipconfig'], capture_output=True, text=True, timeout=5)
            gateways = [
                line.strip() for line in result.stdout.split('\n')
                if 'Default Gateway' in line or 'Puerta de enlace predeterminada' in line
            ]
            if gateways:
                console.print(Panel(
                    "\n".join(gateways),
                    title="Puertas de Enlace", border_style="cyan"
                ))
            else:
                console.print("[yellow]No se encontraron puertas de enlace.[/yellow]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

    def dns_info(self):
        if is_windows():
            self._dns_windows()
        else:
            self._dns_linux()

    def _dns_linux(self):
        dns_servers = []
        try:
            with open('/etc/resolv.conf', 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('nameserver'):
                        parts = line.split()
                        if len(parts) >= 2:
                            dns_servers.append(parts[1])
        except FileNotFoundError:
            pass

        if dns_servers:
            console.print(Panel(
                "\n".join(f"  - {s}" for s in dns_servers),
                title=f"Servidores DNS ({len(dns_servers)})", border_style="cyan"
            ))
        else:
            console.print("[yellow]No se encontraron servidores DNS.[/yellow]")

    def _dns_windows(self):
        try:
            result = subprocess.run(['ipconfig', '/all'], capture_output=True, text=True, timeout=5)
            dns_lines = [
                line.strip() for line in result.stdout.split('\n')
                if 'DNS' in line.upper() and ':' in line
            ]
            if dns_lines:
                console.print(Panel(
                    "\n".join(dns_lines[:10]),
                    title="Servidores DNS", border_style="cyan"
                ))
            else:
                console.print("[yellow]No se encontraron servidores DNS.[/yellow]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

    def system_info(self):
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        cpu_freq = psutil.cpu_freq()

        info_lines = [
            f"[bold]Sistema:[/bold] {platform.system()} {platform.release()}",
            f"[bold]Nodo:[/bold] {platform.node()}",
            f"[bold]Python:[/bold] {platform.python_version()}",
            f"[bold]CPU:[/bold] {platform.processor() or 'N/A'}",
            f"[bold]RAM:[/bold] {format_bytes(mem.total)} ({mem.percent}% uso)",
            f"[bold]Disco:[/bold] {format_bytes(disk.used)} / {format_bytes(disk.total)} ({disk.percent}%)",
        ]
        if cpu_freq:
            info_lines.append(f"[bold]CPU Freq:[/bold] {cpu_freq.current:.0f} MHz")

        console.print(Panel(
            "\n".join(info_lines),
            title="Información del Sistema", border_style="magenta"
        ))
