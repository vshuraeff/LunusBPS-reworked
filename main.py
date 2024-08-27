import os, sys, shutil
from concurrent.futures import ThreadPoolExecutor
import time
from datetime import datetime
from pathlib import Path
import ipaddress
import httpx
import socks
import socket
from loguru import logger
import argparse
from rich.progress import Progress, TextColumn, BarColumn, TaskID, TimeRemainingColumn
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.console import Group
from rich.control import Control
from rich.text import Text

console = Console()
logger.remove()
logger.add(lambda msg: console.print(msg, markup=True, end=""), format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{message}</cyan>")

def format_stats(checked, total, http_found, socks4_found, socks5_found, speed, eta):
    return (
        f"Checked: {checked}/{total} | "
        f"HTTP: {http_found} | "
        f"SOCKS4: {socks4_found} | "
        f"SOCKS5: {socks5_found} | "
        f"Speed: {speed:.2f} proxies/s | "
        f"ETA: {eta}"
    )

https_scraped = socks4_scraped = socks5_scraped = 0
http_checked = socks4_checked = socks5_checked = 0

http_links = [
    "https://api.proxyscrape.com/?request=getproxies&proxytype=https&timeout=10000&country=all&ssl=all&anonymity=all",
    "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/MuRongPIG/Proxy-Master/main/http.txt",
    "https://raw.githubusercontent.com/prxchk/proxy-list/main/http.txt",
    "https://raw.githubusercontent.com/saisuiu/Lionkings-Http-Proxys-Proxies/main/cnfree.txt",
    "https://raw.githubusercontent.com/Anonym0usWork1221/Free-Proxies/main/proxy_files/http_proxies.txt",
    "https://raw.githubusercontent.com/Anonym0usWork1221/Free-Proxies/main/proxy_files/https_proxies.txt",
    "https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt",
    "https://raw.githubusercontent.com/officialputuid/KangProxy/KangProxy/https/https.txt",
    "https://raw.githubusercontent.com/officialputuid/KangProxy/KangProxy/http/http.txt"
]

socks4_list = [
    "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=socks4",
    "https://api.proxyscrape.com/?request=displayproxies&proxytype=socks4&country=all",
    "https://api.openproxylist.xyz/socks4.txt",
    "https://proxyspace.pro/socks4.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks4.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies_anonymous/socks4.txt",
    "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-socks4.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks4.txt",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt",
    "https://raw.githubusercontent.com/roosterkid/openproxylist/main/SOCKS4_RAW.txt",
    "https://proxyspace.pro/socks4.txt",
    "https://www.proxy-list.download/api/v1/get?type=socks4",
    "https://raw.githubusercontent.com/HyperBeats/proxy-list/main/socks4.txt",
    "https://raw.githubusercontent.com/mmpx12/proxy-list/master/socks4.txt",
    "https://raw.githubusercontent.com/saschazesiger/Free-Proxies/master/proxies/socks4.txt",
    "https://raw.githubusercontent.com/B4RC0DE-TM/proxy-list/main/SOCKS4.txt",
    "https://raw.githubusercontent.com/rdavydov/proxy-list/main/proxies/socks4.txt",
    "https://raw.githubusercontent.com/rdavydov/proxy-list/main/proxies_anonymous/socks4.txt",
    "https://raw.githubusercontent.com/zevtyardt/proxy-list/main/socks4.txt",
    "https://raw.githubusercontent.com/MuRongPIG/Proxy-Master/main/socks4.txt",
    "https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/master/socks4.txt",
    "https://raw.githubusercontent.com/prxchk/proxy-list/main/socks4.txt",
    "https://raw.githubusercontent.com/ALIILAPRO/Proxy/main/socks4.txt",
    "https://raw.githubusercontent.com/zloi-user/hideip.me/main/socks4.txt",
    # "https://www.proxyscan.io/download?type=socks4," # This link is not working
]

socks5_list = [
    "https://raw.githubusercontent.com/B4RC0DE-TM/proxy-list/main/SOCKS5.txt",
    "https://raw.githubusercontent.com/saschazesiger/Free-Proxies/master/proxies/socks5.txt",
    "https://raw.githubusercontent.com/mmpx12/proxy-list/master/socks5.txt",
    "https://raw.githubusercontent.com/HyperBeats/proxy-list/main/socks5.txt",
    "https://api.openproxylist.xyz/socks5.txt",
    "https://api.proxyscrape.com/?request=displayproxies&proxytype=socks5",
    "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=socks5",
    "https://proxyspace.pro/socks5.txt",
    "https://raw.githubusercontent.com/manuGMG/proxy-365/main/SOCKS5.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies_anonymous/socks5.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks5.txt",
    "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-socks5.txt",
    "https://raw.githubusercontent.com/roosterkid/openproxylist/main/SOCKS5_RAW.txt",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt",
    "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt",
    "https://raw.githubusercontent.com/rdavydov/proxy-list/main/proxies/socks5.txt",
    "https://raw.githubusercontent.com/rdavydov/proxy-list/main/proxies_anonymous/socks5.txt",
    "https://raw.githubusercontent.com/zevtyardt/proxy-list/main/socks5.txt",
    "https://raw.githubusercontent.com/MuRongPIG/Proxy-Master/main/socks5.txt",
    "https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/master/socks5.txt",
    "https://raw.githubusercontent.com/prxchk/proxy-list/main/socks5.txt",
    "https://raw.githubusercontent.com/ALIILAPRO/Proxy/main/socks5.txt",
    "https://spys.me/socks.txt",
    "https://raw.githubusercontent.com/zloi-user/hideip.me/main/socks5.txt"
]

def is_valid_ip(ip):
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False

def scrape_proxy_link(link, proxy_type):
    try:
        response = httpx.get(link, timeout=10)
        if response.status_code == 200:
            proxies = response.text.splitlines()
            valid_proxies = [proxy for proxy in proxies if ":" in proxy and is_valid_ip(proxy.split(":")[0])]
            logger.info(f"Scraped {len(valid_proxies)} {proxy_type} proxies from {link[:50]}...")
            return valid_proxies
    except Exception as e:
        logger.error(f"Error scraping {proxy_type} from {link}: {e}")
    return []

def scrape_proxy_links(links, proxy_type):
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(lambda link: scrape_proxy_link(link, proxy_type), links))
    return [proxy for sublist in results for proxy in sublist]

