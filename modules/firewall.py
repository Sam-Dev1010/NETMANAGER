import json
import os
import subprocess
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from modules.utils import get_rules_path, is_root, is_windows

console = Console()


class FirewallManager:
    def __init__(self):
        self.rules = []
        self.blocked_ips = set()
        self.blocked_ports = set()
        self.allowed_ips = set()
        self.rules_file = get_rules_path()
        self.load_rules()

    def load_rules(self):
        if os.path.exists(self.rules_file):
            try:
                with open(self.rules_file, 'r') as f:
                    data = json.load(f)
                self.blocked_ips = set(data.get('blocked_ips', []))
                self.blocked_ports = set(data.get('blocked_ports', []))
                self.allowed_ips = set(data.get('allowed_ips', []))
                self.rules = data.get('rules', [])
                console.print(f"[green]Reglas cargadas: {len(self.rules)} reglas, {len(self.blocked_ips)} IPs bloqueadas[/green]")
            except Exception as e:
                console.print(f"[red]Error cargando reglas: {e}[/red]")

    def save_rules(self):
        data = {
            'blocked_ips': list(self.blocked_ips),
            'blocked_ports': list(self.blocked_ports),
            'allowed_ips': list(self.allowed_ips),
            'rules': self.rules,
        }
        with open(self.rules_file, 'w') as f:
            json.dump(data, f, indent=2)
        console.print(f"[green]Reglas guardadas en {self.rules_file}[/green]")

    def _apply_iptables(self, action, target, port=None):
        if is_windows() or not is_root():
            return
        try:
            if port:
                cmd = ['iptables', '-A', 'INPUT', '-p', 'tcp', '--dport', str(port), '-j', action]
            else:
                cmd = ['iptables', '-A', 'INPUT', '-s' if action == 'DROP' else '-d', target, '-j', action]
            subprocess.run(cmd, capture_output=True, timeout=5)
        except Exception:
            pass

    def _remove_iptables(self, target, port=None):
        if is_windows() or not is_root():
            return
        try:
            if port:
                cmd = ['iptables', '-D', 'INPUT', '-p', 'tcp', '--dport', str(port), '-j', 'DROP']
            else:
                cmd = ['iptables', '-D', 'INPUT', '-s', target, '-j', 'DROP']
            subprocess.run(cmd, capture_output=True, timeout=5)
        except Exception:
            pass

    def block_ip(self, ip, reason="manual"):
        self.blocked_ips.add(ip)
        self.rules.append({
            'type': 'block_ip', 'target': ip, 'reason': reason, 'action': 'BLOCK'
        })
        self._apply_iptables('DROP', ip)
        self.save_rules()
        console.print(f"[bold red]IP bloqueada: {ip} (razón: {reason})[/bold red]")

    def unblock_ip(self, ip):
        if ip in self.blocked_ips:
            self.blocked_ips.discard(ip)
            self.rules = [r for r in self.rules if not (r['type'] == 'block_ip' and r['target'] == ip)]
            self._remove_iptables(ip)
            self.save_rules()
            console.print(f"[bold green]IP desbloqueada: {ip}[/bold green]")
        else:
            console.print(f"[yellow]IP {ip} no está bloqueada.[/yellow]")

    def block_port(self, port, reason="manual"):
        self.blocked_ports.add(port)
        self.rules.append({
            'type': 'block_port', 'target': str(port), 'reason': reason, 'action': 'BLOCK'
        })
        self._apply_iptables('DROP', None, port)
        self.save_rules()
        console.print(f"[bold red]Puerto bloqueado: {port} (razón: {reason})[/bold red]")

    def unblock_port(self, port):
        if port in self.blocked_ports:
            self.blocked_ports.discard(port)
            self.rules = [r for r in self.rules if not (r['type'] == 'block_port' and r['target'] == str(port))]
            self._remove_iptables(None, port)
            self.save_rules()
            console.print(f"[bold green]Puerto desbloqueado: {port}[/bold green]")
        else:
            console.print(f"[yellow]Puerto {port} no está bloqueado.[/yellow]")

    def allow_ip(self, ip):
        self.allowed_ips.add(ip)
        self.rules.append({
            'type': 'allow_ip', 'target': ip, 'reason': 'whitelist', 'action': 'ALLOW'
        })
        self.save_rules()
        console.print(f"[bold green]IP permitida: {ip}[/bold green]")

    def remove_allowed_ip(self, ip):
        self.allowed_ips.discard(ip)
        self.rules = [r for r in self.rules if not (r['type'] == 'allow_ip' and r['target'] == ip)]
        self.save_rules()
        console.print(f"[yellow]IP removida de whitelist: {ip}[/yellow]")

    def is_blocked(self, ip, port=None):
        if ip in self.blocked_ips:
            return True
        if port and port in self.blocked_ports:
            return True
        return False

    def list_rules(self):
        if not self.rules:
            console.print("[yellow]No hay reglas definidas.[/yellow]")
            return

        table = Table(title="Reglas de Firewall", show_header=True, header_style="bold cyan")
        table.add_column("#", justify="right", style="bold")
        table.add_column("Tipo", style="bold")
        table.add_column("Objeto")
        table.add_column("Acción")
        table.add_column("Razón")

        for i, rule in enumerate(self.rules, 1):
            action_color = "red" if rule['action'] == 'BLOCK' else "green"
            table.add_row(
                str(i), rule['type'], rule['target'],
                f"[{action_color}]{rule['action']}[/{action_color}]",
                rule.get('reason', 'N/A')
            )
        console.print(table)

    def list_blocked(self):
        console.print(Panel(
            f"[bold red]IPs Bloqueadas ({len(self.blocked_ips)}):[/bold red]\n" +
            ("\n".join(f"  - {ip}" for ip in sorted(self.blocked_ips)) if self.blocked_ips else "  Ninguna") +
            f"\n\n[bold red]Puertos Bloqueados ({len(self.blocked_ports)}):[/bold red]\n" +
            ("\n".join(f"  - {p}" for p in sorted(self.blocked_ports)) if self.blocked_ports else "  Ninguno"),
            title="Elementos Bloqueados", border_style="red"
        ))

    def list_allowed(self):
        if self.allowed_ips:
            console.print(Panel(
                "\n".join(f"  - {ip}" for ip in sorted(self.allowed_ips)),
                title=f"IPs Permitidas ({len(self.allowed_ips)})", border_style="green"
            ))
        else:
            console.print("[yellow]No hay IPs en la whitelist.[/yellow]")

    def clear_all_rules(self):
        self.rules.clear()
        self.blocked_ips.clear()
        self.blocked_ports.clear()
        self.allowed_ips.clear()
        self.save_rules()
        console.print("[bold yellow]Todas las reglas han sido eliminadas.[/bold yellow]")

    def export_rules(self, filename="firewall_export.json"):
        data = {
            'blocked_ips': list(self.blocked_ips),
            'blocked_ports': list(self.blocked_ports),
            'allowed_ips': list(self.allowed_ips),
            'rules': self.rules
        }
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        console.print(f"[green]Reglas exportadas a {filename}[/green]")
