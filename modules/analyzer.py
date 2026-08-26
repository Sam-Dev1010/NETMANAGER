import psutil
import time
import json
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live

from modules.utils import format_bytes

console = Console()


class TrafficAnalyzer:
    def __init__(self):
        self.snapshots = []
        self.running = False

    def take_snapshot(self):
        counters = psutil.net_io_counters()
        conns = psutil.net_connections()
        timestamp = datetime.now().isoformat()

        snapshot = {
            'timestamp': timestamp,
            'bytes_sent': counters.bytes_sent,
            'bytes_recv': counters.bytes_recv,
            'packets_sent': counters.packets_sent,
            'packets_recv': counters.packets_recv,
            'errin': counters.errin,
            'errout': counters.errout,
            'dropin': counters.dropin,
            'dropout': counters.dropout,
            'active_connections': len(conns),
        }
        self.snapshots.append(snapshot)
        return snapshot

    def get_rate(self):
        if len(self.snapshots) < 2:
            return None
        prev = self.snapshots[-2]
        curr = self.snapshots[-1]
        t1 = datetime.fromisoformat(prev['timestamp'])
        t2 = datetime.fromisoformat(curr['timestamp'])
        dt = (t2 - t1).total_seconds()
        if dt == 0:
            return None
        return {
            'send_rate': (curr['bytes_sent'] - prev['bytes_sent']) / dt,
            'recv_rate': (curr['bytes_recv'] - prev['bytes_recv']) / dt,
            'packet_rate_out': (curr['packets_sent'] - prev['packets_sent']) / dt,
            'packet_rate_in': (curr['packets_recv'] - prev['packets_recv']) / dt,
        }

    def _build_analysis_table(self, rate, elapsed, remaining):
        table = Table(title="Análisis de Tráfico en Vivo", show_header=True, header_style="bold cyan")
        table.add_column("Métrica", style="bold")
        table.add_column("Valor", justify="right")
        table.add_row("Tasa de Envío", f"[green]{format_bytes(rate['send_rate'])}/s[/green]")
        table.add_row("Tasa de Recepción", f"[blue]{format_bytes(rate['recv_rate'])}/s[/blue]")
        table.add_row("Paquetes/s Out", f"{rate['packet_rate_out']:.1f}")
        table.add_row("Paquetes/s In", f"{rate['packet_rate_in']:.1f}")
        table.add_row("Muestras", str(len(self.snapshots)))
        if remaining is not None:
            table.add_row("Tiempo restante", f"{max(0, int(remaining))}s")
        return table

    def live_analysis(self, duration=30):
        self.running = True
        self.snapshots.clear()
        self.take_snapshot()
        console.print(f"[bold yellow]Analizando tráfico por {duration} segundos...[/bold yellow]")
        start = time.time()

        try:
            with Live(console=console, refresh_per_second=1) as live:
                while self.running and (time.time() - start) < duration:
                    time.sleep(2)
                    self.take_snapshot()
                    rate = self.get_rate()
                    if rate:
                        elapsed = time.time() - start
                        remaining = duration - elapsed
                        table = self._build_analysis_table(rate, elapsed, remaining)
                        live.update(table)
        except KeyboardInterrupt:
            self.running = False

        console.print("\n[bold green]Análisis completado.[/bold green]")

    def generate_report(self):
        if not self.snapshots:
            self.take_snapshot()

        table = Table(title="Reporte de Tráfico", show_header=True, header_style="bold cyan")
        table.add_column("Métrica", style="bold")
        table.add_column("Valor", justify="right")

        curr = self.snapshots[-1]
        table.add_row("Total Enviado", format_bytes(curr['bytes_sent']))
        table.add_row("Total Recibido", format_bytes(curr['bytes_recv']))
        table.add_row("Total Paquetes Out", str(curr['packets_sent']))
        table.add_row("Total Paquetes In", str(curr['packets_recv']))
        table.add_row("Errores Entrada", str(curr['errin']))
        table.add_row("Errores Salida", str(curr['errout']))
        table.add_row("Descartados Entrada", str(curr['dropin']))
        table.add_row("Descartados Salida", str(curr['dropout']))
        table.add_row("Conexiones Activas", str(curr['active_connections']))

        if len(self.snapshots) >= 2:
            rate = self.get_rate()
            if rate:
                table.add_section()
                table.add_row("Tasa Envío Actual", f"{format_bytes(rate['send_rate'])}/s")
                table.add_row("Tasa Recepción Actual", f"{format_bytes(rate['recv_rate'])}/s")

        console.print(table)

        if len(self.snapshots) >= 2:
            first = self.snapshots[0]
            last = self.snapshots[-1]
            t1 = datetime.fromisoformat(first['timestamp'])
            t2 = datetime.fromisoformat(last['timestamp'])
            elapsed = (t2 - t1).total_seconds()
            if elapsed > 0:
                avg_up = (last['bytes_sent'] - first['bytes_sent']) / elapsed
                avg_down = (last['bytes_recv'] - first['bytes_recv']) / elapsed
                console.print(Panel(
                    f"[bold]Promedio Envío:[/bold] {format_bytes(avg_up)}/s\n"
                    f"[bold]Promedio Recepción:[/bold] {format_bytes(avg_down)}/s\n"
                    f"[bold]Duración:[/bold] {elapsed:.1f}s",
                    title="Resumen",
                    border_style="green"
                ))

    def save_log(self, filename="traffic_log.json"):
        with open(filename, 'w') as f:
            json.dump(self.snapshots, f, indent=2, default=str)
        console.print(f"[green]Log guardado en {filename} ({len(self.snapshots)} muestras)[/green]")

    def load_log(self, filename="traffic_log.json"):
        try:
            with open(filename, 'r') as f:
                self.snapshots = json.load(f)
            console.print(f"[green]Log cargado: {len(self.snapshots)} muestras desde {filename}[/green]")
        except FileNotFoundError:
            console.print(f"[red]Archivo no encontrado: {filename}[/red]")

    def compare_snapshots(self):
        if len(self.snapshots) < 2:
            console.print("[yellow]Se necesitan al menos 2 muestras para comparar.[/yellow]")
            return

        first = self.snapshots[0]
        last = self.snapshots[-1]
        t1 = datetime.fromisoformat(first['timestamp'])
        t2 = datetime.fromisoformat(last['timestamp'])
        elapsed = (t2 - t1).total_seconds()

        table = Table(title="Comparación de Muestras", show_header=True, header_style="bold cyan")
        table.add_column("Métrica", style="bold")
        table.add_column("Primera", justify="right")
        table.add_column("Última", justify="right")
        table.add_column("Cambio", justify="right")

        def diff_str(a, b, fmt=True):
            d = b - a
            if fmt:
                sign = "+" if d >= 0 else ""
                return f"{sign}{format_bytes(abs(d))}"
            return str(d)

        table.add_row("Bytes Enviados",
                       format_bytes(first['bytes_sent']),
                       format_bytes(last['bytes_sent']),
                       diff_str(first['bytes_sent'], last['bytes_sent']))
        table.add_row("Bytes Recibidos",
                       format_bytes(first['bytes_recv']),
                       format_bytes(last['bytes_recv']),
                       diff_str(first['bytes_recv'], last['bytes_recv']))
        table.add_row("Paquetes Out", str(first['packets_sent']),
                       str(last['packets_sent']),
                       diff_str(first['packets_sent'], last['packets_sent'], fmt=False))
        table.add_row("Paquetes In", str(first['packets_recv']),
                       str(last['packets_recv']),
                       diff_str(first['packets_recv'], last['packets_recv'], fmt=False))
        table.add_row("Errores",
                       str(first['errin'] + first['errout']),
                       str(last['errin'] + last['errout']),
                       diff_str(first['errin'] + first['errout'],
                                last['errin'] + last['errout'], fmt=False))
        table.add_row("Descartados",
                       str(first['dropin'] + first['dropout']),
                       str(last['dropin'] + last['dropout']),
                       diff_str(first['dropin'] + first['dropout'],
                                last['dropin'] + last['dropout'], fmt=False))
        table.add_row("Duración", f"{elapsed:.1f}s", "", "")

        console.print(table)
