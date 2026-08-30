# VEKTOR Windows 1.5.0

## Hybrydowy model główny i Vision

- Domyślny model główny `glm-5.3:cloud`, specjalista obrazu `glm-5.3-flash:cloud`; edytowalne role i potwierdzane możliwości modeli w ustawieniach.
- Analiza obrazu dostosowana do zadania. Walidowany raport rozdziela OCR, obserwacje, lokalizacje, niepewności i alternatywy. Oryginały zachowane; model może dopytać o szczegół lub wycinek. Domyślnie dwie dodatkowe rundy, ustawienie 0–8.
- Czytelne, rozwijane raporty w chronologii chatu, osobna odpowiedź końcowa, otwieranie i pobieranie źródeł. Cache powiązany z oryginałem, pytaniem i modelem.
- Wspólny limit trzech żądań Ollama cloud. Tryb lokalny bez inferencji cloud i Swarmu, jeden załadowany model naraz. Usunięto fałszywe przełączanie na local przy błędach wewnętrznych i autoryzacji.
- Streaming publicznej odpowiedzi z zachowaniem historii; licznik działa również przy częstych pakietach bez tekstu. Po odświeżeniu zadanie trwa dalej; zatrzymanie zwalnia strumień i natychmiast aktualizuje plan.

## Niezawodność pracy i MCP

- Naprawiono interpretację „dodasz sobie serwer MCP Context7”, „Ponów” i „Przystąp do realizacji planu”. Kontynuacja wymaga wcześniejszego zakresu zgody; pytania i wycofanie zgody nadal blokują zmiany także przy pełnym dostępie.
- Powtórzone odczyty powodują wykorzystanie poprzedniego wyniku i przeplanowanie, nie blokadę całej odpowiedzi. Nieistotne błędy źródeł nie zastępują uzyskanych rezultatów komunikatem niepowodzenia.
- MCP: precheck przed dodaniem, rzeczywisty handshake i wykonywanie narzędzi, zgodność z SDK 2.x oraz trwałe metadane. Context7 przetestowano od konfiguracji po zapytania o dokumentację Python. Instalator nie dodaje go bez polecenia użytkownika.
- Narzędzia pamięci i wiedzy związane z bieżącym projektem. Niejednoznaczne „znajdź sobie plik z pamięcią” wywołuje doprecyzowanie zamiast poszukiwania zrzutów RAM.
- Poprawki układu: miejsce i suwak historii rozmów także w niskim oknie, zawijanie długich nazw, wyrównane kontrolki ustawień. Pozostają wcześniejsze funkcje Office, artefaktów, powiadomień i graficznych diagramów.

## Weryfikacja i instalacja

- Backend Windows: **216 PASS / 1 SKIP** (render LibreOffice sprawdzany w Dockerze). Backend Linux w wydawanym obrazie: **200 PASS / 17 SKIP** (integracje Windows sprawdzane na Windowsie). UI: **48 PASS**, produkcyjny build poprawny.
- Rzeczywiste próby: dwie ścieżki cloud na syntetycznej tabeli, doprecyzowanie wycinka, cache po otwarciu nowej sesji, lokalny Vision bez cloud, Context7, upload i rozłączenie SSE, odświeżenie podczas streamingu, zatrzymanie oraz nowy chat.
- Obraz `1.5.0` i `latest` sprawdzone po publikacji; instalator przypina dokładny SHA256, zachowuje lokalne dane i logowania. Domyślny Flash migruje jednorazowo do mocniejszego modelu; niestandardowe wybory pozostają.
- Installer CI sprawdza PowerShell 5.1, profile sprzętowe, przypięcia obrazów, nowe role modeli, zgodność wersji i zawartość EXE oraz faktyczny start spakowanego modułu Windows, blokadę żądań bez tokenu i endpoint metryk. Te same testy przeszły lokalnie. Instalator nadal jest online, Windows x64, bez komercyjnego podpisu Authenticode. Nie deklarujemy testów na wszystkich fizycznych komputerach ani gwarancji bezbłędności modeli.

## Wcześniejsze wydania

