# VEKTOR Windows 1.8.1 — bezpieczne domykanie generowania obrazów

- Agent kończy zwykłe zlecenie po najwyżej dwóch natywnych generacjach: pierwszym obrazie i jednej autonomicznej korekcie. Jawnie zamówione serie i warianty nadal zachowują wskazaną liczbę wyników.
- Po osiągnięciu limitu VEKTOR wybiera najlepszy istniejący artefakt i przedstawia odpowiedź końcową zamiast bez końca poprawiać obraz.
- Zablokowano obchodzenie natywnego generatora przez rysowanie obrazu lub „referencji” w Pythonie, shellu, SVG, Matplotlib, Pillow, OpenCV albo podobnym kodzie. Odczyt i techniczna kontrola obrazu nadal są dozwolone.
- Chronologia czatu pokazuje, że limit iteracji zadziałał. Oryginalny wynik i dopuszczona korekta pozostają dostępne jako zwykłe artefakty.
- Instalator przypina po SHA256 zarówno VEKTORA, jak i lokalny generator Stable Diffusion 1.8.1; modele i dane użytkownika pozostają w trwałych woluminach.

## Weryfikacja 1.8.1

- Pełny backend: **529 PASS / 2 SKIP**; UI: **127 PASS**, produkcyjny build poprawny, ESLint bez błędów. Dodano regresje limitu generowania oraz wykrywania syntezy obrazów przez kod.
- Rzeczywisty test E2E na RTX 5070 Laptop z trudnym promptem zakończył się po dwóch natywnych generacjach, bez Pythona. Końcowy PNG 512×512 został poprawnie otwarty i pobrany; druga wersja przeszła analizę Vision.
- Docker Scout dla obu finalnych obrazów: **0 critical / 0 high**. Główny obraz zawiera powiązane z wydaniem oświadczenie OpenVEX.

# VEKTOR Windows 1.8.0 — lokalny Stable Diffusion

- Lokalny generator **Stable Diffusion XL** działa jako osobny, izolowany kontener GPU. Obsługuje text-to-image i img2img, pokazuje postęp w czacie i zapisuje wynik jako zwykły artefakt z podglądem, otwieraniem i pobieraniem.
- Domyślny szybki model to SDXL Turbo. Klasyczny SDXL Base jest dostępny do świadomego pobrania. Użytkownik widzi rozmiar, licencję i stan modelu; pobranie kilku GB wymaga potwierdzenia i można je anulować.
- Ustawienia obejmują model, wymiary, liczbę kroków, guidance, seed, siłę img2img, urządzenie, tryb pamięci i timeout. Profile są walidowane — np. Turbo nie przyjmuje CFG ani negative prompt — a naprawiona późniejsza próba nie blokuje całego wyniku.
- Generator nie ma dostępu do bazy rozmów ani całego workspace. Dostaje uwierzytelnione, ograniczone żądanie oraz kontrolowaną kopię obrazu wejściowego; nie uruchamia kodu ani dowolnych ścieżek. Proces generowania kończy się po zadaniu, zwalniając VRAM dla Ollamy.
- Instalator uruchamia generator tylko po rzeczywistym teście NVIDIA w Dockerze. Komputer bez działającego GPU zachowuje VEKTORA i Ollamę bez pobierania ciężkiego obrazu generatora. Modele są trzymane w osobnym, trwałym woluminie.
- Protokół aktualizacji 2 wiąże po SHA256 zarówno obraz VEKTORA, jak i generatora. Starszy moduł bezpiecznie wymaga jednorazowego uruchomienia instalatora 1.8.0; kolejne zgodne aktualizacje zachowują modele i potrafią cofnąć oba obrazy.

## Weryfikacja 1.8.0

- Rzeczywiste generowanie na RTX 5070 Laptop: txt2img 512×512 i img2img z zachowaniem oryginału, poprawne PNG, kontrola SHA256 i pełne dekodowanie. Po zakończeniu VRAM wrócił do stanu spoczynkowego.
- Pełny backend Windows: **523 PASS / 2 SKIP**; UI: **127 PASS**, poprawny build TypeScript/Vite oraz ESLint bez błędów. Testy instalatora PowerShell 5.1 i spójności przypięć obu obrazów również przeszły.
- Docker Scout: **0 critical / 0 high** w sidecarze bez wyjątków oraz **0 / 0** w obrazie aplikacji po poprawkach i uwzględnieniu dwóch publicznych ocen OpenVEX dla narzędzi `tiffcrop` i `libgstogg.so`, których obraz runtime nie zawiera.
- Nie obiecujemy identycznej szybkości ani jakości na każdym GPU. Pierwsze pobranie modelu wymaga internetu i wolnego miejsca; generowanie lokalne nie zastępuje generatora OpenAI, który pozostaje osobnym wyborem.

