# VEKTOR 1.7 — odzyskiwanie, kontekst i edycja wyników

## Kontynuacja po przerwaniu

Zadanie i zaakceptowany zestaw wywołań narzędzi są zapisywane przed wykonaniem.
Zamknięcie karty nie zatrzymuje zadania. Po restarcie VEKTOR kontynuuje od zapisanego
etapu, zachowując identyfikator zadania, rozmowę, model i zużyty budżet operacji.
Potwierdzone wyniki nie są wykonywane drugi raz. Przerwany odczyt można powtórzyć.

Jeżeli proces zniknął podczas operacji mogącej zmienić dane, w chacie pojawia się
**Odzyskiwanie zadania**. Sprawdź nazwę, argumenty i rzeczywiste skutki. Możesz:

- kontynuować bez ponowienia (nie oznacza to, że poprzednia operacja się udała),
- świadomie ponowić wskazaną operację,
- zatrzymać zadanie bez kontynuacji.

Zewnętrzne serwery, MCP i polecenia systemowe nie zapewniają wspólnej transakcji
z bazą VEKTORA. Nie obiecujemy dokładnie jednego wykonania po dowolnej awarii;
niepewne skutki wymagają decyzji. Stare zadania bez punktu kontynuacji nie dostają
zmyślonego kontekstu wykonania.

## Cofanie zmian zadania

Przycisk **Zmiany zadania** pokazuje pliki utworzone, zmienione i usunięte podczas
zadania, wraz z różnicami i wyborem plików do przywrócenia. Potwierdź dopiero po
obejrzeniu różnic. Nowszy zapis jest zachowywany w prywatnej kopii; konflikt po
wykonaniu zadania blokuje nadpisanie.

Kopia obejmuje obserwowane zmiany w katalogu projektu, a nie cały komputer.
Może objąć również zapis innego programu wykonany równolegle w tym katalogu;
to nie izolacja systemowa ani pewne ustalenie autora każdej zmiany. Nie cofa
wysłanych wiadomości, instalacji, operacji sieciowych ani plików poza projektem.
Dowiązania, specjalne pliki i pliki przekraczające limity są pomijane i wskazywane.

**Ustawienia → Odzyskiwanie i historia** zawierają limity magazynu kopii, jednej
kopii, pliku i liczby plików. Po osiągnięciu limitu starsze kopie nie są samowolnie
usuwane — interfejs informuje o niepełnym pokryciu.

## Kosz

Usunięcie rozmowy lub projektu z potwierdzeniem przenosi go do **Kosza**. Domyślna
retencja to 30 dni; 0 oznacza brak automatycznego opróżniania. Zmiana retencji
dotyczy nowych elementów. Przywrócenie projektu pozostawia jego automatyzacje
wstrzymane, aby nie wykonały od razu zaległych działań.

Rozmowy w koszu nie uczestniczą w wyszukiwaniu kontekstu. Usunięcie samej rozmowy
nie usuwa plików projektu. Trwałe usunięcie projektu obejmuje jego własny katalog
z rozmowami i artefaktami; pliki zewnętrzne/współdzielone pozostają chronione.
Trwałe usunięcie jest osobną, potwierdzaną akcją. Przetwarzanie wygasłej retencji
odbywa się, gdy aplikacja działa.

## Skąd to wiesz?

Przycisk przy odpowiedzi otwiera źródła faktycznie przekazane modelowi w danej
rundzie: pamięć, dokumenty, rozmowy projektu, załączniki i wyniki narzędzi.
Możesz zmienić rundę, otworzyć źródło, przypiąć je, pominąć w dalszych odpowiedziach
lub poprawić aktualną pamięć. Historyczny zapis pozostaje niezmieniony.

Przypinanie działa w ramach budżetu kontekstu. Inspektor nie odtwarza prywatnego
rozumowania modelu i nie zgaduje źródeł starych odpowiedzi bez zapisanego kontekstu.

## Edytor wyników przy chacie

**Edytuj** na karcie artefaktu otwiera boczny panel. Na małym ekranie można użyć
widoku nakładanego, a na większym regulować szerokość lub powiększyć panel.

- Tekst, kod, Markdown i Mermaid: edycja treści, podgląd Markdown/diagramu.
- Word: wskazany akapit lub komórka tabeli, bez zastępowania całego dokumentu.
- Excel: komórka albo zakres; formuły przelicza LibreOffice w obrazie Dockera.
- PowerPoint: tekst we wskazanym polu lub komórce tabeli.
- PDF: kolejność stron oraz obsługiwane pola formularza, nie dowolny tekst strony.

Najpierw tworzona jest prywatna propozycja z podglądem różnic. **Zatwierdź i zapisz**
sprawdza, czy oryginał się nie zmienił, a następnie zapisuje nową wersję z historią.
Możesz poprosić VEKTORA o propozycję zmiany wskazanego fragmentu. Taka tura ma
ograniczony zestaw narzędzi; nawet pełny dostęp nie zatwierdza automatycznie
propozycji edytora. Nie zapisuj nieznanych makr ani nie uruchamiaj kodu tylko dlatego,
że znalazł się w pliku — podgląd kodu go nie wykonuje.

## Procedury

**Procedury** w chacie pozwalają utworzyć nowy przepis albo szkic z zakończonej
rozmowy i jej rzeczywistych działań. Uzupełnij kroki, kryteria i parametry
`{{nazwa_parametru}}`; przejrzyj instrukcje i opublikuj zatwierdzoną wersję.

Opublikowane wersje są niezmienne. Uruchomienie oraz harmonogram wskazują konkretną
wersję i wartości parametrów. Zmiana przepisu nie zmienia po cichu istniejącej
automatyzacji. Każde uruchomienie podlega aktualnym limitom, trybowi lokalnemu/cloud
i zgodom — zgoda z dawnej rozmowy nie jest nową zgodą.

## Laboratorium jakości

**Ustawienia → Diagnostyka → Laboratorium jakości** uruchamia kontrole komponentów
oraz opcjonalnie porównanie do trzech modeli, w tym najwyżej jednego lokalnego.
Modele działają kolejno na syntetycznych danych: obliczenia, odczyt narzędziem,
wielokrokowy zapis pliku, próba iniekcji i prosty obraz (jeżeli Vision jest dostępne).

Brak obsługi lub dostępu jest oznaczany jako nieprzetestowany, nie jako sukces.
Wyniki, czas, liczba tokenów i dowody można przeglądać historycznie i pobrać.
Test nie zmienia domyślnego modelu, nie przetwarza prywatnych rozmów i nie daje
modelowi narzędzi systemowych ani MCP. Cloud zużywa limity konta. Jest przycisk
zatrzymania, limit każdego scenariusza i zachowanie wyników częściowych.
Zaliczenie tych przypadków nie jest gwarancją poprawności dowolnego zadania.
