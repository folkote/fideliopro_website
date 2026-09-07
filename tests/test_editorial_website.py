"""Editorial redesign and factual correction: no runtime dependencies."""
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'static' / 'website'

class EditorialWebsiteTests(unittest.TestCase):
    def test_fiscal_setup_precedes_verification(self):
        for name in ['index.html', 'ru/index.html', 'cases.html']:
            text = (ROOT / name).read_text()
            self.assertIn('Настроили агентское вознаграждение', text)
            self.assertNotIn('Проверили агентский чек с разными ставками НДС', text)
        text = (ROOT / 'cases.html').read_text()
        self.assertIn('Выполнили первоначальную настройку агентского вознаграждения', text)
        self.assertIn('не является юридической или налоговой консультацией', text)

    def test_editorial_css_on_all_locales_and_details(self):
        for name in ['index.html', 'ru/index.html', 'en/index.html', 'es/index.html', 'cases.html']:
            self.assertIn('css/editorial.css?v=1', (ROOT / name).read_text())
        css = (ROOT / 'css/editorial.css').read_text()
        self.assertIn('--radius-md: 6px', css)
        self.assertIn('focus-visible', css)
        self.assertIn('prefers-reduced-motion', css)

    def test_original_graphics_are_local_safe_svg(self):
        for name in ['hotel-systems', 'case-restore', 'case-accounting', 'case-fiscal']:
            path = ROOT / 'images/editorial' / (name + '.svg')
            svg = ET.parse(path).getroot()
            self.assertTrue(svg.get('viewBox'))
            self.assertTrue(svg.get('aria-labelledby'))
            for el in svg.iter():
                tag = el.tag.split('}')[-1]
                self.assertNotIn(tag, ['script', 'foreignObject', 'image'])
                self.assertFalse(any(k.lower().startswith('on') for k in el.attrib))
                for k, v in el.attrib.items():
                    if k.endswith('href'):
                        self.assertTrue(v.startswith('#'))
            self.assertLess(path.stat().st_size, 100000)

    def test_case_links_have_specific_accessible_labels(self):
        for name in ['index.html', 'ru/index.html']:
            text = (ROOT / name).read_text()
            for case in ['restore', 'accounting', 'fiscal']:
                self.assertIn('case-' + case + '.svg', text)
            self.assertNotIn('>Подробнее о работе</a>', text)
        self.assertIn('class="case-study"', (ROOT / 'cases.html').read_text())

if __name__ == '__main__':
    unittest.main()
