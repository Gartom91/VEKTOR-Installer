# VEKTOR Windows 1.0.0

Pierwszy instalator online Windows 10/11 x64: Docker Desktop/WSL2, przypięte obrazy VEKTORA i Ollamy, automatyczny profil sprzętu, lokalny fallback, opcjonalny moduł Windows, skrót i autostart.

Aplikacja zawiera historię plików, weryfikację techniczną rezultatów, plan z edycją przyszłych kroków, doprecyzowanie podczas pracy, trwałą kolejkę, diagnostykę i oddzielne projekty.

Zachowanie danych przy aktualizacji, kontrola podpisu Docker Desktop, losowy lokalny token brokera. Brak zapisanych rozmów lub tokenów autora w paczce.

Wydanie nie jest podpisane Authenticode. Sprawdź SHA256SUMS.txt. Wymagane własne konto Ollama do cloud. Nie obsługuje ARM64/Windows Server. Nie gwarantuje działania na każdej konfiguracji BIOS/sterowników/polityk firmowych. Instalację WSL po restarcie należy ponowić.

Weryfikacja: 82 testy backendu i 10 testów interfejsu aplikacji. Test instalacji i ponownej naprawy na oddzielnych woluminach Docker: healthcheck obu kontenerów, NVIDIA, moduł Windows i kopia bazy. Testy instalatora obejmują składnię PowerShell 5.1, dobór sprzętu, zajęte porty, przypięte obrazy, kody procesów i prywatny ACL. Pełny przebieg instalowania WSL/Dockera na czystym komputerze nie był testowany fizycznie.
