import psutil
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from collections import Counter

console = Console()


class ConnectionTracker:
    def __init__(self):
        self.blocked_ips = set()

    def get_connections(self, kind='inet'):
        try:
            return psutil.net_connections(kind=kind)
        except psutil.AccessDenied:
            console.print("[bold red]Acceso denegado. Ejecuta con sudo.[/bold red]")
            return []

    def _safe_process(self, pid):
        if pid is None or pid <= 0:
            return "N/A"
        try:
            return psutil.Process(pid).name()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return "N/A"

    def _parse_ip(self, addr):
        if '[' in addr:
            bracket_end = addr.rfind(']')
            if bracket_end != -1:
                return addr[1:bracket_end]
        parts = addr.rsplit(':', 1)
        return parts[0] if len(parts) == 2 else addr

    def _format_addr(self, addr):
        if not addr:
            return "N/A"
        return f"{addr.ip}:{addr.port}"

    def list_connections(self, show_all=False):
        conns = self.get_connections()
        table = Table(title="Conexiones Activas", show_header=True, header_style="bold cyan")
        table.add_column("PID", justify="right", style="bold")
        table.add_column("Local Address", style="green")
        table.add_column("Remote Address", style="yellow")
        table.add_column("Estado", style="bold")
        table.add_column("Proceso")

        state_colors = {
            'ESTABLISHED': 'green',
            'LISTEN': 'blue',
            'TIME_WAIT': 'yellow',
            'CLOSE_WAIT': 'red',
            'FIN_WAIT1': 'magenta',
            'FIN_WAIT2': 'magenta',
            'SYN_SENT': 'cyan',
            'SYN_RECV': 'cyan',
            'CLOSING': 'red',
            'LAST_ACK': 'red',
            'NONE': 'dim',
        }

        for conn in conns:
            local = self._format_addr(conn.laddr)
            remote = self._format_addr(conn.raddr)
            state = conn.status or "NONE"

            if not show_all and state == 'NONE':
                continue

            remote_ip = self._parse_ip(remote) if remote != "N/A" else ""
            if remote_ip and remote_ip in self.blocked_ips:
                state = "[bold red]BLOQUEADO[/bold red]"

            s_color = state_colors.get(state if not state.startswith('[') else '', 'white')
            proc_name = self._safe_process(conn.pid)

            table.add_row(
                str(conn.pid) if conn.pid else "-",
                local,
                remote,
                f"[{s_color}]{state}[/{s_color}]" if not state.startswith('[') else state,
                proc_name
            )

        console.print(table)

    def connections_by_state(self):
        conns = self.get_connections()
        states = Counter(c.status or 'NONE' for c in conns)
        table = Table(title="Conexiones por Estado", show_header=True, header_style="bold cyan")
        table.add_column("Estado", style="bold")
        table.add_column("Cantidad", justify="right")

        for state, count in states.most_common():
            table.add_row(state, str(count))

        console.print(table)

    def connections_by_process(self):
        conns = self.get_connections()
        proc_conns = {}
        for conn in conns:
            name = self._safe_process(conn.pid)
            proc_conns.setdefault(name, {'count': 0, 'pids': set()})
            proc_conns[name]['count'] += 1
            if conn.pid:
                proc_conns[name]['pids'].add(conn.pid)

        table = Table(title="Conexiones por Proceso", show_header=True, header_style="bold cyan")
        table.add_column("Proceso", style="bold")
        table.add_column("Conexiones", justify="right")
        table.add_column("PIDs")

        for name, data in sorted(proc_conns.items(), key=lambda x: x[1]['count'], reverse=True):
            pids = ', '.join(str(p) for p in sorted(data['pids'])) if data['pids'] else "-"
            table.add_row(name, str(data['count']), pids)

        console.print(table)

    def top_remote_hosts(self, limit=15):
        conns = self.get_connections()
        host_counts = Counter()
        for conn in conns:
            if conn.raddr:
                host = conn.raddr.ip
                host_counts[host] += 1

        table = Table(title=f"Top {limit} Hosts Remotos", show_header=True, header_style="bold cyan")
        table.add_column("#", justify="right", style="bold")
        table.add_column("Host Remoto", style="yellow")
        table.add_column("Conexiones", justify="right")

        for i, (host, count) in enumerate(host_counts.most_common(limit), 1):
            table.add_row(str(i), host, str(count))

        console.print(table)

    def find_pid_by_port(self, port):
        conns = self.get_connections()
        for conn in conns:
            if conn.laddr and conn.laddr.port == port:
                return conn.pid, self._safe_process(conn.pid), conn.status or "N/A"
        return None, None, None
