from injector import inject_secrets_in_cv, safe_remove, strip_placeholders, yaml_scalar


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

class TestInjectSecretsOutput:
    def test_fallback_logs_count_not_key_names(self, tmp_path, capsys):
        t = tmp_path / "cv.yaml"
        t.write_text("cv:\n  phone: \n  email: \n  name: Test\n", encoding="utf-8")
        inject_secrets_in_cv(t, {"phone": "+39000000000", "email": "x@y.com"})
        out = capsys.readouterr().out
        assert "2" in out
        assert "phone" not in out
        assert "email" not in out

    def test_missing_keys_logs_count_not_key_names(self, tmp_path, capsys):
        t = tmp_path / "cv.yaml"
        t.write_text("cv:\n  email: ${SECRET_EMAIL}\n  phone: ${SECRET_PHONE}\n", encoding="utf-8")
        inject_secrets_in_cv(t, {})
        out = capsys.readouterr().out
        assert "2" in out
        assert "email" not in out
        assert "phone" not in out


class TestSafeRemove:
    def test_cleanup_error_does_not_log_path_or_exception(self, tmp_path, capsys):
        secret_path = tmp_path / "secret-cv.yaml"

        class UnremovablePath:
            def exists(self):
                return True

            def unlink(self):
                raise OSError(f"cannot remove {secret_path}")

        safe_remove(UnremovablePath())

        captured = capsys.readouterr()
        assert "Could not remove temporary file." in captured.err
        assert str(secret_path) not in captured.err
        assert "cannot remove" not in captured.err

