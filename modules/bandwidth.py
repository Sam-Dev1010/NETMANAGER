import psutil
import time
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text

from modules.utils import format_bytes

console = Console()


class BandwidthMonitor:
    def __init__(self):
        self.running = False
        self.interval = 1
        self._prev = None

    def _current_counters(self):
        c = psutil.net_io_counters()
        return c.bytes_sent, c.bytes_recv, c.packets_sent, c.packets_recv

    def _delta(self):
        curr = self._current_counters()
        if self._prev is None:
            self._prev = curr
            time.sleep(self.interval)
            curr = self._current_counters()
        ds = (curr[0] - self._prev[0]) / self.interval
        dr = (curr[1] - self._prev[1]) / self.interval
        self._prev = curr
        return ds, dr

    def _bar(self, value, max_value, width=30, color="green"):
        if max_value == 0:
            filled = 0
        else:
            filled = int((value / max_value) * width)
        filled = min(filled, width)
        bar = "█" * filled + "░" * (width - filled)
        return f"[{color}]{bar}[/{color}]"

    def _build_live_table(self, up_speed, down_speed, total_sent, total_recv):
        max_speed = max(up_speed, down_speed, 1)
        table = Table(title="📊 Monitor de Ancho de Banda (en vivo)", show_header=True, header_style="bold cyan", expand=True)
        table.add_column("Métrica", style="bold", ratio=2)
        table.add_column("Valor", justify="right", ratio=1)
        table.add_column("Gráfico", ratio=3)

        table.add_row(
            "Velocidad de Subida ↑",
            f"[green]{format_bytes(up_speed)}/s[/green]",
            self._bar(up_speed, max_speed, color="green")
        )
        table.add_row(
            "Velocidad de Bajada ↓",
            f"[blue]{format_bytes(down_speed)}/s[/blue]",
            self._bar(down_speed, max_speed, color="blue")
        )
        table.add_row("Total Enviado", f"[yellow]{format_bytes(total_sent)}[/yellow]", "")
        table.add_row("Total Recibido", f"[yellow]{format_bytes(total_recv)}[/yellow]", "")
        table.add_row("Conexiones Activas", str(len(psutil.net_connections())), "")
        return table

    def live_monitor(self):
        self.running = True
        self._prev = None
        console.print("[bold yellow]Iniciando monitor en vivo... Presiona Ctrl+C para detener.[/bold yellow]")
        time.sleep(0.5)

        try:
            with Live(console=console, refresh_per_second=1) as live:
                while self.running:
                    up, down = self._delta()
                    c = psutil.net_io_counters()
                    table = self._build_live_table(up, down, c.bytes_sent, c.bytes_recv)
                    live.update(table)
                    time.sleep(self.interval)
        except KeyboardInterrupt:
            self.running = False
            console.print("\n[bold red]Monitor detenido.[/bold red]")

    def snapshot(self):
        c = psutil.net_io_counters()
        conns = psutil.net_connections()
        table = Table(title="Instantánea de Red", show_header=True, header_style="bold cyan")
        table.add_column("Métrica", style="bold")
        table.add_column("Valor", justify="right")
        table.add_row("Total Enviado", f"[yellow]{format_bytes(c.bytes_sent)}[/yellow]")
        table.add_row("Total Recibido", f"[yellow]{format_bytes(c.bytes_recv)}[/yellow]")
        table.add_row("Paquetes Out", str(c.packets_sent))
        table.add_row("Paquetes In", str(c.packets_recv))
        table.add_row("Errores", f"{c.errin} in / {c.errout} out")
        table.add_row("Descartados", f"{c.dropin} in / {c.dropout} out")
        table.add_row("Conexiones Activas", str(len(conns)))
        console.print(table)

    def per_interface(self):
        counters = psutil.net_io_counters(pernic=True)
        table = Table(title="Tráfico por Interfaz", show_header=True, header_style="bold cyan")
        table.add_column("Interfaz", style="bold")
        table.add_column("Enviado", justify="right")
        table.add_column("Recibido", justify="right")
        table.add_column("Paquetes Out", justify="right")
        table.add_column("Paquetes In", justify="right")
        table.add_column("Errores", justify="right")

        for name, stats in counters.items():
            errors = stats.errin + stats.errout
            table.add_row(
                name,
                format_bytes(stats.bytes_sent),
                format_bytes(stats.bytes_recv),
                str(stats.packets_sent),
                str(stats.packets_recv),
                str(errors) if errors > 0 else "[dim]0[/dim]",
            )

        console.print(table)

    def protocol_stats(self):
        c = psutil.net_io_counters()
        console.print(Panel(
            f"[bold]Enviado:[/bold] {format_bytes(c.bytes_sent)} ({c.packets_sent} paquetes)\n"
            f"[bold]Recibido:[/bold] {format_bytes(c.bytes_recv)} ({c.packets_recv} paquetes)\n"
            f"[bold]Errores:[/bold] {c.errin} entrantes, {c.errout} salientes\n"
            f"[bold]Descartados:[/bold] {c.dropin} entrantes, {c.dropout} salientes",
            title="Estadísticas de Protocolo",
            border_style="green"
        ))
