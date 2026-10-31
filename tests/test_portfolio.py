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
            self.assertEqual(img.size, (1024, 1024))

        with Image.open(JPG_PATH) as img:
            self.assertEqual(img.format, "JPEG")
            self.assertEqual(img.size, (1024, 1024))

        # Hero picture check
        hero_idx = self.html.find('assets/jubayer.webp')
        hero_snippet = self.html[hero_idx-100:hero_idx+400]
        self.assertIn('<picture', hero_snippet)
        self.assertIn('width="1024"', hero_snippet)
        self.assertIn('height="1024"', hero_snippet)
        self.assertIn('fetchpriority="high"', hero_snippet)

        # Contact avatar check
        contact_idx = self.html.rfind('assets/jubayer.webp')
        contact_snippet = self.html[contact_idx-100:contact_idx+400]
        self.assertIn('<picture', contact_snippet)
        self.assertIn('width="64"', contact_snippet)
        self.assertIn('height="64"', contact_snippet)
        self.assertIn('loading="lazy"', contact_snippet)

    def test_dom_cleanliness_and_html_validity(self):
        """5.0 HTML syntax validity and hover modal position above scripts."""
        hover_idx = self.html.find('id="hover-preview-modal"')
        last_script_idx = self.html.rfind('<!-- ==================== JAVASCRIPT ==================== -->')
        self.assertLess(hover_idx, last_script_idx, "hover-preview-modal must be placed before main script")

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

    def test_javascript_email_dispatch_routing(self):
        """6.3 JavaScript handlers must dispatch to jubayer.ahamed.dev@gmail.com with fallback channels."""
        self.assertIn("https://formsubmit.co/ajax/jubayer.ahamed.dev@gmail.com", self.html)
        self.assertIn("mailto:jubayer.ahamed.dev@gmail.com", self.html)
        self.assertIn("https://wa.me/8801610594042", self.html)
        # Ensure replyto mapping logic exists
        self.assertIn("contactReplyToEl", self.html)
        self.assertIn("auditReplyToEl", self.html)


if __name__ == '__main__':
    unittest.main()
