"""Static publication contract; stdlib only, no database or outbound requests."""
import unittest
from pathlib import Path
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1] / 'static' / 'website'

class Document(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.ids = []
        self.links = []
        self.h1 = 0
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.append(attrs['id'])
        if tag == 'a':
            self.links.append(attrs.get('href', ''))
        if tag == 'h1':
            self.h1 += 1

class PublicCasesTests(unittest.TestCase):
    def test_details_and_confidentiality(self):
        text = (ROOT / 'cases.html').read_text()
        doc = Document(text)
        self.assertEqual(doc.h1, 1)
        self.assertEqual(len(doc.ids), len(set(doc.ids)))
        for slug in ['restore', 'accounting', 'fiscal']:
            self.assertIn(slug, doc.ids)
        for forbidden in ['Intourist', 'Design Hotel', 'Istra', 'V8TRAIN', 'HRS_DEV', '@session:', 'q_2026', 'Kabardinka', 'Bega', '202608', 'Тест провели, всё получилось']:
            self.assertNotIn(forbidden, text)
        for boundary in ['не запуск всей PMS', 'Приём комплекта бухгалтерией', 'подтверждённый пилот', 'не является юридической или налоговой консультацией']:
            self.assertIn(boundary, text)

    def test_cards_link_to_existing_details(self):
        details = Document((ROOT / 'cases.html').read_text())
        for name in ['index.html', 'ru/index.html']:
            doc = Document((ROOT / name).read_text())
            self.assertEqual(doc.h1, 1)
            self.assertEqual(len(doc.ids), len(set(doc.ids)))
            links = [x for x in doc.links if x.startswith('/cases.html#')]
            self.assertEqual(len(links), 3)
            for link in links:
                self.assertIn(link.split('#')[1], details.ids)

    def test_approved_email_all_locales(self):
        for name in ['index.html', 'ru/index.html', 'en/index.html', 'es/index.html', 'cases.html']:
            text = (ROOT / name).read_text()
            self.assertIn('mailto:support@fidelio.pro', text)
            self.assertNotIn('fidelio@giorni.ru', text)
            self.assertIn('https://telegram.me/fideliopro', text)

if __name__ == '__main__':
    unittest.main()
