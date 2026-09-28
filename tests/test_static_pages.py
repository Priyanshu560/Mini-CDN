import json
import os
import unittest
from html.parser import HTMLParser

import config


class _LinkCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.hrefs.extend(value for name, value in attrs if name == "href")


def _links(file_name):
    collector = _LinkCollector()
    with open(os.path.join(config.DATA_DIR, file_name), encoding="utf-8") as f:
        collector.feed(f.read())
    return collector.hrefs


class StaticPageTests(unittest.TestCase):
    def test_demo_page_footer_links_to_legal_pages(self):
        links = _links("index.html")
        self.assertIn("privacy.html", links)
        self.assertIn("terms.html", links)

    def test_legal_pages_exist_and_link_back(self):
        for name in ("privacy.html", "terms.html"):
            self.assertTrue(os.path.isfile(os.path.join(config.DATA_DIR, name)))
            self.assertIn("index.html", _links(name))

    def test_legal_pages_are_not_part_of_the_simulated_catalog(self):
        with open(os.path.join(config.DATA_DIR, "manifest.json"), encoding="utf-8") as f:
            names = {entry["name"] for entry in json.load(f)["files"]}
        self.assertFalse({"privacy.html", "terms.html"} & names)

    def test_demo_page_references_only_files_that_exist(self):
        class Refs(HTMLParser):
            def __init__(self):
                super().__init__()
                self.refs = []

            def handle_starttag(self, tag, attrs):
                self.refs.extend(v for k, v in attrs if k in ("src", "href") and v)

        refs = Refs()
        with open(os.path.join(config.DATA_DIR, "index.html"), encoding="utf-8") as f:
            refs.feed(f.read())
        for ref in refs.refs:
            self.assertTrue(os.path.isfile(os.path.join(config.DATA_DIR, ref)), ref)

    def test_legal_pages_have_no_unfilled_placeholders(self):
        for name in ("privacy.html", "terms.html"):
            with open(os.path.join(config.DATA_DIR, name), encoding="utf-8") as f:
                text = f.read()
            self.assertNotIn("[Add", text)
            self.assertIn("mailto:", text)

    def test_no_external_requests_in_static_pages(self):
        for name in ("index.html", "privacy.html", "terms.html", "style.css", "script.js"):
            with open(os.path.join(config.DATA_DIR, name), encoding="utf-8") as f:
                self.assertNotIn("http://", f.read())
                f.seek(0)
                self.assertNotIn("https://", f.read())


if __name__ == "__main__":
    unittest.main()
