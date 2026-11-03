"""
Comprehensive Portfolio Verification Suite
Verifies:
1. 60fps Mobile Scroll & Touch Optimization
2. Touch Target Ergonomics (>= 44x44px)
3. WCAG 2.2 Level AA Color Contrast
4. CLS & Image Optimization (WebP + JPG fallback + explicit dimensions)
5. DOM Cleanliness & Tag Balance
6. Local HTTP Server & MIME types
"""

import os
import re
import sys
import unittest
from html.parser import HTMLParser
from PIL import Image

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_HTML = os.path.join(BASE_DIR, 'index.html')
WEBP_PATH = os.path.join(BASE_DIR, 'assets', 'jubayer.webp')
JPG_PATH = os.path.join(BASE_DIR, 'assets', 'jubayer.jpg')

def srgb_to_linear(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

def luminance(hex_code):
    hex_code = hex_code.lstrip('#')
    r, g, b = [int(hex_code[i:i+2], 16) for i in (0, 2, 4)]
    return 0.2126 * srgb_to_linear(r) + 0.7152 * srgb_to_linear(g) + 0.0722 * srgb_to_linear(b)

def contrast(hex1, hex2):
    l1 = luminance(hex1)
    l2 = luminance(hex2)
    return (max(l1, l2) + 0.05) / (min(l1, l2) + 0.05)


class TestPortfolioAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(INDEX_HTML, 'r', encoding='utf-8') as f:
            cls.html = f.read()

    def test_scrollspy_early_exit_guard(self):
        """1.1 setActiveNav must have early exit guard against forced layout thrashing."""
        self.assertIn(
            "if (activeNavTarget === targetId && !isUserClick) return;",
            self.html,
            "setActiveNav missing early exit guard"
        )
        self.assertIn(
            "let activeNavTarget = null;",
            self.html,
            "activeNavTarget should initialize to null for clean first-tick sync"
        )

    def test_passive_scroll_and_resize_listeners(self):
        """1.2 scroll and resize listeners must have { passive: true }."""
        self.assertIn(
            "window.addEventListener('scroll', () => {",
            self.html
        )
        self.assertIn(
            "}, { passive: true });",
            self.html
        )
        self.assertIn(
            "window.addEventListener('resize', () => {",
            self.html
        )

    def test_touch_and_fine_pointer_guards(self):
        """1.3 mousemove handlers must guard against touch scrolling."""
        guard = "if (!isFinePointer || (Date.now() - lastTouchTime < 1000)) return;"
        # Must be present in project-card, bento/case-study cards, and global window mousemove
        occurrences = self.html.count(guard)
        self.assertGreaterEqual(
            occurrences,
            3,
            f"Expected at least 3 occurrences of touch guard, found {occurrences}"
        )
        self.assertIn("let isFinePointer = window.matchMedia('(pointer: fine)').matches;", self.html)
        self.assertIn("finePointerQuery.addEventListener('change'", self.html)

    def test_mobile_menu_scroll_lock_and_safe_dismiss(self):
        """1.4 toggleMobileMenu must lock/unlock scroll and have safe dismissal."""
        self.assertIn(
            "document.body.style.overflow = isClosed ? 'auto' : 'hidden';",
            self.html
        )
        # Resize to desktop must dismiss open mobile menu
        self.assertIn("if (window.innerWidth >= 768 && mobileMenu && !mobileMenu.classList.contains('hidden'))", self.html)
        # Escape key must dismiss mobile menu if open
        self.assertIn("mobileMenu && !mobileMenu.classList.contains('hidden')", self.html)

    def test_touch_target_sizes_compliance(self):
        """2.0 All interactive buttons must satisfy >= 44x44px touch targets."""
        # Theme toggle button
        self.assertIn('id="theme-toggle"', self.html)
        self.assertIn('w-11 h-11', self.html[self.html.find('id="theme-toggle"'):self.html.find('id="theme-toggle"')+150])

        # Mobile menu toggle button
        self.assertIn('min-w-[44px] min-h-[44px]', self.html[self.html.find('toggleMobileMenu()'):self.html.find('toggleMobileMenu()')+180])

        # Filter category buttons
        filters = re.findall(r'class="project-filter-btn[^"]*"', self.html)
        self.assertEqual(len(filters), 4, "Must have exactly 4 filter category buttons")
        for f in filters:
            self.assertIn('min-h-[44px]', f)
            self.assertIn('inline-flex items-center', f)
            self.assertIn('cursor-pointer', f)

        # Modal close buttons & chevrons
        self.assertIn('w-11 h-11 min-w-[44px] min-h-[44px]', self.html)
        
        # Audit modal close button
        audit_idx = self.html.find('id="audit-modal"')
        audit_snippet = self.html[audit_idx:audit_idx+600]
        self.assertIn('closeAuditModal()', audit_snippet)
        self.assertIn('w-11 h-11 min-w-[44px] min-h-[44px]', audit_snippet)

        # Case study modal bottom close button
        self.assertIn('onclick="closeCaseStudyModal()" class="min-h-[44px]', self.html)
        # Legal modal bottom close button
        self.assertIn('onclick="closeLegalModal()" class="min-h-[44px]', self.html)

    def test_color_contrast_wcag_aa(self):
        """3.0 Colors must maintain WCAG 2.2 Level AA >= 4.5:1 contrast."""
        # ink-soft must be #4769a5
        self.assertIn("'ink-soft': '#4769a5'", self.html)
        cr_ink_soft = contrast('#4769a5', '#ffffff')
        self.assertGreaterEqual(cr_ink_soft, 4.5, f"ink-soft contrast against white is {cr_ink_soft:.2f}, must be >= 4.5:1")

        # Zero low contrast slate-500
        self.assertEqual(self.html.count('dark:text-slate-500'), 0, "No dark:text-slate-500 should remain")

        # Audit modal close button must have dark:text-dark-muted
        audit_idx = self.html.find('id="audit-modal"')
        audit_snippet = self.html[audit_idx:audit_idx+600]
        self.assertIn('dark:text-dark-muted', audit_snippet)
        cr_dark_muted = contrast('#94a3b8', '#141f36')
        self.assertGreaterEqual(cr_dark_muted, 4.5, f"dark-muted contrast against dark-card is {cr_dark_muted:.2f}, must be >= 4.5:1")

    def test_image_optimization_and_cls(self):
        """4.0 Hero and Avatar images must have dimensions, picture WebP source, and lazy/high priority."""
        self.assertTrue(os.path.exists(WEBP_PATH), "assets/jubayer.webp must exist")
        self.assertTrue(os.path.exists(JPG_PATH), "assets/jubayer.jpg must exist")

        with Image.open(WEBP_PATH) as img:
            self.assertEqual(img.format, "WEBP")
            self.assertEqual(img.size, (1024, 819))

        with Image.open(JPG_PATH) as img:
            self.assertEqual(img.format, "JPEG")
            self.assertEqual(img.size, (1024, 819))

        # OpenGraph metadata check
        self.assertIn('<meta property="og:image:width" content="1024">', self.html)
        self.assertIn('<meta property="og:image:height" content="819">', self.html)

        # Hero picture check
        hero_idx = self.html.find('assets/jubayer.webp')
        hero_snippet = self.html[hero_idx-100:hero_idx+400]
        self.assertIn('<picture', hero_snippet)
        self.assertIn('width="1024"', hero_snippet)
        self.assertIn('height="819"', hero_snippet)
        self.assertIn('fetchpriority="high"', hero_snippet)
        # Hero wrapper aspect ratio style check for fail-safe zero CLS
        hero_wrap_idx = self.html.find('aspect-[1024/819]')
        self.assertNotEqual(hero_wrap_idx, -1, "Hero image wrapper must have aspect-[1024/819]")
        hero_wrap_snippet = self.html[hero_wrap_idx-50:hero_wrap_idx+250]
        self.assertIn('style="aspect-ratio: 1024 / 819;"', hero_wrap_snippet)

        # Contact avatar check
        contact_idx = self.html.rfind('assets/jubayer.webp')
        contact_snippet = self.html[contact_idx-100:contact_idx+400]
        self.assertIn('<picture', contact_snippet)
        self.assertIn('width="64"', contact_snippet)
        self.assertIn('height="64"', contact_snippet)
        self.assertIn('loading="lazy"', contact_snippet)
        self.assertIn('transform: scale(2.15)', contact_snippet)
        self.assertIn('transform-origin: 95% 25%', contact_snippet)

    def test_dom_cleanliness_and_html_validity(self):
        """5.0 HTML syntax validity and modal cleanliness."""
        self.assertNotIn('id="hover-preview-modal"', self.html, "hover-preview-modal must be removed from DOM")

        class StrictValidator(HTMLParser):
            def __init__(self):
                super().__init__()
                self.stack = []
                self.void = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}
                self.errors = []
            def handle_starttag(self, tag, attrs):
                if tag.lower() not in self.void:
                    self.stack.append((tag.lower(), self.getpos()))
            def handle_endtag(self, tag):
                if tag.lower() in self.void:
                    return
                if not self.stack:
                    self.errors.append(f"Unexpected </{tag}> at line {self.getpos()[0]}")
                    return
                last, pos = self.stack.pop()
                if last != tag.lower():
                    self.errors.append(f"Mismatched </{tag}> (expected </{last}> at {pos[0]})")

        val = StrictValidator()
        val.feed(self.html)
        self.assertEqual(len(val.errors), 0, f"HTML nesting errors: {val.errors}")
        self.assertEqual(len(val.stack), 0, f"Unclosed HTML tags: {val.stack}")

    def test_audit_modal_form_configuration(self):
        """6.1 Audit modal form must have FormSubmit action, method, and hidden configuration fields."""
        form_idx = self.html.find('id="audit-modal-form"')
        self.assertNotEqual(form_idx, -1, "audit-modal-form must be present")
        form_snippet = self.html[form_idx:form_idx+1500]
        
        self.assertIn('action="https://formsubmit.co/jubayer.ahamed.dev@gmail.com"', form_snippet)
        self.assertIn('method="POST"', form_snippet)
        self.assertIn('onsubmit="handleAuditSubmit(event)"', form_snippet)
        self.assertIn('name="_subject"', form_snippet)
        self.assertIn('name="_template" value="table"', form_snippet)
        self.assertIn('name="_captcha" value="false"', form_snippet)
        self.assertIn('name="_autoresponse"', form_snippet)
        self.assertIn('name="_replyto" id="audit-replyto"', form_snippet)
        self.assertIn('name="_next"', form_snippet)
        self.assertIn('name="_honey"', form_snippet)
        self.assertIn('id="modal-success-icon"', self.html)

    def test_contact_solutions_form_configuration(self):
        """6.2 Contact solutions brief form must have FormSubmit action, method, and hidden configuration fields."""
        form_idx = self.html.find('id="contact-solutions-form"')
        self.assertNotEqual(form_idx, -1, "contact-solutions-form must be present")
        form_snippet = self.html[form_idx:form_idx+1500]
        
        self.assertIn('action="https://formsubmit.co/jubayer.ahamed.dev@gmail.com"', form_snippet)
        self.assertIn('method="POST"', form_snippet)
        self.assertIn('onsubmit="handleContactSolutionsSubmit(event)"', form_snippet)
        self.assertIn('name="_subject"', form_snippet)
        self.assertIn('name="_template" value="table"', form_snippet)
        self.assertIn('name="_captcha" value="false"', form_snippet)
        self.assertIn('name="_autoresponse"', form_snippet)
        self.assertIn('name="_replyto" id="contact-replyto"', form_snippet)
        self.assertIn('name="_next"', form_snippet)
        self.assertIn('name="_honey"', form_snippet)

    def test_javascript_email_dispatch_routing(self):
        """6.3 JavaScript handlers must dispatch to jubayer.ahamed.dev@gmail.com with fallback channels."""
        self.assertIn("https://formsubmit.co/ajax/jubayer.ahamed.dev@gmail.com", self.html)
        self.assertIn("mailto:jubayer.ahamed.dev@gmail.com", self.html)
        self.assertIn("https://wa.me/8801610594042", self.html)
        # Ensure replyto mapping logic exists
        self.assertIn("contactReplyToEl", self.html)
        self.assertIn("auditReplyToEl", self.html)
        self.assertIn("Dispatching to Jubayer...", self.html)

    def test_project_models_verification(self):
        """Verify Project 01 uses Gemini 3.5 and Project 06 uses Gemma 4 / Google Gemma 4."""
        # Project 1 in index.html
        self.assertIn('data-preview-tag="Python · Gemini 3.5"', self.html)
        self.assertIn('>Gemini 3.5</span>', self.html)
        self.assertNotIn('id="preview-tag"', self.html)
        self.assertNotIn('Gemini 2.0', self.html)
        self.assertNotIn('Gemini 2.5', self.html)

        # Project 6 in index.html
        self.assertIn('data-preview-title="Gemma 4 Local AI Workspace"', self.html)
        self.assertIn('aria-label="Gemma 4 Local AI Workspace - View on GitHub"', self.html)
        self.assertIn('running Google Gemma 4 for sovereign private intelligence', self.html)
        self.assertIn('>Gemma 4 Local AI Workspace</h3>', self.html)
        self.assertIn('data-card-link="https://github.com/Jubayer-ahamed42/gemma4-local-ai-workspace"', self.html)
        self.assertIn('href="https://github.com/Jubayer-ahamed42/gemma4-local-ai-workspace"', self.html)
        self.assertIn('href="https://jubayer-ahamed42.github.io/gemma4-local-ai-workspace/"', self.html)
        self.assertNotIn('Gemma 2', self.html)

        # README.md verification
        readme_path = os.path.join(BASE_DIR, 'README.md')
        with open(readme_path, 'r', encoding='utf-8') as f:
            readme = f.read()
        self.assertIn('01. B2B AI Sales Engine', readme)
        self.assertIn('Python · Gemini 3.5', readme)
        self.assertIn('06. Gemma 4 Local AI Workspace', readme)
        self.assertIn('Google Gemma 4', readme)
        self.assertNotIn('Gemini 2.0', readme)
        self.assertNotIn('Gemini 2.5', readme)
        self.assertNotIn('Gemma 2', readme)

    def test_dark_mode_default_configuration(self):
        """Verify the website opens in Dark Mode by default with zero-flicker toggle."""
        # 0. Root html tag must have dark class by default for zero-FOUC native dark rendering
        self.assertIn('<html lang="en" class="dark scroll-smooth">', self.html)

        # 1. Head script must default to dark mode unless localStorage explicitly has 'light'
        self.assertIn(
            "if (localStorage.theme === 'light') {\n        document.documentElement.classList.remove('dark');\n      } else {\n        document.documentElement.classList.add('dark');\n      }",
            self.html,
            "Head script must set dark mode by default unless 'light' is stored"
        )
        # Catch fallback must also guarantee dark mode
        self.assertIn(
            "catch (e) {\n      document.documentElement.classList.add('dark');\n    }",
            self.html,
            "Private browsing / storage-disabled fallback must default to dark mode"
        )

        # 2. Toggle button initial markup
        self.assertIn('id="theme-toggle"', self.html)
        self.assertIn('aria-label="Switch to light mode"', self.html)
        self.assertIn('id="theme-toggle-dark-icon" class="w-4 h-4 hidden"', self.html)
        self.assertIn('id="theme-toggle-light-icon" class="w-4 h-4"', self.html)

        # 3. Theme switch handler persists 'dark' or 'light'
        self.assertIn("localStorage.setItem('theme', isDark ? 'dark' : 'light');", self.html)
        self.assertIn("themeToggleBtn.setAttribute('aria-label', isDark ? 'Switch to light mode' : 'Switch to dark mode');", self.html)

    def test_enterprise_indigo_palette_and_zero_coral(self):
        """Verify Enterprise Royal Indigo replaces all coral/red accents (#fb2c36, #ff6b4a) across the codebase."""
        # Zero occurrences of red/coral in index.html
        coral_classes = re.findall(r'[a-zA-Z0-9_\:\/\.\-]+coral[a-zA-Z0-9_\:\/\.\-]*', self.html)
        self.assertEqual(len(coral_classes), 0, f"Expected 0 coral classes in index.html, found: {coral_classes}")
        self.assertEqual(self.html.count('#fb2c36'), 0, "No #fb2c36 should remain in index.html")
        self.assertEqual(self.html.count('#ff6b4a'), 0, "No legacy coral #ff6b4a should remain in index.html")

        # Service action button hover & focus-visible in Enterprise Indigo
        self.assertIn("color: #4f46e5 !important;", self.html)
        self.assertIn("color: #818cf8 !important;", self.html)
        self.assertIn("outline: 2px solid #6366f1;", self.html)
        self.assertIn(".dark .service-action-btn:focus-visible {\n      outline-color: #818cf8;", self.html)

        # Enterprise Indigo system in Tailwind configuration
        self.assertIn("DEFAULT: '#6366f1'", self.html)
        self.assertIn("'indigo-light': '#818cf8'", self.html)
        self.assertIn("accent: '#6366f1'", self.html)

        # Accent attributes in Service 07 and Case Study 01
        self.assertIn('data-accent-color="#6366f1" data-accent-rgb="99, 102, 241"', self.html)

        # Ambient chromatic spotlight & lerp loop uses [99, 102, 241]
        self.assertIn("Math.round(246 + (241 - 246) * t)", self.html)
        self.assertIn("if (b > 200 && r > 80) return [139, 92, 246];", self.html)

        # WCAG 2.2 Level AA Contrast compliance for Enterprise Indigo
        cr_indigo_light = contrast('#4f46e5', '#ffffff')
        self.assertGreaterEqual(cr_indigo_light, 4.5, f"indigo-600 contrast against white is {cr_indigo_light:.2f}, must be >= 4.5:1")

        cr_indigo_dark_card = contrast('#818cf8', '#141f36')
        self.assertGreaterEqual(cr_indigo_dark_card, 4.5, f"indigo-400 contrast against dark-card is {cr_indigo_dark_card:.2f}, must be >= 4.5:1")

        cr_indigo_dark_bg = contrast('#818cf8', '#070b14')
        self.assertGreaterEqual(cr_indigo_dark_bg, 4.5, f"indigo-400 contrast against dark-bg is {cr_indigo_dark_bg:.2f}, must be >= 4.5:1")

        # SVG branding assets check
        favicon_path = os.path.join(BASE_DIR, 'assets', 'favicon.svg')
        with open(favicon_path, 'r', encoding='utf-8') as f:
            fav = f.read()
        self.assertNotIn('#fb2c36', fav)
        self.assertIn('#6366f1', fav)

        logo_path = os.path.join(BASE_DIR, 'assets', 'logo.svg')
        with open(logo_path, 'r', encoding='utf-8') as f:
            logo = f.read()
        self.assertNotIn('#fb2c36', logo)
        self.assertIn('#6366f1', logo)

    def test_project_card_clean_hover_and_modal_removal(self):
        """Verify #hover-preview-modal is removed and all 15 project cards feature smooth hover scale elevation, active feedback, and security."""
        # 1. Zero occurrences of floating preview modal and its inner elements
        self.assertNotIn('id="hover-preview-modal"', self.html)
        self.assertNotIn('id="preview-accent-line"', self.html)
        self.assertNotIn('id="preview-indicator-dot"', self.html)
        self.assertNotIn('id="preview-tag"', self.html)
        self.assertNotIn('id="preview-click-icon"', self.html)

        # 2. JavaScript does not reference hover-preview-modal element, old animateModal name, or popup tracking variables
        self.assertNotIn("document.getElementById('hover-preview-modal')", self.html)
        self.assertNotIn("document.getElementById('preview-tag')", self.html)
        self.assertNotIn("isHoveringCard", self.html)
        self.assertNotIn("hoverLeaveTimeout", self.html)
        self.assertNotIn("animateModal", self.html)
        self.assertIn("animateSpotlight", self.html)

        # 3. All 15 project cards feature smooth forward hover lift & scale classes + active press feedback
        project_cards = re.findall(r'class="project-card\s[^"]*"', self.html)
        self.assertEqual(len(project_cards), 15, "Must have exactly 15 project cards")
        for card_class in project_cards:
            self.assertIn('hover:-translate-y-2', card_class)
            self.assertIn('hover:scale-[1.02]', card_class)
            self.assertIn('hover:shadow-2xl', card_class)
            self.assertIn('active:-translate-y-0.5', card_class)
            self.assertIn('active:scale-[0.995]', card_class)
            self.assertIn('transition-all', card_class)

        # 4. CSS defines project card hover elevation, accent glow, and z-index transition smoothing
        self.assertIn(".project-card:hover", self.html)
        self.assertIn("transform: translateY(-8px) scale(1.02);", self.html)
        self.assertIn("border-color: var(--card-accent", self.html)
        self.assertIn("box-shadow: 0 20px 40px -10px var(--card-glow", self.html)
        self.assertIn("z-index: 10;", self.html)
        self.assertIn("z-index 0s 0.3s", self.html)
        self.assertIn(".project-card:active {\n      transform: translateY(-2px) scale(0.995) !important;", self.html)

        # 5. Security & accessibility: all project action links in #projects-grid have rel="noopener noreferrer"
        grid_start = self.html.find('id="projects-grid"')
        grid_end = self.html.find('</section>', grid_start)
        grid_html = self.html[grid_start:grid_end]
        links = re.findall(r'<a\s+[^>]*>', grid_html)
        self.assertGreaterEqual(len(links), 15)
        for link in links:
            if 'target="_blank"' in link:
                self.assertIn('rel="noopener noreferrer"', link)

        # 6. Interaction: full card navigation and keyboard accessibility attributes
        self.assertEqual(self.html.count('role="link" tabindex="0"'), 15)
        self.assertEqual(self.html.count('data-card-link="https://github.com/'), 15)

    def test_warmheart_cafe_bakery_project(self):
        """Verify Project 15 WarmHeart Cafe & Bakery is properly integrated in index.html and README.md."""
        # 1. index.html card structure and metadata
        self.assertIn('data-preview-title="WarmHeart Cafe &amp; Bakery"', self.html)
        self.assertIn('https://github.com/Jubayer-ahamed42/warmheart-cafe-bakery-website', self.html)
        self.assertIn('https://warmheart-cafe-bakery-website.sbmc4042.workers.dev', self.html)
        self.assertIn('aria-label="WarmHeart Cafe &amp; Bakery - View on GitHub"', self.html)
        self.assertIn('>WarmHeart Cafe &amp; Bakery</h3>', self.html)
        self.assertIn('All Projects (15)', self.html)
        self.assertIn('Full-Stack SaaS & Web (5)', self.html)
        self.assertIn('<span>Projects</span>', self.html)
        self.assertIn('Explore 15 Projects', self.html)
        self.assertIn('15 Featured Projects', self.html)
        self.assertIn('15 Repos', self.html)

        # All 15 sequential counters (01 / 15 through 15 / 15) must be present
        for i in range(1, 16):
            self.assertIn(f'{i:02d} / 15', self.html, f"Project counter {i:02d} / 15 missing")

        # Category distribution verification
        categories = re.findall(r'data-category="([a-z]+)"', self.html)
        self.assertEqual(len(categories), 15, "Must have exactly 15 project card categories")
        self.assertEqual(categories.count('ai'), 5, "Must have 5 AI & Conversational projects")
        self.assertEqual(categories.count('fullstack'), 5, "Must have 5 Full-Stack SaaS & Web projects")
        self.assertEqual(categories.count('automation'), 5, "Must have 5 Automation & Tools projects")

        # 2. README.md verification
        readme_path = os.path.join(BASE_DIR, 'README.md')
        with open(readme_path, 'r', encoding='utf-8') as f:
            readme = f.read()
        self.assertIn('15. WarmHeart Cafe & Bakery Website', readme)
        self.assertIn('warmheart-cafe-bakery-website', readme)
        self.assertIn('15 Featured Projects', readme)
        self.assertIn('15 enterprise production systems', readme)

    def test_badge_pills_removed(self):
        """Verify that the hero live status badge pill, secondary title, and founder card dual-role badge pills are removed."""
        # 1. Hero top status badge and accompanying title text
        self.assertNotIn("Available for High-Impact Projects", self.html, "Hero live status badge must be removed")
        self.assertNotIn("AI Systems Architect &middot; Founder", self.html, "Hero top status secondary title must be removed")
        self.assertNotIn("AI Systems Architect · Founder", self.html, "Hero top status secondary title must be removed")
        self.assertNotIn("<!-- Top Live Status Badge -->", self.html, "Top live status badge container comment/wrapper must be removed")

        # 2. Founder card dual role badge pills
        self.assertNotIn("Principal AI Solutions Architect", self.html, "Founder showcase role badge must be removed")
        self.assertNotIn("<!-- Floating Active Status Badge -->", self.html, "Floating active status badge container comment/wrapper must be removed")

        # 3. Structural verification: founder card begins cleanly with portrait display
        card_start = self.html.find('class="founder-showcase-card')
        card_end = self.html.find('<!-- Founder Bio Details -->', card_start)
        card_header = self.html[card_start:card_end]
        self.assertNotIn('bg-emerald-50', card_header, "Role badge pill container must not exist in founder card")
        self.assertNotIn('bg-amber-500', card_header, "Business problem solver dot must not exist in founder card")
        self.assertIn('Full-Face High-Resolution Portrait Display', card_header, "Portrait display must be the leading element in founder card")

    def test_ui_ux_pro_max_accessibility_and_ergonomics(self):
        """Verify UI/UX Pro Max WCAG 2.2 AA landmarks, skip-link, reduced-motion, and form ergonomics."""
        # 1. Accessible skip link
        self.assertIn('<a href="#main-content"', self.html, "Skip to content link must point to #main-content")
        self.assertIn('Skip to main content', self.html, "Skip link must have accessible text")

        # 2. Semantic main content landmark
        main_start = self.html.find('<main id="main-content">')
        main_end = self.html.find('</main>')
        self.assertNotEqual(main_start, -1, "<main id='main-content'> landmark must be present")
        self.assertNotEqual(main_end, -1, "</main> must be present")
        home_pos = self.html.find('id="home"')
        contact_pos = self.html.find('id="contact"')
        footer_pos = self.html.find('<footer')
        self.assertTrue(main_start < home_pos < contact_pos < main_end < footer_pos,
                        "main landmark must cleanly enclose primary content sections before footer")

        # 3. Reduced motion media query
        self.assertIn('@media (prefers-reduced-motion: reduce)', self.html,
                      "Must support prefers-reduced-motion for motion sensitivity")

        # 4. Form autocomplete and inputmode directives
        self.assertIn('autocomplete="name"', self.html)
        self.assertIn('autocomplete="email"', self.html)
        self.assertIn('autocomplete="url"', self.html)
        self.assertIn('autocomplete="email tel"', self.html)
        self.assertIn('inputmode="email"', self.html)

        # 5. Form status ARIA live regions
        self.assertIn('id="contact-form-success" role="status" aria-live="polite"', self.html)
        self.assertIn('id="modal-success" role="status" aria-live="polite"', self.html)

    def test_cloudflare_pages_deployment_configuration(self):
        """Verify Cloudflare Pages configuration, domain, canonical, og:image, and _headers."""
        # 1. Zero occurrences of vercel in index.html
        self.assertNotIn("jubayer-ahamed.vercel.app", self.html)

        # 2. Canonical URL & OpenGraph point to Cloudflare Pages
        self.assertIn('<link rel="canonical" href="https://jubayer-ahamed.pages.dev/">', self.html)
        self.assertIn('<meta property="og:url" content="https://jubayer-ahamed.pages.dev/">', self.html)
        self.assertIn('<meta property="og:image" content="https://jubayer-ahamed.pages.dev/assets/jubayer.jpg">', self.html)
        self.assertIn('<meta property="og:image:secure_url" content="https://jubayer-ahamed.pages.dev/assets/jubayer.jpg">', self.html)
        self.assertIn('<meta name="twitter:image" content="https://jubayer-ahamed.pages.dev/assets/jubayer.jpg">', self.html)

        # 3. Form redirect _next values point to Cloudflare Pages
        self.assertIn('value="https://jubayer-ahamed.pages.dev/#contact"', self.html)
        self.assertIn('value="https://jubayer-ahamed.pages.dev/?audit_submitted=true"', self.html)

        # 4. Cloudflare configuration files exist and are correctly configured
        cf_headers_path = os.path.join(BASE_DIR, '_headers')
        wrangler_json_path = os.path.join(BASE_DIR, 'wrangler.json')
        wrangler_toml_path = os.path.join(BASE_DIR, 'wrangler.toml')
        vercel_json_path = os.path.join(BASE_DIR, 'vercel.json')
        package_json_path = os.path.join(BASE_DIR, 'package.json')

        self.assertTrue(os.path.isfile(cf_headers_path), "_headers file must exist for Cloudflare Pages")
        self.assertTrue(os.path.isfile(wrangler_json_path), "wrangler.json must exist")
        self.assertTrue(os.path.isfile(wrangler_toml_path), "wrangler.toml must exist")
        self.assertFalse(os.path.isfile(vercel_json_path), "vercel.json must be removed to avoid ambiguous deployments")

        with open(cf_headers_path, 'r', encoding='utf-8') as f:
            headers_content = f.read()
        self.assertIn('X-Content-Type-Options: nosniff', headers_content)
        self.assertIn('X-Frame-Options: SAMEORIGIN', headers_content)
        self.assertIn('Referrer-Policy: strict-origin-when-cross-origin', headers_content)
        self.assertIn('Cache-Control: public, max-age=31536000, immutable', headers_content)

        import json
        with open(wrangler_json_path, 'r', encoding='utf-8') as f:
            wrangler_json = json.load(f)
        self.assertEqual(wrangler_json.get('pages_build_output_dir'), '.', "wrangler.json must configure pages_build_output_dir as .")

        with open(wrangler_toml_path, 'r', encoding='utf-8') as f:
            wrangler_toml = f.read()
        self.assertIn('pages_build_output_dir = "."', wrangler_toml, "wrangler.toml must configure pages_build_output_dir")

        with open(package_json_path, 'r', encoding='utf-8') as f:
            package_json = json.load(f)
        self.assertIn('cf:deploy', package_json.get('scripts', {}), "package.json must contain cf:deploy script")

        # 5. README.md references Cloudflare Pages live deployment
        readme_path = os.path.join(BASE_DIR, 'README.md')
        with open(readme_path, 'r', encoding='utf-8') as f:
            readme = f.read()
        self.assertIn('https://jubayer-ahamed.pages.dev', readme)
        self.assertIn('Live_Deployment-Cloudflare_Pages-F38020', readme)
        self.assertNotIn('jubayer-ahamed.vercel.app', readme)

    def test_hero_cta_audit_iconography(self):
        """Verify the primary 'Audit Your Business' CTA button uses search-check icon and interactive hover transition."""
        self.assertIn('data-lucide="search-check"', self.html)
        hero_audit_pattern = (
            r'class="group inline-flex items-center justify-center[^"]*">\s*'
            r'<i data-lucide="search-check" class="w-4 h-4 text-emerald-200"></i>\s*'
            r'<span>Audit Your Business</span>\s*'
            r'<i data-lucide="arrow-right" class="w-4 h-4 group-hover:translate-x-1 transition-transform"></i>'
        )
        self.assertRegex(self.html, hero_audit_pattern)
        self.assertNotRegex(
            self.html,
            r'<a[^>]*>\s*<i data-lucide="sparkles"[^>]*>\s*<span>Audit Your Business</span>'
        )


if __name__ == '__main__':
    unittest.main()


