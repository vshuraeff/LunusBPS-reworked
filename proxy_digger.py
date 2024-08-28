import asyncio
import httpx
import aiofiles
from pathlib import Path
import time
import ipaddress
import uvloop
import shutil
from datetime import datetime
from rich.progress import Progress, TextColumn, BarColumn, TimeRemainingColumn
from rich.live import Live
from rich.console import Console
from rich.panel import Panel
from rich.console import Group
import argparse
from proxy_sources import http_links, socks4_list, socks5_list
import socket
import socks
import aiohttp
from aiohttp import ClientTimeout, ClientError
from aiohttp_socks import ProxyConnector
import warnings
import logging
import ssl

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
console = Console()

# Global counters
checked_proxies = {'http': 0, 'socks4': 0, 'socks5': 0}
valid_proxies = {'http': 0, 'socks4': 0, 'socks5': 0}
start_times = {'http': 0, 'socks4': 0, 'socks5': 0}

# Suppress specific RuntimeWarnings
warnings.filterwarnings("ignore", category=RuntimeWarning, message="Enable tracemalloc to get the object allocation traceback")
warnings.filterwarnings("ignore", category=RuntimeWarning, message="An HTTPS request is being sent through an HTTPS proxy.*")

# Set logging level to suppress most warnings
logging.getLogger("asyncio").setLevel(logging.ERROR)
logging.getLogger("aiohttp").setLevel(logging.ERROR)

async def download_proxies(session, url):
    try:
        async with session.get(url, timeout=30) as response:
            if response.status == 200:
                proxies = (await response.text()).splitlines()
                return [proxy for proxy in proxies if ':' in proxy and await is_valid_ip(proxy.split(':')[0])]
    except Exception:
        pass
    return []

async def is_valid_ip(ip):
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False

async def check_proxy(proxy, proxy_type):
    global checked_proxies, valid_proxies
    max_retries = 3
    retry_delay = 1

    for attempt in range(max_retries):
        try:
            proxy_url = f'{proxy_type}://{proxy}'
            proxy_ip = proxy.split(':')[0]

            if proxy_type == 'http':
                connector = aiohttp.TCPConnector(ssl=False)
                proxy_auth = proxy_url
            else:  # socks4 or socks5
                connector = ProxyConnector.from_url(proxy_url, ssl=False)
                proxy_auth = None

            timeout = ClientTimeout(total=30, connect=10)
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                async with session.get('http://echo.free.beeceptor.com', proxy=proxy_auth, ssl=ssl_context) as response:
                    checked_proxies[proxy_type] += 1
                    if response.status == 200:
                        response_json = await response.json()
                        if response_json.get('ip').split(":")[0] == proxy_ip:
                            valid_proxies[proxy_type] += 1
                            return proxy
            break  # If we reach here without exceptions, break the retry loop
        except (ClientError, asyncio.TimeoutError, ssl.SSLError, RuntimeError) as e:
            if attempt == max_retries - 1:  # Last attempt
                checked_proxies[proxy_type] += 1
                console.print(f"[red]Failed to check proxy {proxy} after {max_retries} attempts: {str(e)}[/red]") if args.verbose else None
            else:
                console.print(f"[yellow]Retrying proxy {proxy} after error: {str(e)}[/yellow]") if args.verbose else None
                await asyncio.sleep(retry_delay)
        except Exception as e:
            checked_proxies[proxy_type] += 1
            console.print(f"[red]Unexpected error checking proxy {proxy}: {str(e)}[/red]") if args.verbose else None
            break  # For other exceptions, don't retry
    return None

async def worker(queue, proxy_type, results_file, progress, task_id):
    while True:
        proxy = await queue.get()
        result = await check_proxy(proxy, proxy_type)
        if result:
            async with aiofiles.open(results_file, 'a') as f:
                await f.write(f"{result}\n")
        progress.update(task_id, advance=1, checked=checked_proxies[proxy_type], valid=valid_proxies[proxy_type])
        queue.task_done()

