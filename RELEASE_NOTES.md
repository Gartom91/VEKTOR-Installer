# VEKTOR Windows 1.3.1

## Interfejs 1.3.1
- „Od VEKTORA” jako centrum powiadomień w osobnym, przestronnym oknie. Kompaktowy przycisk z dzwonkiem nie rozwija listy wewnątrz nawigacji.
- Filtry wiadomości, odrębna karta sugestii, czytelne podglądy bez surowego Markdown, rozwijana pełna treść i przejście do rozmowy.
- Przewijana zawartość, stały nagłówek, responsywny układ i zamykanie Escape z powrotem fokusu.
- 24 testy UI PASS, TypeScript/Vite build PASS. Bez zmian w backendzie personalizacji.

## Personalizacja 1.3
- Opcjonalna pamięć krótkich deklaracji i preferencji z nowych interakcji; profile i liczniki rodzajów zadań izolowane między projektami. Bez śledzenia całego komputera, bez trenowania modelu. Usuwanie profilu oraz wyłącznik używania automatycznej pamięci.
- Regułowe propozycje kolejnego kroku i wzorce przejść między zadaniami; zawsze wymagają decyzji użytkownika, nie wykonują narzędzi.
- Spontaniczne propozycje jako trwałe osobne rozmowy: losowy odstęp, godziny ciszy, dzienny limit, brak zaczepek podczas aktywnych zadań.
- Skrzynka „Od VEKTORA” i opcjonalne powiadomienia pulpitu z fragmentem odpowiedzi i otwarciem rozmowy. Wymagana zgoda przeglądarki i otwarte (także zminimalizowane) okno aplikacji. Bez okna pozostaje trwała skrzynka. Nie deklarujemy testu fizycznego dostarczenia toastu Windows.
- Domyślnie nowe instalacje mają uczenie, zaczepki i powiadomienia wyłączone. Włącz je w Ustawienia → Pamięć o Tobie i proaktywność. Pamięć wykorzystana w kontekście modelu cloud jest przesyłana do tego dostawcy.
- Testy UI: 23 PASS; testy backendu i rzeczywiste przywołanie zapisanej preferencji w nowej rozmowie z GLM.

## Poprawka 1.2.1
- Wbudowana kontrola integralności obrazów, rzeczywistych wymiarów i SHA256; kontrola składni Python/JSON bez wykonywania plików.
- Rozróżnienie nierozwiązanych błędów i naprawionej próby z zachowaniem oryginalnego błędu w historii. Niepowiązany sukces nie usuwa wcześniejszej porażki.
- Agent podejmuje do dwóch dodatkowych prób przeglądu weryfikacji; przy nierozwiązanym błędzie zwraca wynik częściowy zamiast deklaracji sukcesu.
- Ponowna kontrola artefaktów w panelu weryfikacji; rzeczywiste wymiary obrazów także w rezultacie generatora.
- Walidacja: 114 testów backendu, 20 testów UI, build produkcyjny i ponowna kontrola rzeczywistej rozmowy z obrazem w Dockerze. Kontrola techniczna nie zastępuje oceny artystycznej ani testu funkcjonalnego programu.

## Zmiany 1.2
- Eksplorator projektu: drzewo folderów, podgląd kodu i obrazów, pobieranie oraz dodawanie/przeciąganie plików do chatu.
- Centrum wyników z filtrami, miniaturami i przejściem do rozmowy źródłowej.
- Podgląd Przed/Po przed zatwierdzeniem write_file, append_file i copy_file. Konflikt z późniejszą zmianą pliku blokuje zapis. Pełny dostęp pomija zgody; shell/Python/MCP nie są przechwytywane przez ten mechanizm.
- Trwała kolejka per chat: edycja prompta, przeciąganie/strzałki kolejności, pauza, wznowienie i anulowanie. Osobny status oczekiwania.
- Kopia ZIP instrukcji, rozmów, pamięci, wiedzy i plików; import do nowego projektu. Limit 100 MB. Bez logowań, konfiguracji MCP, aktywnych zgód/zadań, automatyzacji i prywatnego magazynu załączników. Treści projektu mogą zawierać prywatne informacje — ostrzeżenie przed eksportem.
- Konfigurowalny czas zadania (0 = bez limitu), liczba wywołań i powtórzeń, tryb tylko odczyt niezależny od pełnego dostępu.
- Źródła z datą dostępu w weryfikacji: odróżnienie odczytanej strony od znalezionego linku. To ślad dowodowy, nie gwarancja prawdziwości odpowiedzi.
- Duży popup zarządzania projektami z osobnym edytorem i stale widocznym paskiem akcji.
- Walidacja aplikacji: 106 testów backendu, 19 testów UI, build produkcyjny, rzeczywisty GLM z akceptacją pliku, edytowaną kolejką po odświeżeniu oraz eksport/import w Dockerze.

## Zmiany 1.1
- Kolejka promptów w poszczególnych chatach; oczekujące prompty nie trafiają przedwcześnie do kontekstu modelu.
- Diagnostyka w ustawieniach, przestronne zarządzanie projektami, „Bez projektu” i filtrowanie chatów.
- Poprawiony układ karty i przełącznika pełnego dostępu.
- Logowanie Codex / ChatGPT kodem urządzenia i natywne generowanie GPT Image 2 przez Codex App Server. CLI w obrazie, prywatne logowanie dla przestrzeni projektu, bez kopiowania tokenów autora.
- Walidacja: 90 testów backendu, 13 testów UI, rzeczywista kolejka dwóch promptów w tym samym chacie. App Server zwrócił kod logowania. Generowanie obrazu z prywatnego konta wymaga jego autoryzacji i nie jest deklarowane jako potwierdzone tym wydaniem.

Dokumentacja: https://learn.chatgpt.com/docs/app-server oraz https://learn.chatgpt.com/docs/image-generation.

## Podstawa instalatora (walidacja 1.0)

Pierwszy instalator online Windows 10/11 x64: Docker Desktop/WSL2, przypięte obrazy VEKTORA i Ollamy, automatyczny profil sprzętu, lokalny fallback, opcjonalny moduł Windows, skrót i autostart.

Aplikacja zawiera historię plików, weryfikację techniczną rezultatów, plan z edycją przyszłych kroków, doprecyzowanie podczas pracy, trwałą kolejkę, diagnostykę i oddzielne projekty.

Zachowanie danych przy aktualizacji, kontrola podpisu Docker Desktop, losowy lokalny token brokera. Brak zapisanych rozmów lub tokenów autora w paczce.

Wydanie nie jest podpisane Authenticode. Sprawdź SHA256SUMS.txt. Wymagane własne konto Ollama do cloud. Nie obsługuje ARM64/Windows Server. Nie gwarantuje działania na każdej konfiguracji BIOS/sterowników/polityk firmowych. Instalację WSL po restarcie należy ponowić.

Weryfikacja: 82 testy backendu i 10 testów interfejsu aplikacji. Test instalacji i ponownej naprawy na oddzielnych woluminach Docker: healthcheck obu kontenerów, NVIDIA, moduł Windows i kopia bazy. Testy instalatora obejmują składnię PowerShell 5.1, dobór sprzętu, zajęte porty, przypięte obrazy, kody procesów i prywatny ACL. Pełny przebieg instalowania WSL/Dockera na czystym komputerze nie był testowany fizycznie.
