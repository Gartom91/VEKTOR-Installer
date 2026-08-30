# VEKTOR Installer — Windows x64

Graficzny instalator VEKTORA z niezależną Ollamą w Dockerze. Pobierz `VEKTOR-Setup-x64.exe` z [Releases](https://github.com/Gartom91/VEKTOR-Installer/releases/latest).

## Wymagania i instalacja

Windows 10 22H2 / Windows 11 **x64**, minimum 8 GB RAM (zalecane 16 GB+), wirtualizacja BIOS/UEFI i WSL2. Nie obsługuje Windows Server, x86 ani ARM64. Internet oraz kilkanaście GB wolnego miejsca są potrzebne na Docker, obrazy i modele. WSL może wymagać UAC i restartu; po restarcie ponów instalator, wskazując ten sam folder.

1. Uruchom EXE, wybierz pusty folder instalacji albo folder wcześniejszej instalacji.
2. Przeczytaj i zaakceptuj warunki Docker Desktop. Niektóre zastosowania wymagają płatnej licencji producenta.
3. Opcjonalnie włącz moduł Windows i autostart. Instalator nie włącza pełnego dostępu ani nie zatwierdza automatycznie działań agenta.
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
- Cloud: glm-5.3-flash:cloud i mocniejszy glm-5.3:cloud; wymagają własnego logowania i dostępności w Ollamie.
- Sterowniki GPU, BIOS, proxy firmowe i polityki zabezpieczeń pozostają zależne od komputera. Instalator nie wyłącza ochrony Windows ani zapory.

## Dane, aktualizacja, usuwanie

Rozmowy, projekty, pamięć, konfiguracja i historia plików: wolumin `vektor-desktop_agent-data`. Modele i logowanie Ollamy: `vektor-desktop_ollama-data`. Pliki użytkownika: `workspace` w wybranym folderze. Aktualizacja zachowuje te zasoby i przed wymianą działającego kontenera zapisuje kopię głównej bazy SQLite w `/app/data/backups`.

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
```

Tag `v*` uruchamia GitHub Actions, buduje instalator, wykonuje testy, zapisuje sumę SHA256 i publikuje artefakty w GitHub Releases. Aktualizacja wersji aplikacji wymaga wcześniejszej publikacji obrazu i zmiany przypiętego digestu w `payload/release.json`.

Źródła wymagań: [Docker Windows](https://docs.docker.com/desktop/setup/install/windows-install/), [WSL](https://learn.microsoft.com/windows/wsl/install), [Ollama Docker](https://docs.ollama.com/docker), [Ollama cloud](https://docs.ollama.com/cloud).
