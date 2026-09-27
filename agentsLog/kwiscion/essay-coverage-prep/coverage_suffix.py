"""Inactive, source-independent single-answer essay policy. No runtime or calls."""
import copy
import hashlib

SUFFIX = '''

Przed napisaniem wybierz jeden z oferowanych tematów: ten, dla którego potrafisz
najlepiej poprzeć wszystkie wymagane aspekty konkretną wiedzą historyczną.
Dla każdego aspektu wskazanego w oryginalnym poleceniu rozwiń argument:
postaw twierdzenie, przywołaj konkretny i pewny przykład historyczny (wydarzenie,
działanie, instytucję lub proces), wyjaśnij mechanizm przyczynowo-skutkowy oraz
pokaż, jak ten przykład uzasadnia Twoje stanowisko wobec tezy tematu.
Nie zastępuj argumentu listą nazw ani powtarzaniem ogólnych ocen. Nie wymyślaj
dat, nazwisk, porozumień ani szczegółów; jeżeli przykład jest niepewny, oprzyj
argument na innym, dobrze znanym fakcie. Sprawdź pokrycie wszystkich wymaganych
aspektów i zgodność wniosków z przytoczonymi faktami.
Zwróć tylko numer wybranego tematu i jedno wypracowanie: 400–500 słów ciągłego
tekstu z tezą i zakończeniem, bez planu, checklisty, oceny własnej pracy,
komentarzy ani drugiego tematu. Zachowaj pełne wymagania i materiały zadania.
'''
SUFFIX_SHA256 = hashlib.sha256(SUFFIX.encode('utf8')).hexdigest()


def append_to_item(item):
    """Return a derived organizer item; preserve every original field and prefix.

    The caller selects the essay route explicitly and freezes a NEW package.
    This function does not classify, select a historical answer, or edit files.
    """
    if not isinstance(item, dict) or not isinstance(item.get('question'), str) or not item['question'].strip():
        raise ValueError('A complete original question is required')
    if item['question'].endswith(SUFFIX):
        raise ValueError('Coverage policy is already appended')
    derived = copy.deepcopy(item)
    derived['question'] += SUFFIX
    return derived
