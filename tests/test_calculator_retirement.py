"""Retired one-off calculator must not ship or remain linked."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1] / 'static' / 'website'

class CalculatorRetirementTests(unittest.TestCase):
    def test_calculator_file_removed(self):
        self.assertFalse((ROOT / 'digital-id-calculator.html').exists())

    def test_no_public_html_references(self):
        for file in ROOT.rglob('*.html'):
            with self.subTest(file=str(file.relative_to(ROOT))):
                self.assertFalse(b'digital-id-calculator' in file.read_bytes().lower(), str(file))

    def test_case_surfaces_use_site_dark_palette(self):
        css = (ROOT / 'css/editorial.css').read_text()
        self.assertFalse('#e8ecee' in css)
        self.assertIn('#cases { background: var(--bg-2); }', css)
        self.assertIn('.case-page { background: var(--bg); }', css)
        for name in ['index.html', 'ru/index.html', 'en/index.html', 'es/index.html', 'cases.html']:
            self.assertIn('/css/editorial.css?v=2', (ROOT / name).read_text())

    def test_digital_id_product_and_contacts_preserved(self):
        for name in ['index.html', 'ru/index.html', 'en/index.html', 'es/index.html']:
            text = (ROOT / name).read_text()
            self.assertIn('solution-digital-id.svg', text)
            self.assertIn('Digital ID', text)
            self.assertIn('mailto:support@fidelio.pro', text)
            self.assertIn('https://telegram.me/fideliopro', text)

if __name__ == '__main__':
    unittest.main()
