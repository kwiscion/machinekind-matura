"""Synthetic instructions only; no exam/source packs or model calls."""
import copy
import unittest
from classify_item import classify_item


def item(question, fmt='', images=None, **extra):
    return dict(question=question, answer_format=fmt, images=images or [], **extra)


class Tests(unittest.TestCase):
    def test_explicit_essay_without_ids_or_word_minimum(self):
        self.assertEqual(classify_item(item('Napisz wypracowanie na wybrany temat.'))['route'], 'essay')

    def test_existing_structural_essay_shape(self):
        q='Wybierz jeden z tematów wypracowania. Praca: minimum 300 słów.\nTemat 1. A\nTemat 2. B'
        self.assertEqual(classify_item(item(q))['route'], 'essay')

    def test_essay_format_field(self):
        self.assertEqual(classify_item(item('Oceń przedstawione przemiany.', 'Wypracowanie, co najmniej 300 słów.'))['route'], 'essay')

    def test_essay_mention_is_not_an_essay_task(self):
        self.assertEqual(classify_item(item('Wyjaśnij, dlaczego autor nazwał tekst wypracowaniem.'))['route'], 'open')

    def test_closed_option_selection(self):
        self.assertEqual(classify_item(item('Wskaż poprawną odpowiedź.\nA. Pierwsza\nB. Druga'))['route'], 'closed')

    def test_finite_format_can_include_justification(self):
        self.assertEqual(classify_item(item('Wskaż odpowiedź i uzasadnij wybór.', 'Jedna litera i uzasadnienie.'))['route'], 'closed')

    def test_true_false(self):
        self.assertEqual(classify_item(item('Oceń, które stwierdzenia są prawdziwe, a które fałszywe.'))['route'], 'closed')

    def test_open_and_unknown_visual(self):
        self.assertEqual(classify_item(item('Podaj dwie przyczyny.'))['route'], 'open')
        r=classify_item(item('Przyjrzyj się ilustracji.', images=[{'path':'synthetic.png'}]))
        self.assertEqual(r['route'], 'unknown');self.assertTrue(r['visual']);self.assertTrue(r['baseline_fallback'])

    def test_source_and_id_are_never_read(self):
        class Restricted(dict):
            def get(self, key, *args):
                if key not in ('question','answer_format','images'):raise AssertionError('forbidden field read')
                return super().get(key,*args)
        r=Restricted(item('Przeczytaj materiał.', source_text='Napisz wypracowanie minimum 300 słów.', id='essay-closed-secret'))
        self.assertEqual(classify_item(r)['route'], 'unknown')

    def test_source_mutation_and_id_do_not_change_result(self):
        a=item('Podaj nazwę.', source_text='text', id='1');b=dict(a,source_text='wypracowanie prawda fałsz',id='42')
        self.assertEqual(classify_item(a), classify_item(b))

    def test_explicit_override_and_baseline(self):
        x=item('Napisz wypracowanie.')
        self.assertEqual(classify_item(x,override='closed')['route'], 'closed')
        self.assertTrue(classify_item(x,override='unknown')['baseline_fallback'])
        with self.assertRaises(ValueError):classify_item(x,override='auto')

    def test_conflicting_formats_fall_back(self):
        r=classify_item(item('Napisz wypracowanie.', 'Jedna litera.'))
        self.assertEqual(r['route'],'unknown');self.assertIn('conflicting',r['reason'])

    def test_invalid_fields_and_input_immutability(self):
        self.assertTrue(classify_item({'question':None,'answer_format':'','images':[]})['baseline_fallback'])
        x=item('Podaj nazwę.', images=[{'path':'full.png'}],source_text='original');before=copy.deepcopy(x)
        classify_item(x);self.assertEqual(x,before)

    def test_topics_alone_and_numbered_source_are_not_closed(self):
        self.assertEqual(classify_item(item('Wybierz jeden temat.\n1. A\n2. B'))['route'], 'unknown')

    def test_pronoun_choice_with_explicit_essay_structure(self):
        q='Zadanie zawiera dwa tematy. Wybierz jeden z nich do opracowania. Minimum 350 słów.\n1. Pierwszy temat fikcyjny.\n2. Drugi temat fikcyjny.\nWYPRACOWANIE'
        self.assertEqual(classify_item(item(q))['route'], 'essay')

    def test_pronoun_variant_named_topics_and_word_count_linebreak(self):
        q='Przedstawiono tematy.\nWybierz jeden spośród nich. Co najmniej\n400 wyrazów.\nTemat 1. Syntetyczny problem A.\nTemat 2. Syntetyczny problem B.\nESEJ'
        self.assertEqual(classify_item(item(q))['route'], 'essay')

    def test_academic_mention_with_topics_and_length_is_not_directive(self):
        q='Autor omawia tematy wypracowania i minimum 300 słów wymagane w szkole.\n1. Syntetyczny temat A.\n2. Syntetyczny temat B.\nWYPRACOWANIE'
        self.assertEqual(classify_item(item(q))['route'], 'unknown')

    def test_pronoun_structure_without_essay_heading_stays_unknown(self):
        q='Omówiono tematy wypracowania. Wybierz jeden z nich. Minimum 300 słów.\n1. A\n2. B'
        self.assertEqual(classify_item(item(q))['route'], 'unknown')

    def test_unrelated_source_cannot_supply_missing_essay_structure(self):
        q='Przeczytaj omówienie.'
        source='Tematy. Wybierz jeden z nich. Minimum 300 słów.\n1. A\n2. B\nWYPRACOWANIE'
        self.assertEqual(classify_item(item(q,source_text=source))['route'], 'unknown')

    def test_pronoun_choice_without_length_is_not_automatic_essay(self):
        q='Tematy. Wybierz jeden z nich.\n1. A\n2. B\nWYPRACOWANIE'
        self.assertEqual(classify_item(item(q))['route'], 'unknown')


if __name__ == '__main__':unittest.main()
