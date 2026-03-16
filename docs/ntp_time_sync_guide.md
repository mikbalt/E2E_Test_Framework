# NTP Time Synchronization Guide

## Why This Matters

Remote logs dari multiple server (e-Admin, Proxy, HSM) di-aggregate berdasarkan timestamp.
Jika jam antar server tidak sinkron, `aggregated_timeline.log` urutannya menyesatkan
dan korelasi cross-component jadi tidak akurat.

## Server Inventory

| Server              | IP / Hostname | OS              | Role                        |
|---------------------|---------------|-----------------|-----------------------------|
| I2J62-0418          | (local)       | Windows 11 Pro  | Test runner + e-Admin host  |
| HSM Proxy           | 10.66.1.10    | Windows Server  | Sphere HSM Proxy            |
| **Loki (NTP Master)** | **10.88.1.14** | **Linux**    | **Monitoring + NTP source** |
| Kiwi TCMS           | 10.88.1.13    | Linux           | Test case management        |

## Architecture

```
                    ┌──────────────────────┐
                    │   Loki Server        │
                    │   10.88.1.14         │
                    │   (NTP Master)       │
                    └──────┬───────────────┘
                           │ UDP 123
            ┌──────────────┼──────────────┐
            │              │              │
            ▼              ▼              ▼
   ┌────────────┐  ┌────────────┐  ┌────────────┐
   │ I2J62-0418 │  │ HSM Proxy  │  │ Kiwi TCMS  │
   │  (local)   │  │ 10.66.1.10 │  │ 10.88.1.13 │
   └────────────┘  └────────────┘  └────────────┘
```

Semua server sync ke **Loki server (10.88.1.14)** sebagai NTP master internal.
Alasan: jaringan internal tidak bisa reach public NTP (UDP 123 diblokir).

## Step 1: Setup Loki Server sebagai NTP Master

SSH ke Loki server (10.88.1.14):

```bash
# Cek status waktu saat ini
timedatectl status

# Cek NTP service yang aktif
systemctl status chronyd 2>/dev/null || systemctl status systemd-timesyncd 2>/dev/null
```

### Jika pakai chrony (RHEL/CentOS/Rocky):

```bash
# Edit config
sudo vi /etc/chrony.conf

# Tambahkan baris berikut agar server melayani NTP untuk jaringan internal:
allow 10.0.0.0/8

# Restart
sudo systemctl enable --now chronyd
sudo systemctl restart chronyd

# Verifikasi
chronyc sources -v
chronyc tracking
```

### Jika pakai systemd-timesyncd (Ubuntu/Debian):

systemd-timesyncd adalah client-only, tidak bisa serve NTP. Install chrony:

```bash
sudo apt install chrony -y

# Edit /etc/chrony/chrony.conf, tambahkan:
allow 10.0.0.0/8

sudo systemctl enable --now chrony
sudo systemctl restart chrony
```

### Buka firewall untuk NTP:

```bash
# firewalld (RHEL/CentOS/Rocky)
sudo firewall-cmd --add-service=ntp --permanent
sudo firewall-cmd --reload

# ufw (Ubuntu/Debian)
sudo ufw allow 123/udp
```

### Verifikasi Loki server bisa serve NTP:

```bash
# Dari Loki server sendiri, pastikan chrony listening
ss -ulnp | grep 123
```

## Step 2: Sync Windows Servers ke Loki

Jalankan **PowerShell as Administrator** di **masing-masing** Windows server
(I2J62-0418 dan HSM Proxy 10.66.1.10):

```powershell
# 1. Aktifkan & set Windows Time service auto-start
Set-Service w32time -StartupType Automatic
Start-Service w32time

# 2. Konfigurasi Loki sebagai NTP source
w32tm /config /manualpeerlist:"10.88.1.14" /syncfromflags:manual /reliable:yes /update

# 3. Restart service agar config diterapkan
Restart-Service w32time

# 4. Force sync sekarang
w32tm /resync /force

# 5. Verifikasi
w32tm /query /status
w32tm /query /peers
```

**Expected output setelah berhasil:**

```
Leap Indicator: 0(no warning)
Stratum: 4 (atau 5)
Source: 10.88.1.14
Last Successful Sync Time: <timestamp terbaru>
```

## Step 3: Sync Kiwi TCMS ke Loki

SSH ke Kiwi server (10.88.1.13):

```bash
# Jika pakai chrony
sudo vi /etc/chrony.conf
# Set server ke Loki:
server 10.88.1.14 iburst

sudo systemctl restart chronyd
chronyc sources -v

# Jika pakai systemd-timesyncd
sudo vi /etc/systemd/timesyncd.conf
# Set:
# [Time]
# NTP=10.88.1.14

sudo systemctl restart systemd-timesyncd
timedatectl timesync-status
```

## Step 4: Verifikasi Cross-Server

Dari mesin test runner (I2J62-0418), jalankan PowerShell as Admin:

```powershell
# Cek offset ke Loki (NTP master)
w32tm /stripchart /computer:10.88.1.14 /samples:5 /dataonly

# Cek offset ke HSM Proxy
w32tm /stripchart /computer:10.66.1.10 /samples:5 /dataonly
```

**Target:** offset < 100ms antar semua server.

## Troubleshooting

### `The computer did not resync because no time data was available.`

NTP source belum serve NTP. Pastikan:
1. Loki server chrony sudah running: `systemctl status chronyd`
2. Config `allow 10.0.0.0/8` ada di `/etc/chrony.conf`
3. Firewall di Loki sudah buka UDP 123

### `error: 0x800705B4` (timeout)

NTP port (UDP 123) diblokir. Buka di Loki server:

```bash
# firewalld
sudo firewall-cmd --add-service=ntp --permanent && sudo firewall-cmd --reload

# ufw
sudo ufw allow 123/udp
```

### `Source: Free-running System Clock` atau `Source: Local CMOS Clock`

Windows belum berhasil sync. Jalankan ulang:

```powershell
Restart-Service w32time
w32tm /resync /force
w32tm /query /status
```

### `Leap Indicator: 3 (not synchronized)`

NTP source tidak reachable. Cek koneksi:

```powershell
# Test UDP connectivity (via PowerShell)
Test-NetConnection 10.88.1.14 -Port 123

# Atau ping saja dulu
ping 10.88.1.14
```

### Clock drift kembali setelah beberapa hari

Default poll interval Windows = 1024 detik (~17 menit). Untuk poll lebih sering:

```powershell
# Set poll interval ke 64 detik (lebih sering sync)
w32tm /config /update /manualpeerlist:"10.88.1.14,0x1" /syncfromflags:manual
Restart-Service w32time
```

## Maintenance

NTP sync berjalan otomatis setelah dikonfigurasi. Untuk cek berkala:

```powershell
# Cek Windows Time service masih running
Get-Service w32time

# Cek last sync time
w32tm /query /status | Select-String "Last Successful"

# Quick cross-server check
w32tm /stripchart /computer:10.88.1.14 /samples:1 /dataonly
```

Jika server di-restart, `w32time` service auto-start (sudah di-set di langkah setup).
