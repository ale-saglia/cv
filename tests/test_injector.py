from injector import inject_secrets_in_cv, strip_placeholders, yaml_scalar


class TestYamlScalar:
    def test_simple_string(self):
        assert yaml_scalar("hello") == "'hello'"

    def test_string_with_apostrophe(self):
        assert yaml_scalar("it's") == "'it''s'"

    def test_empty_string(self):
        assert yaml_scalar("") == "''"

    def test_integer(self):
        assert yaml_scalar(42) == "42"

    def test_newline_normalized_to_space(self):
        result = yaml_scalar("line1\nline2")
        assert "\n" not in result
        assert "line1 line2" in result


class TestInjectSecrets:
    def test_placeholder_substituted(self, tmp_path):
        t = tmp_path / "cv.yaml"
        t.write_text("cv:\n  email: ${SECRET_EMAIL}\n  name: Test\n", encoding="utf-8")
        out = inject_secrets_in_cv(t, {"email": "user@example.com"})
        content = out.read_text(encoding="utf-8")
        assert "${SECRET_EMAIL}" not in content
        assert "user@example.com" in content

    def test_empty_field_filled_from_secrets(self, tmp_path):
        t = tmp_path / "cv.yaml"
        t.write_text("cv:\n  phone: \n  name: Test\n", encoding="utf-8")
        out = inject_secrets_in_cv(t, {"phone": "+39000000000"})
        assert "+39000000000" in out.read_text(encoding="utf-8")

    def test_missing_secret_leaves_placeholder(self, tmp_path):
        t = tmp_path / "cv.yaml"
        t.write_text("cv:\n  email: ${SECRET_EMAIL}\n", encoding="utf-8")
        out = inject_secrets_in_cv(t, {})
        assert "${SECRET_EMAIL}" in out.read_text(encoding="utf-8")

    def test_partial_secrets(self, tmp_path):
        t = tmp_path / "cv.yaml"
        t.write_text(
            "cv:\n  email: ${SECRET_EMAIL}\n  phone: ${SECRET_PHONE}\n",
            encoding="utf-8",
        )
        out = inject_secrets_in_cv(t, {"email": "user@example.com"})
        content = out.read_text(encoding="utf-8")
        assert "${SECRET_EMAIL}" not in content
        assert "${SECRET_PHONE}" in content

    def test_trailing_newline_preserved(self, tmp_path):
        t = tmp_path / "cv.yaml"
        t.write_text("cv:\n  name: Test\n", encoding="utf-8")
        out = inject_secrets_in_cv(t, {})
        assert out.read_text(encoding="utf-8").endswith("\n")

    def test_non_cv_fields_not_touched(self, tmp_path):
        t = tmp_path / "cv.yaml"
        t.write_text("other:\n  email: \ncv:\n  name: Test\n", encoding="utf-8")
        out = inject_secrets_in_cv(t, {"email": "injected@example.com"})
        content = out.read_text(encoding="utf-8")
        lines = content.splitlines()
        other_email_line = next((l for l in lines if "other:" in l or (lines.index(l) < lines.index("cv:") if "cv:" in lines else False)), None)
        # The field under `other:` must not be injected
        assert content.index("other:") < content.index("cv:")


class TestStripPlaceholders:
    def test_secret_lines_removed(self, tmp_path):
        t = tmp_path / "cv.yaml"
        t.write_text("cv:\n  email: ${SECRET_EMAIL}\n  name: Test\n", encoding="utf-8")
        out = strip_placeholders(t, announce=False)
        content = out.read_text(encoding="utf-8")
        assert "${SECRET_EMAIL}" not in content
        assert "name: Test" in content

    def test_non_secret_lines_kept(self, tmp_path):
        t = tmp_path / "cv.yaml"
        t.write_text("cv:\n  name: Test\n  website: https://example.com\n", encoding="utf-8")
        out = strip_placeholders(t, announce=False)
        content = out.read_text(encoding="utf-8")
        assert "name: Test" in content
        assert "website: https://example.com" in content

    def test_trailing_newline_preserved(self, tmp_path):
        t = tmp_path / "cv.yaml"
        t.write_text("cv:\n  name: Test\n", encoding="utf-8")
        out = strip_placeholders(t, announce=False)
        assert out.read_text(encoding="utf-8").endswith("\n")

    def test_multiple_placeholders_all_removed(self, tmp_path):
        t = tmp_path / "cv.yaml"
        t.write_text(
            "cv:\n  email: ${SECRET_EMAIL}\n  phone: ${SECRET_PHONE}\n  name: Test\n",
            encoding="utf-8",
        )
        out = strip_placeholders(t, announce=False)
        content = out.read_text(encoding="utf-8")
        assert "${SECRET_EMAIL}" not in content
        assert "${SECRET_PHONE}" not in content
        assert "name: Test" in content
