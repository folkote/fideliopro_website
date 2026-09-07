from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from functools import partial
from threading import Thread
from pathlib import Path
from playwright.sync_api import sync_playwright
import json
out=Path('/evidence');out.mkdir(exist_ok=True)
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args): pass
server=ThreadingHTTPServer(('127.0.0.1',8765),partial(Quiet,directory='/website'))
Thread(target=server.serve_forever,daemon=True).start()
results=[]
with sync_playwright() as pw:
    browser=pw.chromium.launch(args=['--no-sandbox'])
    page=browser.new_page()
    errors=[]
    page.on('pageerror',lambda e: errors.append(str(e)))
    for width in [320,390,820,1060,1440]:
        page.set_viewport_size({'width':width,'height':1000})
        for path in ['/','/ru/','/en/','/es/','/cases.html']:
            page.goto('http://127.0.0.1:8765'+path,wait_until='networkidle')
            # Load lazy images throughout the actual page.
            page.evaluate("document.querySelectorAll('img[loading]').forEach(i=>i.loading='eager')")
            page.wait_for_function("[...document.images].every(i=>i.complete)")
            d=page.evaluate("""() => ({width:innerWidth,scroll:document.documentElement.scrollWidth,h1:document.querySelectorAll('h1').length,broken:[...document.images].filter(i=>!i.naturalWidth).map(i=>i.getAttribute('src')),radii:[...document.querySelectorAll('.card,.partners-card,.contact-card')].map(e=>getComputedStyle(e).borderTopLeftRadius),headerOverflow:document.querySelector('.header-inner').scrollWidth>document.querySelector('.header-inner').clientWidth,setup:document.body.textContent.includes('Настроили агентское вознаграждение')})""")
            d['path']=path
            results.append(d)
            assert d['scroll']<=width,(path,width,'overflow',d)
            assert not d['headerOverflow'],(path,width,'header overflow')
            assert d['h1']==1
            assert not d['broken'],d['broken']
            assert page.locator('a[href*="digital-id-calculator"]').count()==0
            for surface in page.locator('#cases, .case-study').all():
                assert surface.evaluate('el=>getComputedStyle(el).backgroundColor')=='rgb(16, 29, 43)'
                assert surface.evaluate('el=>getComputedStyle(el).color')=='rgb(237, 241, 243)'
            assert page.request.get('http://127.0.0.1:8765/digital-id-calculator.html').status==404
            assert all(float(v.removesuffix('px'))<=8 for v in d['radii']),d
            if path in ['/','/ru/','/cases.html']:assert d['setup']
            if path=='/' and width<=820:
                page.locator('[data-nav-toggle]').click()
                assert page.locator('[data-nav-toggle]').get_attribute('aria-expanded')=='true'
                page.locator('#main-nav a[href="#services"]').click()
                assert page.locator('[data-nav-toggle]').get_attribute('aria-expanded')=='false'
                assert not page.evaluate("document.body.classList.contains('nav-open')")
            if width in [390,1440] and path in ['/','/cases.html']:
                page.evaluate('window.scrollTo(0,0)')
                slug='home' if path=='/' else 'cases'
                page.screenshot(path=str(out/f'{slug}-{width}.png'),full_page=True)
                if path=='/':
                    page.locator('#cases').screenshot(path=str(out/f'case-index-{width}.png'))
                    page.locator('#top').screenshot(path=str(out/f'hero-{width}.png'))
    assert not errors,errors
    page.set_viewport_size({'width':390,'height':844})
    page.goto('http://127.0.0.1:8765/')
    page.locator('#cases a[href="/cases.html#fiscal"]').click()
    assert page.url.endswith('/cases.html#fiscal')
    assert page.locator('#fiscal-title').inner_text().startswith('Настроили')
    browser.close()
(out/'browser.json').write_text(json.dumps({'results':results,'pageerrors':errors,'navigation':'passed'},ensure_ascii=False,indent=2))
print('PASS:',len(results),'viewport/page combinations; assets, radii, headings, menu, links; page errors:',len(errors))
server.shutdown()
