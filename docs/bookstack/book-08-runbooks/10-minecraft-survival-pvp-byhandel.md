# Minecraft survival — PvP och byhandel

En Paper-server för hushållet och vännerna. Panelen som kör den är [Pterodactyl på srv-mc01](09-pterodactyl-srv-mc01.md).

Spelarna bad om **PvP**, **survival** och **byhandel**. De tre fungerar i samma värld om de inte gäller överallt samtidigt. En öppen värld där man kan döda folk vid handelsboden slutar med döda bybor och en tom hall.

## Regler

```
Spawn + byhall          Claims (hem)              Vildmark
ingen PvP               ingen PvP                 PvP på
ingen mob-spawn         dina byggen är dina       mobs, creepers, räder
bybor kan inte dödas    bybor i claim skyddas     död = tappa saker
bara admin bygger       ägaren bygger             alla bygger
```

En värld, ett ägg, en port. Ingen ekonomi-plugin och ingen shop: handeln är vanilj-bybor.

| Inställning | Värde | Varför |
|-------------|-------|--------|
| Mjukvara | **Paper 26.2** | Klienten kan vara nyare. 26.3 är beta och strular med pluginen. Fältet i panelen byter inte jar-filen. |
| Svårighet | `hard` | Zombie-botning av bybor är pålitlig bara på hard (100 %). På normal är det 50 %, på easy 0 %. |
| `pvp` | `true` | PvP styrs sen av zoner, inte av att hela servern är av. |
| `gamemode` | `survival` | |
| `online-mode` | `true` | Riktiga konton. |
| `white-list` | `true` | `enforce-whitelist=true` |
| `spawn-protection` | `0` | WorldGuard tar över. Spawn-protection i vanilj blockerar bara ops och krockar med regionerna. |
| `view-distance` | `8` | Xeon E5. Höj inte för att "det ser finare ut". |
| `simulation-distance` | `6` | Samma skäl. Byhallen ska ligga inom simulation distance från spawn om den ska ticka när någon står i spawnen. |
| `max-players` | `10` | |
| Heap | 6 GB | Satt i panelen. Swap 0. |

`mobGriefing` ska vara **på**. Bond-bybor som skördar behöver det, och creepers i vildmarken hör till survival. Explosioner i spawn stängs av med en region-flagga, inte med en global gamerule.

## Plugins

Lägg jar-filerna i `plugins/` via panelens filhanterare eller SFTP (port 2022, bara från LAN). Starta om. Varje jar ska säga **26.2** på Hangar eller Modrinth. Gissa inte att en 1.21-build laddar.