def check_proxy_http(proxy):
    global http_checked
    proxy_url = f"http://{proxy}"
    try:
        with httpx.Client(proxies={"http://": proxy_url, "https://": proxy_url}, timeout=10) as client:
            r = client.get("http://httpbin.org/get")
        if r.status_code == 200:
            http_checked += 1
            return proxy
    except Exception:
        pass
    return None

def check_proxy_socks(proxy, proxy_type):
    global socks4_checked, socks5_checked
    try:
        proxy_host, proxy_port = proxy.split(':')
        proxy_port = int(proxy_port)
        with socks.socksocket() as s:
            if proxy_type == "socks4":
                s.set_proxy(socks.SOCKS4, proxy_host, proxy_port)
            elif proxy_type == "socks5":
                s.set_proxy(socks.SOCKS5, proxy_host, proxy_port)
            s.settimeout(5)
            s.connect(("www.google.com", 443))
        if proxy_type == "socks4":
            socks4_checked += 1
        elif proxy_type == "socks5":
            socks5_checked += 1
        return proxy
    except Exception:
        pass
    return None

def check_proxy(proxy_type, proxy, results_file):
    result = None
    if proxy_type == "http":
        result = check_proxy_http(proxy)
    elif proxy_type in ["socks4", "socks5"]:
        result = check_proxy_socks(proxy, proxy_type)

    if result:
        with open(results_file, "a") as f:
            f.write(f"{result}\n")
        logger.info(f"Valid {proxy_type.upper()} -> {result}")

    return result

def backup_results(results_directory):
    backup_directory = results_directory / 'backup' / datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_directory.mkdir(parents=True, exist_ok=True)
    for file in results_directory.glob("*.txt"):
        if file.is_file():
            shutil.move(file, backup_directory)
    logger.info(f"Backed up existing results to {backup_directory}")

def main(args):
    results_directory = Path("results")
    results_directory.mkdir(exist_ok=True)

    if args.backup:
        backup_results(results_directory)

    all_proxies = {}
    total_proxies = 0
    for proxy_type, links in [("http", http_links), ("socks4", socks4_list), ("socks5", socks5_list)]:
        all_proxies[proxy_type] = scrape_proxy_links(links, proxy_type)
        total_proxies += len(all_proxies[proxy_type])
        logger.info(f"Scraped {len(all_proxies[proxy_type])} {proxy_type} proxies")

    progress = Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeRemainingColumn(),
        TextColumn("{task.fields[stats]}"),
    )

    def get_renderable():
        return Group(
            Panel(progress, title="Progress", border_style="cyan"),
            Control()
        )

    total_checked = 0
    start_time = time.time()
    with Live(get_renderable(), console=console, refresh_per_second=4) as live:
        task = progress.add_task(
            "[cyan]Checking proxies...",
            total=total_proxies,
            stats=format_stats(0, total_proxies, 0, 0, 0, 0, "N/A")
        )

        for proxy_type in ["http", "socks4", "socks5"]:
            results_file = results_directory / f"{proxy_type}.txt"

            with ThreadPoolExecutor(max_workers=args.threads) as executor:
                futures = [executor.submit(check_proxy, proxy_type, proxy, results_file)
                           for proxy in all_proxies[proxy_type]]
                for future in futures:
                    result = future.result()
                    total_checked += 1

                    elapsed_time = time.time() - start_time
                    speed = total_checked / elapsed_time if elapsed_time > 0 else 0
                    remaining_proxies = total_proxies - total_checked
                    eta_seconds = remaining_proxies / speed if speed > 0 else 0
                    eta = time.strftime("%H:%M:%S", time.gmtime(eta_seconds))

                    progress.update(
                        task,
                        advance=1,
                        stats=format_stats(
                            total_checked,
                            total_proxies,
                            http_checked,
                            socks4_checked,
                            socks5_checked,
                            speed,
                            eta
                        )
                    )
                    live.refresh()

    console.show_cursor()  # Ensure cursor is shown after the process is complete

    logger.info("Proxy checking completed.")
    logger.info(f"Total proxies checked: {total_checked}/{total_proxies}")
    logger.info(f"HTTP/S proxies found: {http_checked}")
    logger.info(f"SOCKS4 proxies found: {socks4_checked}")
    logger.info(f"SOCKS5 proxies found: {socks5_checked}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Proxy scraper and checker")
    parser.add_argument("-t", "--threads", type=int, default=500, help="Number of threads to use")
    parser.add_argument("-b", "--backup", action="store_true", help="Backup old results before starting")
    args = parser.parse_args()

    try:
        main(args)
    except KeyboardInterrupt:
        logger.info("Exiting...")
        sys.exit(0)
