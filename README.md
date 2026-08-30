# VEKTOR Installer — Windows x64

Graficzny instalator VEKTORA z niezależną Ollamą w Dockerze. Pobierz `VEKTOR-Setup-x64.exe` z [Releases](https://github.com/Gartom91/VEKTOR-Installer/releases/latest).

## Wymagania i instalacja

Windows 10 22H2 / Windows 11 **x64**, minimum 8 GB RAM (zalecane 16 GB+), wirtualizacja BIOS/UEFI i WSL2. Nie obsługuje Windows Server, x86 ani ARM64. Internet oraz kilkanaście GB wolnego miejsca są potrzebne na Docker, obrazy i modele. WSL może wymagać UAC i restartu; po restarcie ponów instalator, wskazując ten sam folder.

1. Uruchom EXE, wybierz pusty folder instalacji albo folder wcześniejszej instalacji.
2. Przeczytaj i zaakceptuj warunki Docker Desktop. Niektóre zastosowania wymagają płatnej licencji producenta.
3. Opcjonalnie włącz dostęp agenta do Windows i autostart. Moduł diagnostyki i aktualizacji uruchamia się zawsze ze skrótu. Instalator nie włącza pełnego dostępu ani nie zatwierdza automatycznie działań agenta.
4. Poczekaj na obrazy i modele. Użyj skrótu **VEKTOR** na pulpicie.
5. Dla cloud kliknij **Zaloguj do Ollama cloud** i otwórz pokazany adres autoryzacji. Konto i limity są Twoje; instalator nie zawiera tokenów autora.
6. Obrazy OpenAI: w aplikacji otwórz **Ustawienia → Generowanie obrazów · Codex / ChatGPT**, zaloguj się kodem urządzenia na stronie OpenAI i wybierz dostawcę Codex. Logowanie jest oddzielne od Ollamy i od aplikacji Codex na komputerze. Dotyczy wybranej przestrzeni projektu. Wymaga dostępności obrazów i limitu na Twoim koncie; nie działa w trybie tylko lokalnym.

Od 1.1 prompty kolejkuje się bezpośrednio w bieżącym chacie. Diagnostyka znajduje się w ustawieniach, a **Bez projektu** zawiera dotychczasowe nieprzypisane rozmowy. Każdy projekt wyświetla wyłącznie swoje chaty.

Program i modele lokalne działają bez instalowania Pythona, Node.js czy .NET na komputerze użytkownika. EXE zawiera runtime .NET oraz skompilowany moduł hosta. Docker i obrazy są pobierane podczas instalacji, więc to instalator **online**, nie offline.

## Powtarzalność i sprzęt

VEKTOR i Ollama są dwoma kontenerami jednego projektu Compose `vektor-desktop`, przypiętymi po SHA256 w `payload/release.json`. To te same funkcje aplikacji, ale nie gwarancja identycznej szybkości ani odpowiedzi generatywnych na różnym sprzęcie.

- NVIDIA jest najpierw sprawdzana w kontenerze; brak działającego GPU powoduje jawny fallback do CPU.
- Dobór lokalnego modelu: 8 GB RAM bez GPU → qwen3:1.7b; 16 GB+ RAM / GPU 4 GB → qwen3:4b; GPU 6 GB+ → qwen3:8b. Kontekst 4096–16384 zależnie od VRAM.
- Lokalny Vision: gemma3:4b. Tylko jeden model lokalny załadowany jednocześnie, lokalny swarm wyłączony.
- Cloud: domyślny model główny **glm-5.3:cloud**, specjalista Vision **glm-5.3-flash:cloud**. Wymagają własnego logowania i dostępności w Ollamie. Obie role można zmienić w ustawieniach aplikacji.
- Obraz jest analizowany pod kątem pytania użytkownika; model główny dostaje walidowany raport OCR/obserwacji/niepewności i może dopytać o wycinek oryginału. Raporty, oryginały i linki pobierania pozostają w chacie. Domyślnie dwie dodatkowe rundy, limit konfigurowalny 0–8.
- VEKTOR ogranicza łącznie wywołania modeli Ollama cloud do trzech naraz. W trybie lokalnym pomija cloud i Swarm; modele lokalne są uruchamiane pojedynczo. Limity konta zużywane przez inne aplikacje pozostają niezależne.
- Sterowniki GPU, BIOS, proxy firmowe i polityki zabezpieczeń pozostają zależne od komputera. Instalator nie wyłącza ochrony Windows ani zapory.

## Dane, aktualizacja, usuwanie

Rozmowy, projekty, pamięć, konfiguracja i historia plików: wolumin `vektor-desktop_agent-data`. Modele i logowanie Ollamy: `vektor-desktop_ollama-data`. Pliki użytkownika: `workspace` w wybranym folderze. Aktualizacja zachowuje te zasoby i przed wymianą działającego kontenera zapisuje kopię głównej bazy SQLite w `/app/data/backups`.

Od 1.6.0 **Ustawienia → Aktualizacje VEKTORA** oferują automatyczne sprawdzanie stabilnych wydań (domyślnie co 6 godzin) i instalowanie po bezczynności (domyślnie 5 minut). Obie opcje można wyłączyć. Zadania, kolejka i zgody we wszystkich projektach opóźniają restart; można pominąć wydanie albo potwierdzić ręczną instalację.

Automatyczny updater zapisuje kopię **wszystkich** baz i plików woluminu danych w `/app/data/backups/updates/`, weryfikuje SHA256 manifestu GitHub, przypięty obraz i zachowanie danych. Błąd kontroli uruchamia rollback, a nie kolejne próby wadliwego wydania. Po przerwaniu pracy pozostaje dziennik w `data/updater/`. Jeśli wyłączony Docker, wygasła blokada lub uszkodzony dysk uniemożliwiają bezpieczny rollback, updater zatrzymuje się z informacją diagnostyczną. Kopie pozostają do ręcznego przeglądu i zajmują miejsce.

Zmienia się tylko kontener `agent`, bez wymiany Dockera, Ollamy i pobranych modeli. Zewnętrzny workspace pozostaje nietknięty. Moduł Windows wymaga nowszego instalatora przy zmianie protokołu. **Sama aktualizacja nie daje agentowi dostępu do pulpitu/plików ani praw administratora.** Wymagany standardowy nazwany wolumin danych, bez niestandardowych plików Compose/dowiązań. Wydania prerelease i samo przesunięcie Docker `latest` nie uruchamiają aktualizacji.

Użyj nowszego instalatora z tym samym folderem. Ustawienia istniejącej instalacji mają pierwszeństwo przed domyślnymi opcjami kreatora. Nie odinstalowuj Docker Desktop i nie używaj `docker system prune --volumes`, jeśli chcesz zachować dane.

`Uninstall-VEKTOR.ps1` zatrzymuje kontenery i usuwa własny skrót/autostart, zachowując dane, modele i pliki. Opcja `-RemoveData` dodatkowo usuwa **nieodwracalnie** woluminy tego projektu; pliki workspace i instalatora pozostają. To świadoma operacja administracyjna, nie domyślne zachowanie.

Moduł Windows działa wyłącznie na loopback, ma osobny losowy token chroniony ACL użytkownika, a eskalacja Windows wymaga UAC dla konkretnej akcji. Projekty izolują kontekst agenta, ale nie są sandboxem dla jawnie dozwolonych poleceń systemowych.

## Weryfikacja

`SHA256SUMS.txt` pozwala sprawdzić pobrany EXE: `Get-FileHash .\VEKTOR-Setup-x64.exe -Algorithm SHA256`. Wydanie nie ma komercyjnego podpisu Authenticode; Windows może pokazać ostrzeżenie nieznanego wydawcy. Nie wyłączaj SmartScreen. Podpis Docker Desktop jest weryfikowany przed uruchomieniem zależności.

Testy automatyczne obejmują składnię PowerShell 5.1, profile RAM/VRAM, wykrywanie konfliktów portów, kody procesów i przypięcie obrazów. Test instalacji na komputerze z działającym Dockerem nie zastępuje macierzy czystych maszyn Windows, różnych GPU i polityk firmowych. Szczegóły bieżącej walidacji są w notatkach wydania.

## Budowanie i wydania

Wymagane .NET 10 SDK i Python 3.12 wyłącznie na komputerze budującym.

```powershell
./test-installer.ps1
./build.ps1 -Python python
./test-payload.ps1
```

Tag `v*` uruchamia GitHub Actions, buduje instalator, wykonuje testy, zapisuje sumy SHA256 i publikuje EXE oraz `release.json` w GitHub Releases. Aktualizacja wersji aplikacji wymaga wcześniejszej publikacji obrazu i zmiany przypiętego digestu w `payload/release.json`; manifest zawiera `updateProtocol: 1`. Repozytoria GitHub i Docker Hub są granicą zaufania wydawcy — SHA256 nie zastępuje niezależnego podpisu kryptograficznego.

Źródła wymagań: [Docker Windows](https://docs.docker.com/desktop/setup/install/windows-install/), [WSL](https://learn.microsoft.com/windows/wsl/install), [Ollama Docker](https://docs.ollama.com/docker), [Ollama cloud](https://docs.ollama.com/cloud).