async def check_proxies(proxies, proxy_type, results_file, progress, task_id, concurrency):
    queue = asyncio.Queue()
    for proxy in proxies:
        await queue.put(proxy)

    start_times[proxy_type] = int(time.time())

    workers = [asyncio.create_task(worker(queue, proxy_type, results_file, progress, task_id))
               for _ in range(concurrency)]

    await queue.join()

    for w in workers:
        w.cancel()

def backup_results(results_directory):
    backup_directory = results_directory / 'backup' / datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_directory.mkdir(parents=True, exist_ok=True)
    for file in results_directory.glob("*.txt"):
        if file.is_file():
            shutil.move(file, backup_directory)
    console.print(f"[yellow]Backed up existing results to {backup_directory}[/yellow]")

async def main(args):
    global checked_proxies, valid_proxies, start_times
    results_dir = Path('results')
    results_dir.mkdir(exist_ok=True)

    if args.backup:
        backup_results(results_dir)

    proxy_sources = {
        'http': http_links,
        'socks4': socks4_list,
        'socks5': socks5_list
    }

    all_proxies = {}
    async with aiohttp.ClientSession() as session:
        for proxy_type, urls in proxy_sources.items():
            all_proxies[proxy_type] = []
            tasks = [download_proxies(session, url) for url in urls]
            results = await asyncio.gather(*tasks)
            for proxies in results:
                all_proxies[proxy_type].extend(proxies)
            all_proxies[proxy_type] = list(set(all_proxies[proxy_type]))  # Remove duplicates
            console.print(f"Total {proxy_type.upper()} proxies: {len(all_proxies[proxy_type])}")

    total_proxies = sum(len(proxies) for proxies in all_proxies.values())

    progress = Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn("Checked: {task.fields[checked]}/{task.total}"),
        TextColumn("Valid: {task.fields[valid]}"),
        TextColumn("Speed: {task.fields[speed]:.2f} p/s"),
        TimeRemainingColumn(),
    )

    def get_renderable():
        return Group(
            Panel(progress, title="Progress", border_style="cyan"),
        )

    start_time = time.time()

    with Live(get_renderable(), console=console, refresh_per_second=4) as live:
        tasks = {}
        for proxy_type, proxies in all_proxies.items():
            tasks[proxy_type] = progress.add_task(f"[cyan]Checking {proxy_type.upper()}...", total=len(proxies), checked=0, valid=0, speed=0)

        async def update_progress():
            while any(not progress.tasks[task].finished for task in tasks.values()):
                for proxy_type, task_id in tasks.items():
                    elapsed = int(time.time()) - start_times[proxy_type]
                    speed = checked_proxies[proxy_type] / elapsed if elapsed > 0 else 0
                    progress.update(task_id, checked=checked_proxies[proxy_type], valid=valid_proxies[proxy_type], speed=speed)
                await asyncio.sleep(0.25)

        update_task = asyncio.create_task(update_progress())

        for proxy_type, proxies in all_proxies.items():
            results_file = results_dir / f'{proxy_type}.txt'
            await check_proxies(proxies, proxy_type, results_file, progress, tasks[proxy_type], args.concurrency)

        await update_task

    elapsed_time = time.time() - start_time
    total_checked = sum(checked_proxies.values())
    total_valid = sum(valid_proxies.values())
    speed = total_checked / elapsed_time if elapsed_time > 0 else 0

    console.print(f"\n[green]Proxy checking completed in {elapsed_time:.2f} seconds.[/green]")
    console.print(f"Total proxies checked: {total_checked}")
    console.print(f"Total valid proxies found: {total_valid}")
    console.print(f"Average speed: {speed:.2f} proxies/second")
    for proxy_type in checked_proxies:
        console.print(f"{proxy_type.upper()} proxies checked: {checked_proxies[proxy_type]}, valid: {valid_proxies[proxy_type]}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Proxy scraper and checker")
    parser.add_argument("-c", "--concurrency", type=int, default=1000, help="Number of concurrent tasks")
    parser.add_argument("-b", "--backup", action="store_true", help="Backup old results before starting")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    args = parser.parse_args()

    uvloop.install()
    try:
        asyncio.run(main(args))
    except KeyboardInterrupt:
        console.print("[yellow]Exiting...[/yellow]")
