import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.prompt import Prompt, IntPrompt

from modules.bandwidth import BandwidthMonitor
from modules.connections import ConnectionTracker
from modules.analyzer import TrafficAnalyzer
from modules.firewall import FirewallManager
from modules.netinfo import NetworkInfo
from modules.utils import is_root, is_windows

console = Console()

BANNER = """
 ██╗   ██╗███╗   ██╗██████╗ ███████╗██╗  ██╗███╗   ██╗███████╗████████╗
 ██║   ██║████╗  ██║██╔══██╗██╔════╝██║  ██║████╗  ██║██╔════╝╚══██╔══╝
 ██║   ██║██╔██╗ ██║██║  ██║███████╗███████║██╔██╗ ██║█████╗     ██║   
 ██║   ██║██║╚██╗██║██║  ██║╚════██║██╔══██║██║╚██╗██║██╔══╝     ██║   
 ╚██████╔╝██║ ╚████║██████╔╝███████║██║  ██║██║ ╚████║███████╗   ██║   
  ╚═════╝ ╚═╝  ╚═══╝╚═════╝ ╚══════╝╚═╝  ╚═╝╚═╝  ╚═══╝╚══════╝   ╚═╝   
"""


class NetworkTrafficApp:
    def __init__(self):
        self.bandwidth = BandwidthMonitor()
        self.connections = ConnectionTracker()
        self.analyzer = TrafficAnalyzer()
        self.firewall = FirewallManager()
        self.netinfo = NetworkInfo()

    def show_banner(self):
        console.clear()
        console.print(Text(BANNER, style="bold cyan"))
        console.print(Panel(
            "[bold white]Gestor de Tráfico de Red[/bold white]\n"
            "[dim]Monitoreo, análisis y control de red[/dim]",
            border_style="cyan"
        ))

    def main_menu(self):
        self.show_banner()
        while True:
            table = Table(show_header=False, border_style="cyan")
            table.add_column("Opción", style="bold", width=4)
            table.add_column("Descripción")

            table.add_row("1", "📊 Monitoreo de Ancho de Banda")
            table.add_row("2", "🔌 Conexiones Activas")
            table.add_row("3", "📈 Análisis de Tráfico")
            table.add_row("4", "🛡️  Firewall / Filtrado")
            table.add_row("5", "ℹ️  Información de Red")
            table.add_row("0", "🚪 Salir")

            console.print(table)
            choice = Prompt.ask("\n[bold cyan]Selecciona una opción[/bold cyan]")

            if choice == '1':
                self.bandwidth_menu()
            elif choice == '2':
                self.connections_menu()
            elif choice == '3':
                self.analyzer_menu()
            elif choice == '4':
                self.firewall_menu()
            elif choice == '5':
                self.netinfo_menu()
            elif choice == '0':
                console.print("[bold green]¡Hasta luego![/bold green]")
                break
            else:
                console.print("[red]Opción no válida.[/red]")

    def bandwidth_menu(self):
        while True:
            console.print("\n[bold cyan]── Monitoreo de Ancho de Banda ──[/bold cyan]")
            table = Table(show_header=False, border_style="cyan")
            table.add_column("Opción", style="bold", width=4)
            table.add_column("Descripción")
            table.add_row("1", "Monitor en vivo")
            table.add_row("2", "Instantánea actual")
            table.add_row("3", "Tráfico por interfaz")
            table.add_row("4", "Estadísticas de protocolo")
            table.add_row("0", "Volver")

            console.print(table)
            choice = Prompt.ask("\n[bold cyan]Opción[/bold cyan]")

            if choice == '1':
                self.bandwidth.live_monitor()
            elif choice == '2':
                self.bandwidth.snapshot()
            elif choice == '3':
                self.bandwidth.per_interface()
            elif choice == '4':
                self.bandwidth.protocol_stats()
            elif choice == '0':
                break

    def connections_menu(self):
        while True:
            console.print("\n[bold cyan]── Conexiones Activas ──[/bold cyan]")
            table = Table(show_header=False, border_style="cyan")
            table.add_column("Opción", style="bold", width=4)
            table.add_column("Descripción")
            table.add_row("1", "Listar todas las conexiones")
            table.add_row("2", "Conexiones por estado")
            table.add_row("3", "Conexiones por proceso")
            table.add_row("4", "Top hosts remotos")
            table.add_row("5", "Buscar proceso por puerto")
            table.add_row("0", "Volver")

            console.print(table)
            choice = Prompt.ask("\n[bold cyan]Opción[/bold cyan]")

            if choice == '1':
                self.connections.list_connections(show_all=True)
            elif choice == '2':
                self.connections.connections_by_state()
            elif choice == '3':
                self.connections.connections_by_process()
            elif choice == '4':
                limit = IntPrompt.ask("¿Cuántos hosts mostrar?", default=15)
                self.connections.top_remote_hosts(limit)
            elif choice == '5':
                port = IntPrompt.ask("Número de puerto")
                pid, name, status = self.connections.find_pid_by_port(port)
                if pid:
                    console.print(f"[green]PID: {pid}, Proceso: {name}, Estado: {status}[/green]")
                else:
                    console.print(f"[yellow]No se encontró proceso usando el puerto {port}[/yellow]")
            elif choice == '0':
                break

    def analyzer_menu(self):
        while True:
            console.print("\n[bold cyan]── Análisis de Tráfico ──[/bold cyan]")
            table = Table(show_header=False, border_style="cyan")
            table.add_column("Opción", style="bold", width=4)
            table.add_column("Descripción")
            table.add_row("1", "Análisis en vivo (temporizado)")
            table.add_row("2", "Reporte actual")
            table.add_row("3", "Comparar muestras")
            table.add_row("4", "Guardar log")
            table.add_row("5", "Cargar log")
            table.add_row("0", "Volver")

            console.print(table)
            choice = Prompt.ask("\n[bold cyan]Opción[/bold cyan]")

            if choice == '1':
                duration = IntPrompt.ask("Duración en segundos", default=30)
                self.analyzer.live_analysis(duration)
            elif choice == '2':
                self.analyzer.generate_report()
            elif choice == '3':
                self.analyzer.compare_snapshots()
            elif choice == '4':
                fname = Prompt.ask("Nombre del archivo", default="traffic_log.json")
                self.analyzer.save_log(fname)
            elif choice == '5':
                fname = Prompt.ask("Nombre del archivo", default="traffic_log.json")
                self.analyzer.load_log(fname)
            elif choice == '0':
                break

    def firewall_menu(self):
        while True:
            console.print("\n[bold cyan]── Firewall / Filtrado ──[/bold cyan]")
            table = Table(show_header=False, border_style="cyan")
            table.add_column("Opción", style="bold", width=4)
            table.add_column("Descripción")
            table.add_row("1", "Listar reglas")
            table.add_row("2", "Bloquear IP")
            table.add_row("3", "Desbloquear IP")
            table.add_row("4", "Bloquear puerto")
            table.add_row("5", "Desbloquear puerto")
            table.add_row("6", "Whitelist - Permitir IP")
            table.add_row("7", "Remover de whitelist")
            table.add_row("8", "Ver bloqueados")
            table.add_row("9", "Ver permitidos")
            table.add_row("10", "Exportar reglas")
            table.add_row("11", "Limpiar todas las reglas")
            table.add_row("0", "Volver")

            console.print(table)
            choice = Prompt.ask("\n[bold cyan]Opción[/bold cyan]")

            if choice == '1':
                self.firewall.list_rules()
            elif choice == '2':
                ip = Prompt.ask("IP a bloquear")
                reason = Prompt.ask("Razón", default="manual")
                self.firewall.block_ip(ip, reason)
            elif choice == '3':
                ip = Prompt.ask("IP a desbloquear")
                self.firewall.unblock_ip(ip)
            elif choice == '4':
                port = IntPrompt.ask("Puerto a bloquear")
                reason = Prompt.ask("Razón", default="manual")
                self.firewall.block_port(port, reason)
            elif choice == '5':
                port = IntPrompt.ask("Puerto a desbloquear")
                self.firewall.unblock_port(port)
            elif choice == '6':
                ip = Prompt.ask("IP a permitir")
                self.firewall.allow_ip(ip)
            elif choice == '7':
                ip = Prompt.ask("IP a remover de whitelist")
                self.firewall.remove_allowed_ip(ip)
            elif choice == '8':
                self.firewall.list_blocked()
            elif choice == '9':
                self.firewall.list_allowed()
            elif choice == '10':
                fname = Prompt.ask("Nombre del archivo", default="firewall_export.json")
                self.firewall.export_rules(fname)
            elif choice == '11':
                confirm = Prompt.ask("[bold red]¿Eliminar TODAS las reglas? (s/n)[/bold red]")
                if confirm.lower() == 's':
                    self.firewall.clear_all_rules()
            elif choice == '0':
                break

    def netinfo_menu(self):
        while True:
            console.print("\n[bold cyan]── Información de Red ──[/bold cyan]")
            table = Table(show_header=False, border_style="cyan")
            table.add_column("Opción", style="bold", width=4)
            table.add_column("Descripción")
            table.add_row("1", "Interfaces de red (detallado)")
            table.add_row("2", "Interfaces de red (simple)")
            table.add_row("3", "Gateway / Puerta de enlace")
            table.add_row("4", "Servidores DNS")
            table.add_row("5", "Info del sistema")
            table.add_row("0", "Volver")

            console.print(table)
            choice = Prompt.ask("\n[bold cyan]Opción[/bold cyan]")

            if choice == '1':
                self.netinfo.interfaces()
            elif choice == '2':
                self.netinfo.interfaces_simple()
            elif choice == '3':
                self.netinfo.gateway_info()
            elif choice == '4':
                self.netinfo.dns_info()
            elif choice == '5':
                self.netinfo.system_info()
            elif choice == '0':
                break


if __name__ == "__main__":
    if not is_root():
        console.print("[bold yellow]⚠ Algunas funciones requieren permisos de root/sudo.[/bold yellow]")
        console.print("[dim]Ejecuta con sudo para acceso completo.[/dim]\n")

    app = NetworkTrafficApp()
    try:
        app.main_menu()
    except KeyboardInterrupt:
        console.print("\n[bold green]¡Hasta luego![/bold green]")