## VEKTOR Windows 1.7.0 — odzyskiwanie, kontekst i edycja wyników

- Trwałe punkty kontynuacji, zaakceptowane wywołania i wyniki narzędzi. Restart zachowuje zadanie i budżet; potwierdzone operacje nie są powtarzane. Niepewne skutki zapisu wymagają jawnej decyzji: pominąć ponowienie, świadomie ponowić lub zatrzymać. Brak obietnicy atomowości zewnętrznych usług.
- **Zmiany zadania**: podgląd różnic, wybór plików i przywracanie z ochroną przed nadpisaniem późniejszych zmian. Kopie są ograniczone do katalogu projektu i limitów dysku; pliki pominięte są widoczne. Operacje poza katalogiem, wiadomości i instalacje nie są cofane.
- **Kosz** rozmów i projektów z przywracaniem, domyślną retencją 30 dni i osobnym potwierdzeniem trwałego usunięcia. Usunięte rozmowy nie zasilają kontekstu. Pliki współdzielone są chronione; przywrócone automatyzacje pozostają wstrzymane.
- **Skąd to wiesz?** przy odpowiedzi: rzeczywiste źródła danej rundy, wyniki narzędzi, przypinanie/pomijanie źródeł i poprawianie pamięci. Historyczne źródła pozostają niezmienione; nie pokazujemy prywatnego rozumowania modelu.
- **Edytuj** przy artefakcie: panel obok czatu, tekst/kod, Markdown/Mermaid, akapity i tabele DOCX, komórki i zakresy XLSX, tekst PPTX, strony i formularze PDF. Propozycja AI ma ograniczony zakres i nie nadpisuje oryginału bez potwierdzenia, także przy pełnym dostępie. Historia, podgląd, pobranie i kontrola konfliktów.
- **Procedury**: szkic z zakończonej rozmowy albo ręcznie, parametry, kroki i kryteria, przegląd przed publikacją, niezmienne wersje oraz uruchamianie i harmonogram związany z konkretną wersją. Dawna zgoda nie autoryzuje nowego działania.
- **Laboratorium jakości** w diagnostyce: kontrole komponentów i syntetyczne testy do trzech modeli, wykonywane kolejno. Czas, tokeny, dowody, historia i pobranie raportu, zatrzymanie i limity. Brak Vision/dostępu nie jest liczony jako PASS; domyślny model nie jest samowolnie zmieniany.
- Poprawki UI: chronologia i liczniki po odświeżeniu, działające względne odnośniki do znanych artefaktów, czytelny edytor w węższym oknie, zawijanie długich skrótów, jednolite przyciski, różnice plików bez końcowego Entera. Aktywne zadanie nie dostaje zmyślonej odpowiedzi końcowej z surowego wyniku narzędzia.

## Weryfikacja 1.7.0

- Backend Windows: **510 PASS / 2 SKIP**; finalny obraz Linux: **494 PASS / 18 SKIP**; UI: **127 PASS**, poprawny build TypeScript/Vite. Pominięte testy są zależne od platformy, nie zaliczamy ich jako sukcesy.
- Pięć rzeczywistych testów zatrzymania/restartu procesu w finalnym obrazie: brak powtórzenia potwierdzonego zapisu, łagodny restart, niepewny zapis z pominięciem, jawne ponowienie oraz przerwanie zatwierdzanej operacji.
- Dwukrotna migracja kopii ośmiu baz projektów do 0003: identyczne dane wszystkich wcześniejszych tabel i poprawna integralność. Testy nie modyfikowały oryginałów.
- Rzeczywiste modele: GLM 5.3 **4/4** obsługiwanych scenariuszy; Flash **5/5**, łącznie z prostym Vision. Wszystkie pięć kontroli aplikacji zaliczone. To konkretne testy, nie gwarancja poprawności dowolnego zadania.
- Testy na żywym UI: wykonanie procedury i zgoda, podgląd/zapis/cofnięcie artefaktu, kosz i przywrócenie, rzeczywisty inspektor kontekstu, laboratorium oraz ograniczona propozycja AI bez modyfikacji oryginału przed zgodą.
- Instalator Windows x64 pozostaje online; przypina obraz VEKTORA i Ollamy po SHA256, obsługuje instalację brakujących zależności, skrót i start modułu Windows. Bez kopiowania tokenów autora. SmartScreen nie jest wyłączany. Nie deklarujemy testu instalacji na każdym komputerze.

