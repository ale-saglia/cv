from generate_index import format_date_range, slugify, md_to_html_inline

IT_MONTHS = ["Gen", "Feb", "Mar", "Apr", "Mag", "Giu", "Lug", "Ago", "Set", "Ott", "Nov", "Dic"]
EN_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


class TestFormatDateRange:
    def test_range_it(self):
        assert format_date_range("2021-08", "2025-11", "it", IT_MONTHS) == "Ago 2021 - Nov 2025"

    def test_range_en(self):
        assert format_date_range("2019-08", "2021-07", "en", EN_MONTHS) == "Aug 2019 - Jul 2021"

    def test_end_present_it(self):
        assert format_date_range("2025-12", "present", "it", IT_MONTHS) == "Dic 2025 - in corso"

    def test_end_present_en(self):
        assert format_date_range("2025-12", "present", "en", EN_MONTHS) == "Dec 2025 - ongoing"

    def test_end_none_treated_as_present(self):
        result = format_date_range("2025-12", None, "it", IT_MONTHS)
        assert result == "Dic 2025 - in corso"

    def test_no_month_abbrs_returns_raw(self):
        assert format_date_range("2021-08", "2025-11", "it", []) == "2021-08 - 2025-11"

    def test_only_start_no_end(self):
        result = format_date_range("2021-08", None, "it", IT_MONTHS)
        assert "Ago 2021" in result

    def test_empty_start(self):
        result = format_date_range("", "2025-11", "it", IT_MONTHS)
        assert "Nov 2025" in result


class TestSlugify:
    def test_basic_lowercase_and_space(self):
        assert slugify("Esperienza lavorativa") == "esperienza-lavorativa"

    def test_uppercase(self):
        assert slugify("HELLO WORLD") == "hello-world"

    def test_multiple_spaces_collapsed(self):
        assert slugify("a  b   c") == "a-b-c"

    def test_special_chars_removed(self):
        assert slugify("Volontariato & Progetti") == "volontariato-progetti"

    def test_leading_trailing_dash_stripped(self):
        assert slugify("-text-") == "text"

    def test_empty_string(self):
        assert slugify("") == ""


class TestMdToHtmlInline:
    def test_bold(self):
        assert md_to_html_inline("**testo**") == "<strong>testo</strong>"

    def test_italic(self):
        assert md_to_html_inline("*testo*") == "<em>testo</em>"

    def test_link(self):
        result = md_to_html_inline("[label](https://example.com)")
        assert 'href="https://example.com"' in result
        assert ">label<" in result
        assert 'target="_blank"' in result

    def test_html_escaped(self):
        assert "&lt;script&gt;" in md_to_html_inline("<script>")

    def test_bold_with_colon(self):
        result = md_to_html_inline("**Governance**: description")
        assert result == "<strong>Governance</strong>: description"

    def test_link_before_escaping(self):
        result = md_to_html_inline("[A & B](https://example.com)")
        assert "A &amp; B" in result
        assert 'href="https://example.com"' in result

    def test_plain_text_unchanged(self):
        assert md_to_html_inline("plain text") == "plain text"
