import requests
import time
import random
import statistics
import platform
import subprocess
import re
from dns import resolver
from .dns_utils import get_system_dns

def test_download(output_signal):
    download_servers = [
        ("Cloudflare", "https://speed.cloudflare.com/__down?bytes=25000000"),
        ("OVH", "https://proof.ovh.net/files/10Mb.dat"),
        ("TadServer", "https://speed.tadserver.com/100MB.test"),
        ("ThinkBroadband", "http://ipv4.download.thinkbroadband.com/20MB.zip"),
    ]

    speed = 0
    for name, url in download_servers:
        try:
            start = time.time()
            r = requests.get(url, stream=True, timeout=45)
            r.raise_for_status()
            downloaded = 0
            for chunk in r.iter_content(chunk_size=1024*1024):
                downloaded += len(chunk)
                if downloaded >= 20_000_000:
                    break
            duration = time.time() - start
            if duration > 0 and downloaded > 5_000_000:
                speed = (downloaded * 8) / (duration * 1_000_000)
                size_mb = downloaded / (1024 * 1024)
                output_signal.emit(f"Download: {speed:.2f} Mbps ({size_mb:.1f} MB) via {name}\n")
                return speed
        except Exception as e:
            output_signal.emit(f"{name} failed: {str(e)[:50]}... trying next\n")
    if speed == 0:
        output_signal.emit("All download servers failed.\n")
    return speed

def test_upload(output_signal):
    volume_mb = 2
    data = bytes(random.randbytes(volume_mb * 1024 * 1024))
    upload_servers = [
        "https://httpbin.org/post",
        "https://postman-echo.com/post",
        "https://bin.org/post",
    ]

    speed = 0
    for url in upload_servers:
        try:
            start = time.time()
            r = requests.post(url, data=data, timeout=60)
            if r.status_code in (200, 201):
                duration = time.time() - start
                if duration > 0:
                    speed = (len(data) * 8) / (duration * 1_000_000)
                    output_signal.emit(f"Upload: {speed:.2f} Mbps ({volume_mb} MB)\n")
                    return speed
        except:
            pass
    if speed == 0:
        output_signal.emit("All upload servers failed.\n")
    return speed

def test_jitter(output_signal, samples=10):
    latencies = []
    for _ in range(samples):
        try:
            start = time.time()
            requests.get("https://api.ipify.org", timeout=20).raise_for_status()
            latencies.append((time.time() - start) * 1000)
        except:
            pass
    if len(latencies) >= 2:
        jitter = statistics.stdev(latencies)
        output_signal.emit(f"Jitter: {jitter:.2f} ms\n")
        return jitter
    return 0

def test_ping(output_signal):
    count = 10
    cmd = ["ping", "-n" if platform.system().lower() == "windows" else "-c", str(count), "1.1.1.1"]
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, timeout=45, text=True, encoding='utf-8', errors='ignore')

        sent_match = re.search(r'(\d+)\s*(پکت|packet|ارسال|transmitted|sent)', output, re.I)
        recv_match = re.search(r'(\d+)\s*(دریافت|received|recv)', output, re.I)
        sent = int(sent_match.group(1)) if sent_match else count
        recv = int(recv_match.group(1)) if recv_match else 0
        packet_loss = (sent - recv) / sent * 100 if sent > 0 else 0

        avg_match = re.search(r'(میانگین|متوسط|Average|avg)\s*[=:]\s*(\d+\.?\d*)\s*(ms|میلی‌ثانیه)', output, re.I)
        if avg_match:
            avg_ping = float(avg_match.group(2))
        else:
            rtt_match = re.search(r'rtt.*=\s*[\d.]+/([\d.]+)/[\d.]+/[\d.]+', output, re.I)
            avg_ping = float(rtt_match.group(1)) if rtt_match else 9999
            if avg_ping == 9999 and recv > 0:
                time_matches = re.findall(r'time[=<]\s*(\d+\.?\d*)\s*ms', output, re.I)
                if time_matches:
                    avg_ping = sum(float(t) for t in time_matches) / len(time_matches)

        output_signal.emit(f"Ping results: Sent {sent}, Received {recv}\nAverage ping: {avg_ping:.1f} ms | Packet Loss: {packet_loss:.2f}%\n")
        return avg_ping if avg_ping < 9999 else 0, packet_loss
    except:
        output_signal.emit("Ping failed.\n")
        return 0, 100

def test_dns(output_signal):
    dns_server = get_system_dns()
    dns_times = []
    try:
        resolv = resolver.Resolver()
        resolv.nameservers = [dns_server] if dns_server != "Unknown" else ['1.1.1.1']
        for _ in range(5):
            try:
                start = time.time()
                resolv.resolve("google.com", "A")
                dns_times.append((time.time() - start) * 1000)
            except:
                dns_times.append(9999)
        if dns_times and any(t < 9999 for t in dns_times):
            avg_dns = statistics.mean([t for t in dns_times if t < 9999])
            output_signal.emit(f"DNS response time: {avg_dns:.1f} ms (Server: {dns_server})\n")
            return avg_dns, dns_server
    except:
        output_signal.emit("DNS test failed.\n")
    return 9999, dns_server