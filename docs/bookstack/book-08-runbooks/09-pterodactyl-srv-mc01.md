# Pterodactyl på srv-mc01

Panel och Wings på **en Ubuntu-VM utanför Kubernetes**. En extra spelmaskin är bara Wings: [extra nod](11-pterodactyl-extra-nod.md). Minecraft-världen som spelarna bad om (survival, PvP, bythandling) sätts upp i [Minecraft survival](10-minecraft-survival-pvp-byhandel.md).

Konfigurationen ligger **på VM:en**, inte i Git. Den här sidan är underlaget.

Officiella guider om ett kommando har flyttats:

- [Panel](https://pterodactyl.io/panel/1.0/getting_started.html)
- [Wings](https://pterodactyl.io/wings/1.0/installing.html)

## Beslut


| Val               | Här                                                                                                      |
| ----------------- | -------------------------------------------------------------------------------------------------------- |
| Var               | Proxmox-**VM**, inte LXC och inte Talos. Wings kör Docker.                                               |
| Värd              | **px-node04** i första hand. Reboot där tar inte en control-plane-nod. px-node03 (E5504) är för långsam. |
| OS                | Ubuntu 24.04 LTS                                                                                         |
| CPU-typ i Proxmox | `host`                                                                                                   |
| Resurser          | 4 vCPU, **12 GB** RAM, **80 GB** disk på **lokal** Proxmox-storage                                       |
| Nät               | VLAN 20, statisk IP i `192.168.20.0/24`                                                                  |
| Namn              | `srv-mc01.lab.engstrom.live`                                                                             |
| Panel             | Bara LAN, HTTPS. Inte Cloudflare-proxy, inte WAN.                                                        |
| Spel              | TCP **25565**. Orange-moln i Cloudflare fungerar inte för Minecraft.                                     |


Världsdisken ska inte ligga på NFS eller Longhorn. Backup-kopian kan ligga på TrueNAS.

Lämna RAM till `srv-talos04` på samma värd. 12 GB till den här VM:en är taket om värden redan är tight — sänk då Minecraft-heapen i samma proportion, inte Talos.

## Brandvägg (OPNsense)

Default deny. Öppna bara det här.


| Från                     | Till     | Port      | Syfte                                          |
| ------------------------ | -------- | --------- | ---------------------------------------------- |
| VLAN 10 (LAN)            | srv-mc01 | 443/tcp   | Panel                                          |
| VLAN 10                  | srv-mc01 | 25565/tcp | Spel hemma                                     |
| VLAN 10, din admin-dator | srv-mc01 | 2022/tcp  | SFTP för plugin-jars                           |
| VLAN 10                  | srv-mc01 | 22/tcp    | SSH, om du inte bara använder Proxmox-konsolen |
| WAN                      | srv-mc01 | 25565/tcp | Bara om vänner spelar utifrån                  |


Stäng WAN mot **443, 2022, 8080 och 22**. Wings (8080) pratar med panelen på samma maskin och ska inte nås utifrån.

Klienter på VLAN 10 ser inte servern av sig själva. "Söker efter spel på det lokala nätverket" är en broadcast som stannar i VLAN 10. Öppna TCP **25565** från VLAN 10 till VM:ens adress, och lägg till servern manuellt i Minecraft. UDP behövs inte för Java-klienten.

I OPNsense, på gränssnittet för VLAN 10: Pass, källa LAN net, destination `192.168.20.70`, TCP, port 25565. Byt adressen om VM:en fick en annan.

Från en dator på VLAN 10. PowerShell:

```powershell
Test-NetConnection 192.168.20.70 -Port 25565
```

CachyOS:

```bash
timeout 3 bash -c 'echo > /dev/tcp/192.168.20.70/25565' && echo open || echo closed
```

`open` är samma sak som `TcpTestSucceeded : True`.

Fjärrspel utan portöppning: ZeroTier, se [ZeroTier controller](08-zerotier-controller-lxc-lab.md). Då ansluter de till VM:ens overlay-IP i stället för en publik port.

## 1. Skapa VM


| Inställning      | Värde                                                          |
| ---------------- | -------------------------------------------------------------- |
| OS               | Ubuntu 24.04 Server                                            |
| Machine          | q35                                                            |
| BIOS             | OVMF (UEFI) eller SeaBIOS — följ samma som övriga Ubuntu-VM:ar |
| SCSI             | VirtIO SCSI, `discard=on`, SSD-emulering                       |
| Cache            | `none`                                                         |
| Nät              | `vmbr0`, VLAN tag **20**, statisk IP                           |
| QEMU Guest Agent | På                                                             |
| Start at boot    | På                                                             |


Efter första booten:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y qemu-guest-agent curl ca-certificates gnupg unzip tar git
sudo systemctl enable --now qemu-guest-agent
sudo hostnamectl set-hostname srv-mc01
```

Lägg en DNS-override i OPNsense: `srv-mc01.lab.engstrom.live` → VM:ens IP.

## 2. Certifikat

Panelen och Wings kräver HTTPS, och namnet i certifikatet måste vara `srv-mc01.lab.engstrom.live`.

HTTP-01 kräver att port 80 nås från internet. Använd **DNS-01** i stället, så panelen kan stanna på LAN. Ni har redan Cloudflare för `engstrom.live`; en record för det här namnet ska vara **DNS only** (grå moln) om den alls är publik.

Skapa en **ny** API-token bara för den här VM:en. Återanvänd inte klustrets.


| Befintlig hemlighet     | Används av                              | Till certbot                  |
| ----------------------- | --------------------------------------- | ----------------------------- |
| `cert-manager-secret`   | Let's Encrypt i klustret                | Nej                           |
| `cloudflare-dns-secret` | external-dns, skriver om publika poster | Nej                           |
| Tunnel-credential       | cloudflared                             | Nej, det är inte en DNS-token |


Zone ID och Account ID är id-nummer, inte tokens. De hör inte hemma i `cloudflare.ini`.

I Cloudflare: **My Profile → API Tokens → Create Token → mallen "Edit zone DNS"**.


| Fält           | Värde                                     |
| -------------- | ----------------------------------------- |
| Namn           | `certbot-srv-mc01`                        |
| Zone / DNS     | Edit (följer med mallen)                  |
| Zone / Zone    | Read (följer med mallen)                  |
| Zone Resources | Include → Specific zone → `engstrom.live` |


Inget Account-scope, ingen Global API Key. Då kan token dras tillbaka utan att röra cert-manager eller external-dns.

```bash
sudo apt install -y certbot python3-certbot-dns-cloudflare
sudo mkdir -p /root/.secrets
sudo nano /root/.secrets/cloudflare.ini
```

```ini
dns_cloudflare_api_token = klistra-token-här
```

Utan citationstecken. Token är ett enda ord utan mellanslag, och Certbots exempel skriver den naken.

```bash
sudo chmod 600 /root/.secrets/cloudflare.ini
sudo certbot certonly \
  --dns-cloudflare \
  --dns-cloudflare-credentials /root/.secrets/cloudflare.ini \
  -d srv-mc01.lab.engstrom.live
```

Filerna hamnar i `/etc/letsencrypt/live/srv-mc01.lab.engstrom.live/`. Lägg inte token i Git.

## 3. Panel

Ubuntu 24.04 har PHP 8.3 i sina egna repo. Panel 1.11+ vill ha 8.2 eller 8.3.

```bash
sudo apt install -y \
  php8.3 php8.3-{cli,gd,mysql,mbstring,bcmath,xml,fpm,curl,zip,intl} \
  mariadb-server nginx redis-server
sudo systemctl enable --now mariadb redis-server php8.3-fpm nginx
```

```bash
curl -sS https://getcomposer.org/installer | sudo php -- --install-dir=/usr/local/bin --filename=composer
```

Databas. Byt lösenordet. `sudo mariadb` loggar in som root via socket.

```sql
CREATE DATABASE panel;
CREATE USER 'pterodactyl'@'127.0.0.1' IDENTIFIED BY 'byt-mig';
GRANT ALL PRIVILEGES ON panel.* TO 'pterodactyl'@'127.0.0.1' WITH GRANT OPTION;
FLUSH PRIVILEGES;
EXIT;
```

```bash
sudo mkdir -p /var/www/pterodactyl
cd /var/www/pterodactyl
sudo curl -Lo panel.tar.gz https://github.com/pterodactyl/panel/releases/latest/download/panel.tar.gz
sudo tar -xzvf panel.tar.gz
sudo chmod -R 755 storage bootstrap/cache
sudo cp .env.example .env
sudo composer install --no-dev --optimize-autoloader
sudo php artisan key:generate --force
```

Svara på promptarna:

```bash
sudo php artisan p:environment:setup
```


| Fråga                   | Svar                                  |
| ----------------------- | ------------------------------------- |
| Egg author email        | din adress                            |
| App URL                 | `https://srv-mc01.lab.engstrom.live` |
| Timezone                | `Europe/Stockholm`                    |
| Cache / session / queue | redis                                 |
| Redis host              | `127.0.0.1`                           |


```bash
sudo php artisan p:environment:database
```

Host `127.0.0.1`, port `3306`, databas `panel`, användare `pterodactyl`.

```bash
sudo php artisan migrate --seed --force
sudo php artisan p:user:make
```

Första användaren är admin. Sätt ett långt lösenord och slå på **2FA** i panelen direkt efter första inloggningen.

```bash
sudo chown -R www-data:www-data /var/www/pterodactyl
sudo crontab -u www-data -e
```

```cron
* * * * * php /var/www/pterodactyl/artisan schedule:run >> /dev/null 2>&1
```

Kö-arbetare, `/etc/systemd/system/pteroq.service`:

```ini
[Unit]
Description=Pterodactyl Queue Worker
After=redis-server.service

[Service]
User=www-data
Group=www-data
Restart=always
ExecStart=/usr/bin/php /var/www/pterodactyl/artisan queue:work --queue=high,standard,low --sleep=3 --tries=3
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable --now pteroq.service
```

Nginx, `/etc/nginx/sites-available/pterodactyl.conf`:

```nginx
server {
    listen 80;
    server_name srv-mc01.lab.engstrom.live;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name srv-mc01.lab.engstrom.live;

    root /var/www/pterodactyl/public;
    index index.php;

    ssl_certificate     /etc/letsencrypt/live/srv-mc01.lab.engstrom.live/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/srv-mc01.lab.engstrom.live/privkey.pem;

    client_max_body_size 100m;

    location / {
        try_files $uri $uri/ /index.php?$query_string;
    }

    location ~ \.php$ {
        fastcgi_split_path_info ^(.+\.php)(/.+)$;
        fastcgi_pass unix:/run/php/php8.3-fpm.sock;
        fastcgi_index index.php;
        include fastcgi_params;
        fastcgi_param PHP_VALUE "upload_max_filesize=100M \n post_max_size=100M";
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        fastcgi_param HTTP_PROXY "";
        fastcgi_read_timeout 300;
    }

    location ~ /\.ht {
        deny all;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/pterodactyl.conf /etc/nginx/sites-enabled/pterodactyl.conf
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
```

Öppna `https://srv-mc01.lab.engstrom.live` från LAN och logga in.

## 4. Wings

```bash
curl -sSL https://get.docker.com/ | CHANNEL=stable sudo bash
sudo systemctl enable --now docker
sudo mkdir -p /etc/pterodactyl
sudo curl -L -o /usr/local/bin/wings \
  https://github.com/pterodactyl/wings/releases/latest/download/wings_linux_amd64
sudo chmod u+x /usr/local/bin/wings
```

Skapa platsen först: **Admin → Locations → Create New**. En plats är huset, inte noden. Fler noder i samma hus återanvänder den.

| Fält | Värde |
|------|-------|
| Short Code | `se-morbylanga` |
| Description | `Mörbylånga, Kalmar län` |

Short code får bara `a-z`, siffror, punkt och bindestreck. Därför `o` i stället för `ö`.

I panelen: **Admin → Nodes → Create New**.

| Fält                 | Värde                        |
| -------------------- | ---------------------------- |
| Location             | `se-morbylanga`              |
| Name                 | `mc01`                       |
| FQDN                 | `srv-mc01.lab.engstrom.live` |
| Communicate Over SSL | Ja                           |
| Behind Proxy         | Nej                          |
| Daemon Port          | `8080`                       |
| SFTP Port            | `2022`                       |
| Total Memory         | `8192` MB                    |
| Memory Overallocate  | `0`                          |
| Disk                 | `60000` MB                   |
| Disk Over-Allocation | `0`                          |

Noden har inget CPU-fält. Taket är VM:ens 4 vCPU. CPU sätts per server längre ner.


Öppna noden → fliken **Configuration**. Rutan där är bara text i panelen. Panelen skriver inte filen på VM:en.

```bash
sudo systemctl stop wings
sudo mkdir -p /etc/pterodactyl
sudo nano /etc/pterodactyl/config.yml
```

Klistra in hela rutan från **Configuration**. Spara. Filen ska heta `config.yml`, inte `config.yaml`.

```bash
sudo chmod 600 /etc/pterodactyl/config.yml
sudo systemctl start wings
```

`journalctl` som säger `Configuration File Not Found` betyder att den sökvägen saknas. Kontrollera med `sudo ls -l /etc/pterodactyl/config.yml`.

`token` är lösenordet panelen använder mot Wings. Lägg det inte i Git eller i en chatt. Behöver det bytas: nodens **Settings** → **Reset Daemon Master Key** → spara, kopiera den nya Configuration-rutan till filen och starta om Wings.

`/etc/systemd/system/wings.service`:

```ini
[Unit]
Description=Pterodactyl Wings
After=docker.service
Requires=docker.service

[Service]
User=root
WorkingDirectory=/etc/pterodactyl
LimitNOFILE=4096
ExecStart=/usr/local/bin/wings
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable --now wings
sudo systemctl status wings
```

Noden ska bli grön i panelen. Om den stannar röd: certnamnet och FQDN är olika, eller klockan på VM:en är fel (`timedatectl`).

På noden: **Allocation**. Lägg till VM:ens IP och port **25565**. Alias kan vara tomt.

## 5. Första servern

**Admin → Servers → Create New.**


| Fält              | Värde                                 |
| ----------------- | ------------------------------------- |
| Nest / Egg        | Minecraft → **Paper**                 |
| Minecraft Version | `26.2` |
| Memory            | `6144` MB                             |
| Swap              | `0`                                   |
| Disk              | `30000` MB                            |
| CPU               | `0` (obegränsat, VM:ens 4 vCPU)       |
| Databases         | `0`                                   |
| Backups           | `5`                                   |
| Allocation        | `25565`                               |


Starta, godkänn Mojangs EULA i konsolen eller sätt `eula=true` i filhanteraren, starta igen. Servern ska nå `Done` innan du lägger in plugins.

`Unable to access jarfile server.jar` betyder att äggets installation inte laddade ner Paper. Panelens inbyggda ägg anropar ofta det nedlagda `api.papermc.io/v2`. Ladda ner 26.2 själv till volymen och starta sedan från panelen.

Volymen ligger i `/var/lib/pterodactyl/volumes/`, inte under `/var/www/pterodactyl`. Den syns med `sudo`.

```bash
sudo apt install -y jq
sudo ls -la /var/lib/pterodactyl/volumes/
```

En katalog per server, döpt till serverns UUID. Sätt `VOL` till den:

```bash
VOL=/var/lib/pterodactyl/volumes/<uuid>/
BUILD=$(curl -fsSL -A "engstrom-srv-mc01" https://fill.papermc.io/v3/projects/paper/versions/26.2 | jq -r '.builds[0]')
URL=$(curl -fsSL -A "engstrom-srv-mc01" "https://fill.papermc.io/v3/projects/paper/versions/26.2/builds/${BUILD}" | jq -r '.downloads["server:default"].url')
sudo curl -fL -A "engstrom-srv-mc01" -o "${VOL}server.jar" "$URL"
echo eula=true | sudo tee "${VOL}eula.txt"
sudo chown pterodactyl:pterodactyl "${VOL}server.jar" "${VOL}eula.txt"
ls -lh "${VOL}server.jar"
```

Saknas `/var/lib/pterodactyl/volumes` även med `sudo`, visa var containern är monterad:

```bash
sudo docker ps -a --format '{{.ID}} {{.Names}}'
sudo docker inspect <container-id> --format '{{range .Mounts}}{{.Source}} -> {{.Destination}}{{println}}{{end}}'
```

`server.jar` ska vara tiotals MB, inte några hundra byte.

### Containern kan inte slå upp DNS

`UnknownHostException: piston-data.mojang.com` betyder att Paper finns, men containern inte kan resolva Mojang. Filen den vill spara heter `cache/mojang_26.2.jar`. Hos Mojang heter samma fil `server.jar` under `piston-data.mojang.com`. Namnet är alltså rätt.

Ubuntu 24.04 pekar `/etc/resolv.conf` på `127.0.0.53`. Det fungerar på VM:en och inte inifrån Docker. Spelarinloggning (`online-mode`) använder samma DNS.

```bash
getent ahostsv4 piston-data.mojang.com
getent ahostsv6 piston-data.mojang.com
curl -4 -I --max-time 10 https://piston-data.mojang.com/
curl -6 -I --max-time 10 https://piston-data.mojang.com/
sudo docker run --rm --entrypoint getent ghcr.io/pterodactyl/yolks:java_25 hosts piston-data.mojang.com
```

VM och container ska få samma svar. Bara en IPv6-adress (`2603:1061:…`) betyder att namnet resolvas, men hämtningen går över IPv6. Fungerar `curl -4` och inte `curl -6` har VLAN 20 ingen fungerande IPv6-väg ut, trots att Unbound lämnar AAAA-svar.

Då lägger du in IPv4 i serverns startup-rad i panelen, **Startup**, före `-jar`:

```text
-Djava.net.preferIPv4Stack=true
```

Hela raden blir:

```text
java -Xms128M -XX:MaxRAMPercentage=95.0 -Dterminal.jline=false -Dterminal.ansi=true -Djava.net.preferIPv4Stack=true -jar server.jar
```

Kräver att `getent ahostsv4` visar en IPv4-adress. Utan A-record hjälper flaggan inte.

`docker run` och Wings använder inte samma DNS. Wings skickar med `1.1.1.1` om inget annat står i `config.yml`, och det vinner över `daemon.json`. OPNsense släpper DNS till sig själv (`192.168.20.1`), inte ut till Cloudflare. Då resolvar VM:en namnet och spelcontainern gör det inte. Java kastar `UnknownHostException` även med `preferIPv4Stack`.

Lägg till det här i `/etc/pterodactyl/config.yml`, under den befintliga texten:

```yaml
docker:
  network:
    dns:
      - 192.168.20.1
```

```bash
sudo systemctl restart wings
```

Starta servern igen. IPv4-flaggan i startup-raden ska vara kvar.

```bash
sudo mkdir -p /etc/docker
printf '%s\n' '{
  "dns": ["192.168.20.1"]
}' | sudo tee /etc/docker/daemon.json
sudo systemctl restart docker
sudo systemctl restart wings
```

Finns redan en `daemon.json`, lägg bara till nyckeln `dns`. Starta om servern i panelen efter att containerns `getent` svarar med en adress.

VM:en utan svar betyder att OPNsense (Unbound, eller en blocklista) inte resolvar namnet. Containern utan svar medan VM:en har en adress betyder att Docker fortfarande inte använder `192.168.20.1`. En brandvägg som släpper igenom DNS men stoppar hämtningen ger timeout, inte `UnknownHostException`.

Världsregler, plugins och zoner: [Minecraft survival](10-minecraft-survival-pvp-byhandel.md).

## 6. Backup

I panelen, på servern: **Backups → Create schedule**. Varje natt **04:30** `Europe/Stockholm`. Låt den ta med världen. Panelens backup ligger under `/var/lib/pterodactyl/backups/`.

Spegel till TrueNAS, inte som live-disk. Skapa en NFS-export som bara den här VM:en får montera, till exempel `/mnt/NFS/games/minecraft-backups`.

```bash
sudo apt install -y nfs-common
sudo mkdir -p /mnt/nas-mc-backups
echo '192.168.20.20:/mnt/NFS/games/minecraft-backups  /mnt/nas-mc-backups  nfs  defaults,_netdev  0  0' | sudo tee -a /etc/fstab
sudo mount -a
```

```cron
30 5 * * * rsync -a /var/lib/pterodactyl/backups/ /mnt/nas-mc-backups/
```

Utan `--delete`, så en misslyckad lokal rensning inte tömmer NAS:en.

Ta en backup **innan** du byter Paper-version eller plugin-version.

## 7. Loggar (valfritt)

UDP/TCP 514 mot [srv-syslog01](../book-02-plattform/10-central-loggning-srv-syslog01.md) om du vill ha VM:ens syslog i Loki. Spelkonsolen läses i panelen; den behöver inte in i Loki.

## Hälsokoll

```bash
systemctl is-active nginx php8.3-fpm mariadb redis-server pteroq wings docker
ss -tlpn | grep -E '443|8080|2022|25565'
curl -fsS https://srv-mc01.lab.engstrom.live/ -o /dev/null -w '%{http_code}\n'
```


| Check        | OK                                                          |
| ------------ | ----------------------------------------------------------- |
| Sex tjänster | `active`                                                    |
| Panel        | HTTP 200 eller 302 från LAN                                 |
| Nod          | grön i panelen                                              |
| Minecraft    | `Done` i konsolen, TCP 25565 lyssnar när servern är startad |




## Uppdatera panelen

Följ [upgrade-guiden](https://pterodactyl.io/panel/1.0/updating.html) den dagen du gör det. Kort version, från `/var/www/pterodactyl`:

```bash
sudo php artisan down
sudo curl -L https://github.com/pterodactyl/panel/releases/latest/download/panel.tar.gz | sudo tar -xzv
sudo composer install --no-dev --optimize-autoloader
sudo php artisan migrate --force
sudo php artisan view:clear && sudo php artisan config:clear
sudo chown -R www-data:www-data /var/www/pterodactyl
sudo php artisan up
sudo systemctl restart pteroq
```

Wings, separat:

```bash
sudo systemctl stop wings
sudo curl -L -o /usr/local/bin/wings \
  https://github.com/pterodactyl/wings/releases/latest/download/wings_linux_amd64
sudo chmod u+x /usr/local/bin/wings
sudo systemctl start wings
```

Gör inte båda mitt i en spelkväll. Backup först.