| Plugin | Roll |
|--------|------|
| [LuckPerms](https://luckperms.net/) | Grupper |
| [EssentialsX](https://essentialsx.net/) | `/home`, `/tpa` |
| [EssentialsX Spawn](https://essentialsx.net/wiki/Module-Breakdown.html) | `/setspawn` och `/spawn`. Ingår inte i EssentialsX-jaren. |
| [Vault](https://github.com/MilkBowl/Vault) | Brygga som EssentialsX förväntar sig. Ingen ekonomi används. |
| [WorldEdit](https://enginehub.org/worldedit/) | Bara admin |
| [WorldGuard](https://enginehub.org/worldguard/) | Spawn, hall, arena |
| [GriefPrevention](https://griefprevention.com/) | Hem-claims och skydd av bybor |
| [CoreProtect](https://github.com/PlayPro/CoreProtect) | Vem bröt vad, och rollback |

CoreProtects stabila v24 listar inte alltid 26.2. Om jar-filen vägrar starta: kör utan den tills en 26.2-build finns, och luta dig mot panel-backupen. Kompilera inte ett slumpmässigt PR.

Hoppa över anticheat, ClearLagg, shop-plugins och mcMMO. En byhall på tio bybor behöver ingen lobotomy-plugin. Paper kan stänga av AI på bybor som står stilla; om `lobotomize` finns i `config/paper-world-defaults.yml`, låt den vara av tills en hall faktiskt drar ner TPS. Avstängd AI som inte fyller på trades är sämre än lite pathfinding.

## Behörigheter

I konsolen, efter att LuckPerms laddat. `DittNamn` är Minecraft-kontots namn, exakt som det står när du går in på servern. Det är inte förnamnet, mejlen eller användaren i Pterodactyl. Har kontot ett annat namn än `Mikael` fungerar inte `Mikael`.

Gå in en gång först, titta i konsolen på raden `UUID of player DittNamn is …`, och använd det namnet.

```text
lp creategroup spelare
lp creategroup admin
lp user DittNamn parent set admin

lp group spelare permission set essentials.spawn true
lp group spelare permission set essentials.home true
lp group spelare permission set essentials.sethome true
lp group spelare permission set essentials.sethome.multiple true
lp group spelare permission set essentials.tpa true
lp group spelare permission set essentials.tpaccept true
lp group spelare permission set essentials.tpdeny true
lp group spelare permission set essentials.msg true
lp group spelare permission set essentials.list true
lp group default parent add spelare

lp group admin permission set essentials.* true
lp group admin permission set worldedit.* true
lp group admin permission set worldguard.* true
lp group admin permission set coreprotect.* true
```

GriefPrevention ger vanliga spelare rätt att claima utan extra nod. Ge dem inte `griefprevention.*`.

EssentialsX-filen heter `plugins/Essentials/config.yml`. Spawn-delen kräver också jar-filen **EssentialsXSpawn**, inte bara EssentialsX.

Det finns ingen mening om nya och återvändande spelare. Det är två nycklar:

| Nyckel | Sätt till | Betyder |
|--------|-----------|---------|
| `spawn-on-join` | `false` | Återvändande spelare hamnar där de loggade ut. Står redan så. |
| `newbies` → `spawnpoint` | `none` | Första inloggningen använder spawn från `/setspawn`. |
| `newbies` → `kit` | `''` | Ingen start-kit. |
| `teleport-delay` | `5` | `/spawn` och `/tpa` väntar 5 sekunder. Rör de sig eller tar skada avbryts den. |
| `respawn-listener-priority` | `none` | Död följer vanilj: säng, annars världens spawn. |
| `sethome-multiple` → `default` | `2` | Två hem. |

GriefPrevention-filen heter `plugins/GriefPreventionData/config.yml`. Det mesta är redan rätt. Kontrollera de här, och ändra bara kommandoraden:

| Nyckel | Värde |
|--------|--------|
| `GriefPrevention.Claims.ProtectCreatures` | `true` |
| `GriefPrevention.PvP.RulesEnabledInWorld.world` | `true` |
| `GriefPrevention.PvP.ProtectFreshSpawns` | `true` |
| `GriefPrevention.PvP.PunishLogout` | `true` |
| `GriefPrevention.PvP.CombatTimeoutSeconds` | `15` |
| `GriefPrevention.PvP.ProtectPlayersInLandClaims.PlayerOwnedClaims` | `true` |
| `GriefPrevention.PvP.ProtectPlayersInLandClaims.AdministrativeClaims` | `true` |
| `GriefPrevention.PvP.ProtectPlayersInLandClaims.AdministrativeSubdivisions` | `true` |
| `GriefPrevention.PvP.BlockedSlashCommands` | `/home;/spawn;/tpa;/tpaccept;/tpahere` |

Starta om servern efter båda filerna. YAML är känslig för mellanslag: behåll indraget som redan står på raden, byt bara värdet.

## Zoner

Gör det här **innan** någon annan får whitelist. Marken behöver inte se ut på något särskilt sätt. Det som spelar roll är att du får plats med två rutor, och att de inte ligger i varandra.

| Plats | Storlek | Hur den ska se ut |
|-------|---------|-------------------|
| Spawn och byhall | ungefär **40×40** block | Mestadels platt. Slätt, strand eller en kulle du jämnat till räcker. En brant eller en flod rakt igenom är jobbig, för då bygger du golvet själv. |
| Arena | ungefär **24×24** block | Öppen plan yta, minst **10 block utanför** spawn-rutan. Ett staket runt så det syns var PvP börjar. Inget tak och inga bybor. |

40×40 är en vanlig tomt, inte en stad. Hallen själv kan vara ett rum på 15×9 block inne i den rutan.

1. Flyg tills du ser en sån yta. Ställ dig där dörren ska vara.

   LuckPerms-gruppen `admin` ger inte de här kommandona. `/setworldspawn` är vanilj och syns bara om du är **op**. `/setspawn` kommer från pluginen **EssentialsXSpawn**, en egen jar i `plugins/`. Utan den finns kommandot inte.

   I Pterodactyls konsol, med ditt Minecraft-namn:

   ```text
   op DittNamn
   ```

   Starta om efter att EssentialsXSpawn lagts in. Stå på platsen **i spelet**, inte i Pterodactyl-konsolen (den har ingen position), och kör:

   ```text
   /setworldspawn
   /setspawn
   ```

2. 40×40-rutan byggs inte. Den är bara skyddets yta, och den definieras senare med WorldEdit. Hallen är ett vanligt rum inne i den ytan.

   Du behöver inte samla sten. Du är op, så byt till creative, bygg, och byt tillbaka:

   ```text
   /gamemode creative
   ```

   Ta sten eller kullersten från creative-inventariet. Lägg ett golv, väggar och tak: ungefär 15 block långt, 9 brett och 4 högt. Lämna ett hål för dörren. Det räcker. Ingen inredning än.

   ```text
   /gamemode survival
   ```

   Arenan görs efter att spawn-regionen finns, och den får inte ligga i den. Spawn är ungefär 20 block ut från mitten, och arenan är 12 block ut från sin mitt. Mitten av arenan måste därför ligga minst **45 block** från spawn-mitten, annars överlappar rutorna och `pvp deny` från spawn vinner.

3. Definiera spawn-rutan där du satte `/setspawn`, inte genom att lägga block runt kanten. WorldEdit räknar 20 block åt varje håll, alltså ungefär 40×40:

   WorldEdit tar inte `~` i `//pos1`. Stå på mitten och låt kommandona räkna ut rutan. `//pos1` och `//pos2` utan koordinater sätter hörnen på blocket du står i, alltså ovanför marken.

   ```text
   //pos1
   //pos2
   //outset -h 20
   //expand vert
   /rg define spawn
   /rg flag spawn pvp deny
   /rg flag spawn mob-spawning deny
   /rg flag spawn mob-damage deny
   /rg flag spawn creeper-explosion deny
   /rg flag spawn tnt deny
   /rg flag spawn lighter deny
   /rg flag spawn interact allow
   /rg flag spawn use allow
   ```

   `//expand vert` drar rutan från bergets botten till himlen. Annars kan någon bygga ovanpå eller gräva under skyddet. En region utan medlemmar stoppar bygg för alla utom ägare och admin. `interact allow` och `use allow` gör att högerklick mot bybor fortfarande fungerar.

   Arenan, när spawn redan är definierad:

   1. Stå på spawn-mitten. Gå minst 45 block åt ett håll, till en plan fläck. Kör `/rg info`. Står `spawn` med i listan är du fortfarande inne i den. Gå längre ut tills den inte nämns.
   2. Stå på marken i mitten och töm träd och allt annat från fotnivå och uppåt. Blocket under fötterna ligger på `~-1` och rörs inte. Blev det fel: `//undo`.

   ```text
   //pos1
   //pos2
   //outset -h 16
   //expand 40 up
   //set air
   ```

   3. `/gamemode creative`. Bygg ett staket, ungefär 24×24, runt den tömda ytan. Inget tak, inga bybor. `/gamemode survival`.
   4. Stå i mitten av staketet och definiera regionen:

   ```text
   //pos1
   //pos2
   //outset -h 12
   //expand vert
   /rg define arena
   /rg flag arena pvp allow
   /rg flag arena mob-spawning deny
   /rg flag arena creeper-explosion deny
   ```

   Sätt inte `build deny`. En region utan medlemmar stoppar redan bygg för alla utom ägaren, och det är du eftersom du körde `/rg define`. `build` är en överstyrningsflagga. Sätts den ersätter den det skyddet helt, och WorldGuard varnar för just det. Har du redan satt den, ta bort den utan att ange ett värde:

   ```text
   /rg flag arena build
   ```

   5. Kontrollera. `//size` ska vara ungefär `25 x … x 25`. Gå till staketet som vetter mot spawn och kör `/rg info`. Där ska `arena` synas och `spawn` inte. Syns båda överlappar de. Ta bort med `/rg remove arena` och gör om längre bort.

   Lägg ingen GriefPrevention-adminclaim här. Den stänger av PvP. `pvp allow` är det som låter spelare skada varandra. `mob-damage deny` kan sättas också, den stoppar bara mobbar och rör inte PvP.

4. GriefPrevention-adminclaim över **samma** 40×40 som spawn och hallen. Inte över arenan. En adminclaim där stänger av PvP, och då är arenan inte en arena.

   ```text
   /adminclaims
   ```

   Gyllene spade: vänsterklick i ena hörnet, högerklick i det motsatta. `/adminclaims` en gång till stänger av läget. Spelare kan gå in och handla. De kan inte riva eller slå bybor. WorldGuard står för PvP och att mobs inte spawnar.

5. Testa med ett andra konto som **inte** är admin:

| Test | Förväntat |
|------|-----------|
| Slå en bybo i hallen | inget händer |
| Högerklicka och handla | fönstret öppnas |
| Bryta en vägg i spawn | blockeras |
| Slå varandra i arenan | skada går fram |
| `/spawn` mitt i strid | blockeras |
| Dö i vildmarken | saker droppar |
| Claima en bit mark, låta det andra kontot bryta där | blockeras |

## Byhallen

En cell är ett skåp av sten med en bybo i. Arbetsblocket är blocket som ger bybon ett yrke. En bybo, ett arbetsblock, och stenväggar så att grannen inte kan ta samma block.

Bygg en cell så här, inne i hallen. Innerytan är 1 block bred, 2 block djup och 2 block hög.

1. Golv, bakvägg, sidoväggar och tak av sten eller kullersten. Inte staket, och **ingen trädörr**. Zombier slår sönder trädörrar. Glas går bra om du vill se bybon.
2. Bybon ska stå i det bakre blocket. Arbetsblocket står på golvet i det främre blocket, precis framför bybon.
3. Sätt en fallucka i öppningen, framför bybons huvud, så att bybon inte kan gå ut och du fortfarande kan högerklicka på den. Spelaren står i korridoren och handlar genom glipan.

`mob-spawning deny` stoppar nya mobbar inne i rutan. De som redan finns utanför kan följa efter in. `mob-damage deny` gör att deras slag och pilar inte skadar så länge målet står i rutan. Facklor är extra, inte ersättning. En järndörr i hallöppningen håller dem ute. Zombier slår inte sönder den. Stenknapp på utsidan, tryckplatta på insidan. Mobbar kan inte trycka på knappen, så de kommer inte in. Plattan öppnar dörren när någon går ut. En tryckplatta på utsidan släpper in dem, för både sten- och träplattor reagerar på mobbar.

Arbetsblocket bestämmer yrket. Lägg bara det blocket i cellen. En tunna, en kompost eller en extra läktare i samma rum gör att bybon tar fel jobb.

| Yrke | Arbetsblock |
| --- | --- |
| Bibliotekarie | läktare |
| Präst | bryggställ |
| Verktygssmed | smidesbord |
| Vapensmed | slipsten |
| Rustningssmed | masugn |
| Bågskytt | pilmakarbänk |
| Fiskare | tunna |
| Bonde | kompost |

`/summon villager` fungerar inte inne i spawn. Regionen har `mob-spawning deny`, och den flaggan stoppar även kommando-spawn. Utanför rutan syns bybon. Inuti försvinner den direkt, även om chatten säger att den skapades.

Flaggan tar inte bort bybor som redan finns. Stäng av den, skapa bybon i cellen, och slå på den igen:

```text
/rg flag spawn mob-spawning allow
/summon villager
/rg flag spawn mob-spawning deny
```

Stå i det bakre blocket när du kör `/summon`. Bybon hamnar i samma block som du. Kliv ut så att du ser den, och sätt tillbaka `deny` direkt efteråt. Gör det på dagen, så hinner inga zombier spawn innan flaggan är tillbaka.

Den bybo som redan står utanför spawn kan dras in utan att röra flaggan. Stå i cellen och kör vaniljkommandot. Essentials tar över `/tp` och förstår inte `@s`.

```text
/minecraft:tp @e[type=villager,distance=..40,limit=1,sort=nearest] @s
```

Kliv sedan ur blocket. Brun rock och inget yrke är rätt. Grön rock och ett vanligt ansikte är en nitwit och kan aldrig ta ett jobb. Grön hud och ett stön är en zombie eller en zombiebybo. `mob-spawning deny` hindrar dem inte från att gå in utifrån. Stå intill den som ska bort. Kommandot tar bara närmaste inom två block:

```text
/minecraft:kill @e[type=villager,distance=..2,limit=1,sort=nearest]
/minecraft:kill @e[type=zombie_villager,distance=..2,limit=1,sort=nearest]
/minecraft:kill @e[type=zombie,distance=..2,limit=1,sort=nearest]
```

Nitwits ersätts med en ny bybo medan `mob-spawning` är `allow`. Zombies ska bara bort. En dörr eller fallucka i hallen stoppar nästa som vandrar in.

Sätt därefter arbetsblocket på det främre golvblocket. Gröna partiklar och ny rock betyder att bybon tagit jobbet.

Innan någon handlar får du bryta arbetsblocket och sätta dit det igen. Varje gång byter bybon utbud. När utbudet är bra, handla **en** gång. Då låses yrket. Efter det ska blocket stå kvar, för priserna fylls bara på om bybon når sitt arbetsblock.

Vill ni ha de stora rabatterna görs botningen på **hard**. En zombie smittar bybon, och spelaren botar med weakness-dryck och gyllene äpple. Gör det i hallen, inte i vildmarken.

Räls och redstone i hall-guider är till för survival, där `/summon` inte finns. En avelsstation spottar ut bybor, en vagn på räls lägger en i varje cell, och en kolv bryter läktaren tills utbudet är rätt. Det behövs inte här.

En namnskylt är föremålet, inte en skylt på väggen. Döp den i ett städ och högerklicka på bybon. Namnet hänger över huvudet, så det syns vilken som är vilken efter en omstart. En vanlig skylt ovanför arbetsblocket är till för spelarna, om ni vill skriva vad den säljer.

Låt spelarna ha egna bybor **inne i sina claims**. GriefPrevention skyddar varelser där. Vildmarkens byar är lovligt byte — det är en del av PvP/survival, hallen är det inte.

## Första kvällen

1. Backup i panelen.
2. `whitelist on` och `whitelist add` för varje spelare.
3. Skriv reglerna i en skylt vid spawn, tre rader: hallen är fredad, hem är fredade, vildmarken är PvP.
4. Spela en kvart själv: handla, dö i vildmarken, döda inga hall-bybor.
5. Öppna port 25565 enligt [Pterodactyl-runbooken](09-pterodactyl-srv-mc01.md).

DNS för vänner utifrån, om du port-forwardar: ett namn mot hemmets publika IP, **grå moln** i Cloudflare. Proxat namn når inte en Minecraft-server.
