from django.test import SimpleTestCase

from conversions.i18n import language_from_header, normalize_language, translate


class ConversionI18nTests(SimpleTestCase):
    def test_normalizes_supported_browser_languages(self):
        self.assertEqual(normalize_language("pt-BR"), "pt-br")
        self.assertEqual(normalize_language("en-US"), "en")
        self.assertEqual(normalize_language("es-MX"), "es-419")
        self.assertEqual(normalize_language("fr-FR"), "pt-br")

    def test_honors_accept_language_priority(self):
        language = language_from_header("fr-FR,es-MX;q=0.9,en;q=0.8")
        self.assertEqual(language, "es-419")

    def test_translates_backend_message(self):
        self.assertEqual(
            translate("queue.unavailable", "en"),
            "The conversion service is temporarily unavailable.",
        )
