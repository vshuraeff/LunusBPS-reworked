import os, sys, shutil
from concurrent.futures import ThreadPoolExecutor
import time
import string
import sys
import argparse
from pathlib import Path

import httpx as http
import aiosocks
import asyncio
import aiohttp_socks
import socks
import socket
import tls_client
from loguru import logger as log

from datetime import datetime
from aiohttp_socks import ProxyConnector, ProxyType
from httpx import InvalidURL, RequestError
from ipaddress import AddressValueError


log.remove()
log.add(sys.stdout, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{message}</cyan>")

https_scraped = 0
socks4_scraped = 0
socks5_scraped = 0

http_checked = 0
socks4_checked = 0
socks5_checked = 0

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

def scrape_proxy_links(link, proxy_type):
    global https_scraped, socks4_scraped, socks5_scraped
    try:
        response = http.get(link)
        if response.status_code == 200:
            log.info(f"Scraped {proxy_type} --> {link[:100]}...")
            proxies = response.text.splitlines()
            if proxy_type == "https":
                https_scraped += len(proxies)
            elif proxy_type == "socks4":
                socks4_scraped += len(proxies)
            elif proxy_type == "socks5":
                socks5_scraped += len(proxies)
            return proxies
    except Exception as e:
        log.error(f"Error scraping {proxy_type} from {link}: {e}")
    return []

def check_proxy_http(proxy):
    global http_checked
    proxy_dict = {
        "http://": f"http://{proxy}",
        "https://": f"http://{proxy}"
    }
    try:
        with http.Client(proxies=proxy_dict, timeout=30) as client:
            r = client.get("http://httpbin.org/get")
        if r.status_code == 200:
            log.info(f"Valid HTTP/S --> {proxy}")
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
        log.info(f"Valid {proxy_type.upper()} -> {proxy}")
        if proxy_type == "socks4":
            socks4_checked += 1
        elif proxy_type == "socks5":
            socks5_checked += 1
        return proxy
    except Exception:
        pass
    return None


def check_proxy(proxy_type, proxy):
    if proxy_type == "http":
        return check_proxy_http(proxy)
    elif proxy_type in ["socks4", "socks5"]:
        return check_proxy_socks(proxy, proxy_type)


def main(args):
    results_directory = Path("results")
    results_directory.mkdir(exist_ok=True)

    # Backup old results to directory with timestamp
    if args.backup:
        backup_directory = results_directory / 'backup' / \
        datetime.now().strftime("%Y-%m-%d") / \
        datetime.now().strftime("%H:%M:%S")
        backup_directory.mkdir(parents=True, exist_ok=True)
        for file in results_directory.glob("*.txt"):
            shutil.move(file, backup_directory)


    for proxy_type in ["http", "socks4", "socks5"]:
        proxy_file = results_directory / f"{proxy_type}.txt"
        proxy_file.touch()

    # Scrape proxies
    for proxy_type, links in [("http", http_links), ("socks4", socks4_list), ("socks5", socks5_list)]:
        with ThreadPoolExecutor(max_workers=args.threads) as executor:
            proxies = list(executor.map(lambda link: scrape_proxy_links(link, proxy_type), links))
        proxies = [proxy for sublist in proxies for proxy in sublist if ":" in proxy and not any(c.isalpha() for c in proxy)]
        with open(f"{proxy_type}_proxies.txt", "w") as file:
            file.write("\n".join(proxies))

    # Check proxies
    for proxy_type in ["http", "socks4", "socks5"]:
        with open(f"{proxy_type}_proxies.txt", "r") as f:
            proxies = f.read().splitlines()

        with ThreadPoolExecutor(max_workers=args.threads) as executor:
            valid_proxies = list(filter(None, executor.map(lambda p: check_proxy(proxy_type, p), proxies)))

        with open(results_directory / f"{proxy_type}.txt", "w") as f:
            f.write("\n".join(valid_proxies))

    # Clean up temporary files
    for proxy_type in ["http", "socks4", "socks5"]:
        os.remove(f"{proxy_type}_proxies.txt")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Proxy scraper and checker")
    parser.add_argument("-t", "--threads", type=int, default=100, help="Number of threads to use")
    parser.add_argument("-b", "--backup", type=bool, default=True, action="store_true", help="Backup old results")
    args = parser.parse_args()

    try:
        main(args)
    except KeyboardInterrupt:
        log.info("Exiting...")
        sys.exit(0)