Instrukcja nowych funkcji: [WORKBENCH.md](https://github.com/Gartom91/VEKTOR-Installer/blob/main/docs/WORKBENCH.md).

## VEKTOR Windows 1.6.4 — kontekst z historii rozmów projektu

- Agent wyszukuje i odczytuje wcześniejsze rozmowy z bieżącego projektu/kategorii. „Bez projektu” ma osobną historię; narzędzia nie pozwalają wybierać obcej bazy ani czytać chatów innego projektu.
- Trafne, datowane fragmenty uzupełniają kontekst automatycznie. `search_project_chats` wyszukuje temat lub przegląda ostatnie rozmowy, a `read_project_chat` doczytuje je chronologicznie, również długie pojedyncze wiadomości, z zachowaniem limitu kontekstu.
- Wyszukiwanie działa lokalnie w SQLite, bez dodatkowego modelu i wywołań cloud. Indeks uwzględnia dodanie, edycję i usunięcie wiadomości; obsługuje polskie znaki, tytuły i stare wiadomości poza ostatnimi 30 wpisami.
- Historyczne ustalenia mają linki do źródeł. Odnośnik otwiera właściwy projekt i chat w osobnej karcie oraz wyróżnia cytowaną wiadomość, zachowując bieżące zadanie i szkic prompta.
- Historia jest cytowanymi danymi, nie nową instrukcją lub zgodą. Dawne polecenia nie odblokowują zmian przy nowym pytaniu, także z pełnym dostępem. Rozpoznawalne sekrety są maskowane, a prywatne rozumowanie, podglądy streamingu i bajty załączników nie są importowane.
- Polecenie „Nie korzystaj z poprzednich rozmów w tym zadaniu” wyłącza korzystanie z historii dla bieżącego zadania. Błąd indeksu nie jest przedstawiany jako pusta historia i nie blokuje niepowiązanej pracy.
- Zbyt duży limit strony podany przez model jest bezpiecznie ograniczany przez serwer zamiast powodować serię ponowień. Nadal dostępny jest kursor do dalszego odczytu.
- Weryfikacja: 36 regresji historii, pełny backend Windows 464 PASS / 1 SKIP, docelowy obraz Linux 447 PASS / 18 SKIP, interfejs 117 PASS i produkcyjny build. Pięć prób HTTP z rzeczywistym `glm-5.3:cloud` na izolowanej instancji Docker potwierdziło trafny kontekst, oba narzędzia, źródła, rozdzielenie dwóch projektów i „Bez projektu” oraz wyłączenie historii, bez błędów narzędzi i bez fallbacku.

## VEKTOR Windows 1.6.3 — edycja obrazów przez podłączony OpenAI

- Polecenia złożone, np. „Weź ten obraz i na jego podstawie wygeneruj mi postać w bardziej bojowej pozie”, nie są już traktowane jako sama dyskusja. Poprawiona klasyfikacja działa także przy ponowieniu wcześniejszej rozmowy; nie cofa wyraźnego wstrzymania działań.
- Generator jest narzędziem niezależnym od listy umiejętności. Sama analiza Vision lub gotowy prompt nie wystarczają do zakończenia zamówionego generowania. Po błędnej odmowie modelu VEKTOR podejmuje ograniczoną próbę naprawczą przez normalne narzędzie i mechanizm zgód.
- Edycja korzysta z oryginalnych obrazów załączonych do rozmowy lub wskazanych w workspace projektu. Codex App Server otrzymuje rzeczywiste obrazy jako wejścia `localImage`, nie tylko opis Vision. Kontrolowane są przynależność źródeł, integralność, format i rozmiar.
- Oryginały i wcześniejsze wyniki nie są nadpisywane. Brak pliku, błąd generatora lub brak obsługi edycji z referencją oznacza jawny problem, nie wygenerowanie zamiennika z samego tekstu ani fałszywy sukces.
- Zachowano tryb lokalny, uprawnienia i wycofywanie zgód. Zatwierdzone generowanie nie jest powtarzane podczas kontynuacji. Tymczasowe kopie wejść są sprzątane także po błędzie, timeoutcie i anulowaniu.
- Bez zmiany logowania: używane jest dotychczas podłączone konto Codex / ChatGPT projektu. Nie są kopiowane tokeny z aplikacji Codex ani włączane rozliczenia API.
- Testy: 74 regresje obrazów PASS, pełny backend Windows 428 PASS / 1 SKIP, docelowy obraz Linux 411 PASS / 18 SKIP, interfejs 103 PASS i produkcyjny build. Testy instalatora PowerShell 5.1 PASS. Regresje obejmują fałszywą odmowę modelu, rzeczywiste bajty referencji, brak załącznika, błędy dostawcy, granice projektów, zgody, timeout i anulowanie.

## VEKTOR Windows 1.6.2 — kompaktowy wybór modelu w chacie

- Selektor modelu nie rozciąga się już na wolną szerokość pola prompta. Pole modelu ma 214 px, cały zestaw z trybem i odświeżaniem — maksymalnie 440 px. Na węższym ekranie kontrolki zawijają się; długie nazwy są skracane wizualnie, a pełna nazwa pozostaje w podpowiedzi i na liście.
- Usunięto stały dopisek o przekazywaniu obrazów przez Flash/Vision i pusty wiersz pod selektorem. Automatyczna analiza obrazów i wybór specjalisty pozostają bez zmian.
- Nadal widoczne są potrzebne komunikaty: wczytywanie, zapis, błędy, brak obsługi narzędzi oraz wpływ zmiany modelu na następny prompt.
- 103 testy UI PASS oraz produkcyjny build TypeScript/Vite. Regresje obejmują brak dopisku i pustego wiersza, komunikaty, długie nazwy, ograniczenie szerokości, wybór i zapisywanie modelu.
- Testy backendu: Windows 359 PASS / 1 SKIP, docelowy obraz Linux 342 PASS / 18 SKIP; testy instalatora PowerShell 5.1 PASS.
- Aktualizacja nie zmienia danych, uprawnień ani konfiguracji modeli. Dostępna przez mechanizm aktualizacji VEKTORA.

## VEKTOR Windows 1.6.1 — podgląd i jawna edycja projektów

- Nazwa i instrukcje istniejącego projektu są domyślnie tylko do odczytu. Tekst nadal można zaznaczyć i skopiować.
- Dopiero przycisk **Edytuj** na karcie projektu lub pod formularzem odblokowuje pola. Zapis ponownie włącza podgląd; **Anuluj edycję** odtwarza zapisane wartości bez wysyłania zmian.
- Wybranie innego projektu i ponowne otwarcie okna nie dziedziczą trybu edycji. Błąd zapisu pozostawia edytowalny szkic. **Nowy projekt** jawnie otwiera pusty formularz do wpisywania.
- Instrukcje „Bez projektu” również wymagają wybrania edycji; stała nazwa tej przestrzeni pozostaje zablokowana.
- 94 testy UI PASS oraz poprawny build TypeScript/Vite. Dodano regresje blokady pól, zmiany projektu, zapisu, anulowania, ponownego otwarcia i tworzenia; test nowszego interfejsu nie zależy już od wpisanej na sztywno wersji aplikacji.
- Testy backendu: Windows 359 PASS / 1 SKIP, docelowy obraz Linux 342 PASS / 18 SKIP; testy instalatora PowerShell 5.1 PASS.
- Aktualizacja dostępna przez mechanizm wprowadzony w 1.6.0; nie zmienia schematu danych ani uprawnień agenta.

## VEKTOR Windows 1.6.0 — automatyczne aktualizacje

- Nowy panel **Ustawienia → Aktualizacje VEKTORA**, wspólny dla wszystkich projektów. Domyślnie sprawdzanie stabilnych wydań co 6 godzin i instalowanie po 5 minutach bezczynności. Obie opcje oraz czasy można zmienić; ręczna instalacja ma potwierdzenie.
- Aktualizacja czeka na zakończenie zadań, kolejki, zgód i bieżących operacji wszystkich projektów. Pobieranie obrazu nie blokuje pracy. Dostępne pomijanie wydania, etapy postępu i historia.
- Weryfikacja SHA256 manifestu GitHub i obrazu Docker, kontrola wersji/protokołu. Wyłącznie oficjalne stabilne wydania; bez uruchamiania pobranych skryptów i bez gniazda Dockera w aplikacji.
- Kopie wszystkich baz SQLite oraz plików woluminu danych przed zmianą. Pomijany jest wyłącznie cache i procesowy katalog tymczasowy Codexa; logowania, sesje i właściwe dane są zachowane. Kontrola nowej wersji, rozmów i zachowanych plików. Przy błędzie powrót do poprzedniego obrazu oraz kopii; wadliwe wydanie nie jest ponawiane automatycznie.
- Trwały dziennik pozwala dokończyć przerwaną aktualizację. Zagubiona odpowiedź HTTP po zakończeniu nie cofa późniejszej pracy. Wygasła blokada, uszkodzenie danych lub niedziałający Docker mogą wymagać ręcznej diagnostyki — updater nie odtwarza starej kopii na niepewnym stanie.
- Moduł Windows startuje ze skrótu także z wyłączonym dostępem do pulpitu/plików. Diagnostyka i aktualizacje nie włączają pełnego dostępu. Przypięta wersja przetrwa kolejne uruchomienie; nowszy instalator zachowuje kopię dotychczasowego przypięcia i odrzuca niestandardowy override. Skrót, instalator i updater mają wspólną blokadę, aby uruchomienie okna nie przerwało przywracania danych.
- Po aktualizacji użytkownik decyduje o odświeżeniu UI. Szkic prompta i załączniki są zachowane; niezapisane pozostałe formularze należy zapisać przed odświeżeniem.
- Docker Desktop, Ollama, pobrane modele i sam moduł Windows nie są automatycznie wymieniane. Nowy protokół hosta wymaga instalatora. Kopie pozostają do ręcznego przeglądu; wymagają wolnego miejsca. Zewnętrzne workspace pozostają nietknięte.

## Weryfikacja 1.6.0

- UI: 87 testów PASS i build TypeScript/Vite. Backend Windows: 359 PASS / 1 SKIP. Linux: 342 PASS / 18 SKIP (integracje Windows testowane osobno). Testy instalatora wykonane lokalnie; pipeline ponownie sprawdza pakiet EXE. Wspólną blokadę sprawdzono między rzeczywistymi procesami PowerShell 5.1 i modułu aktualizacji.
- Naprawa przy starcie historycznych statusów „oczekiwanie na zgodę”, pozostawionych przez starszy mechanizm bez trwałych zadań: wyłącznie gdy wszystkie istniejące zgody są już rozstrzygnięte, a rozmowa nie ma żadnego zadania w rejestrze. Status zmienia się na „przerwane”, z audytem; nie oznaczamy zadania jako pomyślnie ukończonego. Faktycznie oczekujące zgody pozostają bez zmian.
- Rzeczywista próba na osobnej instancji Docker z trzema syntetycznymi projektami: odłożenie przy pracy w innym projekcie, zamiana obrazu, kontrola kopii i zachowanie workspace. Celowe usunięcie testowej wiadomości oraz uszkodzenie testowego pliku logowania wywołały rzeczywisty rollback obrazu i odtworzenie danych. Produkcyjnych danych nie użyto do symulacji awarii.
- Test poprzedniej wersji korzystał z obrazu testowego zawierającego protokół aktualizacji 1. Aktualizacja starszych instalacji bez protokołu wymaga jednorazowego uruchomienia tego instalatora. Nie deklarujemy sprawdzenia każdego komputera Windows ani każdej przyszłej migracji.
- Instalator online, Windows x64, bez komercyjnego podpisu Authenticode. Nie wyłączaj SmartScreen. Zaloguj się samodzielnie do usług cloud; wydanie nie zawiera tokenów autora.

## VEKTOR Windows 1.5.0

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
