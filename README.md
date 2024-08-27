# Proxy-Digger - Parallel Proxy Scraper & Checker
Proxy-Digger is a fork of Lunus BPS, a tool to obtain proxies and verify if they are valid in real-time. We have added support for HTTP/s, SOCKS4, and SOCKS5. When verifying the proxies, your computer might slow down a bit due to the threads.

This Version is a reworked version of the original Lunus BPS, which was made by [some hackers(?)](https://github.com/H4cK3dR4Du/LunusBPS).
I've completely rewrite all codebase, added a lot of new features and fixed some bugs.
I've also added a new UI and use httpX instead of requests.
I've added a proxy backup feature, so you can always go back to the previous scan.
I've added command-line arguments, so you can configure the program without the need to edit the code.

## 🔥 Features
- Proxy Scraper
- Proxy Checker
- Around 150K+ Proxies
- Fast & Slick UI (CLI)
- Easy To Setup
- Use httpX instead of requests
- HTTP/S, SOCKS4 & SOCKS5 Scraper/Checker
- Automatic backup of previous scans

## ✨ Issues / Ideas / Help / Suggestions / Etc
- If you have any questions do not hesitate to parcipiate [GitHub duscussions](https://github.com/vshuraeff/LunusBPS-reworked/discussions)
- Or if you have any error do not forget to report it in: [issues](https://github.com/vshuraeff/LunusBPS-reworked/issues/new)

## 🚀 Installation
```bash
git clone git@github.com:vshuraeff/Proxy-Digger.git
cd Proxy-Digger
pip install -r requirements.txt
```

## 📝 Usage
```bash
python main.py --threads 500 --backup 0
```

## Known Issues
- If you are using UNIX-type system like MacOS or some Linux and set `--threads` value too high you might have issue with error `OSError: [Errno 24] Too many open files: 'results/http.txt'`. To solve this issue you have to execute command
```bash
ulimit -n 4096 # before running the script
```

## Donations
If you want to support me, you can donate me some money. I will be very grateful for any amount. [Donate](https://www.buymeacoffee.com/vshuraeff)
### Cryptocurrency
# markdown table with addresses

| Coin | Address |
| --- | --- |
| `BTC` |`bc1qq49sptu453xphfj473xuk873lwrp6fl8mhq9j4` |
| `TRX/TRC20/USDT` | `TMNGbu954dvPqzuvr3WDEXoHuRQ2ap17v6` |
| `ETH/ERC20/USDT` | `0x692591E7534000a1B666f2bF124a73d2aAFd4605` |

## ⚠️ DISCLAIMER / NOTES
This github repo is for EDUCATIONAL PURPOSES ONLY. We Are NOT under any responsibility if any problems occurs.