## VEKTOR Office 1.4.0
- Tworzenie i edycja Word DOCX, Excel XLSX, PowerPoint PPTX i PDF przez pakiet `office-suite`.
- Przeliczanie formuł Excela, natywne wykresy, notatki prelegenta PowerPoint, firmowe kolory/logo i szablony.
- Lokalny render LibreOffice/Poppler i OCR polski/angielski w obrazie Docker. Nie wymaga instalacji Microsoft Office.
- Graficzny podgląd stron/slajdów przy artefakcie w chacie i bibliotece, pobieranie oraz przygotowanie prośby o poprawki.
- Rozdzielone wyniki kontroli struktury, renderowania i rzeczywistego przeglądu vision. Brak vision nie jest przedstawiany jako pozytywna ocena.
- PDF: eksport, łączenie, wybór stron, wypełnianie istniejących formularzy. Oryginały są zachowywane, zapis korzysta z historii wersji i ochrony przed konfliktami.
- Kontrole bezpieczeństwa: ścieżki projektu, limity wielkości, blokowanie makr/ActiveX i zewnętrznych powiązań. Lokalne renderowanie działa także bez sieci.
- Limity: 10 MB/plik, 100 stron renderu, 24 strony podglądu, 6 stron przeglądu vision, 10 stron OCR; brak gwarancji pełnej zgodności zaawansowanych szablonów Microsoft Office.
- Naprawa kart artefaktów po ręcznej zgodzie oraz kolejności FIFO przy identycznych znacznikach czasu promptów.
- 146 testów backendu i 32 testy UI PASS; render/formuły/OCR dodatkowo sprawdzone w kontenerze offline. Test chatu utworzył PPTX po ręcznej zgodzie i wykonał rzeczywisty przegląd vision.

## Ikona VEKTORA 1.3.5
- Wybrany turkusowy znak V ze strzałką w interfejsie, faviconie oraz manifeście aplikacji.
- Wielorozmiarowa ikona Windows (16–256 px) dla skrótu na pulpicie i instalatora. Instalacja zachowuje ikonę we własnym katalogu.
- Przezroczyste PNG, wariant kafelkowy dla Windows i osobny znak dla małych rozmiarów.
- 29 testów UI PASS, build PASS, zasoby serwowane z poprawnymi typami MIME.

## Korekty ustawień i połączenia 1.3.4
- Prawa kolumna nie rozciąga już formularza modelu. Odstęp do następnej sekcji pozostaje 24 px; dłuższa zawartość po prawej przewija się niezależnie, a na wąskim ekranie układa pod formularzem.
- Podgląd profilu pracy jest rozwijany.
- Chwilowa utrata połączenia Codex nie pozostawia starego błędu po odzyskaniu łączności i nie prezentuje nieaktualnego stanu jako bieżącego. Obsługa błędów HTTP, walidacja odpowiedzi, timeout i automatyczne ponawianie.
- 28 testów UI PASS, TypeScript/Vite build PASS. API po restarcie potwierdziło zachowane połączenie ChatGPT. Zmiana nie wymaga ponownego logowania.

## Układ ustawień 1.3.3
- Diagnostyka przeniesiona obok formularza modelu, bez duplikatu na dole strony. Prawa kolumna zawiera też bezpieczeństwo i podsumowanie wybranej konfiguracji.
- Jednolite odstępy 24 px pomiędzy głównymi sekcjami ustawień.
- Naprawiono dziedziczenie układu formularza chatu przez Limity zadania. Równe karty pól w dwóch kolumnach, osobne opcje bezpieczeństwa i pasek zapisu; na wąskim ekranie jedna kolumna.
- 26 testów UI PASS i build TypeScript/Vite PASS. Pomiar w przeglądarce potwierdził odstępy 24 px i brak poziomego overflow pól.

## Limity 1.3.2
- Jedna sekcja „Limity zadania”: Limit rund modelu i Limit operacji narzędziowych, z opisami oraz przykładem różnicy.
- Usunięto stare pole kroków z ustawień modelu. Zapis obu limitów w jednej transakcji, bez zmiany dotychczasowych wartości. Starsze API nadal obsługiwane.
- Walidacja zakresów i ochrona przed nadpisaniem limitu przez formularz ustawień modelu.

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
