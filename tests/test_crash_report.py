
from core.crash_report import (
    NATIVE_REPORT_NAME,
    REPORT_NAME,
    enable_native_crash_log,
    format_report,
    write_crash_report,
)


def make_error():
    try:
        raise ValueError("the monster escaped")
    except ValueError as error:
        return error


def test_report_contains_the_error_and_the_system():
    report = format_report(make_error())
    assert "ValueError: the monster escaped" in report
    assert "System:" in report and "Python:" in report


def test_report_is_written_in_the_first_writable_folder(tmp_path):
    path = write_crash_report(make_error(), [tmp_path / "game"])
    assert path == tmp_path / "game" / REPORT_NAME
    assert "the monster escaped" in path.read_text(encoding="utf-8")


def test_falls_back_when_the_first_folder_is_not_writable(tmp_path):
    blocked = tmp_path / "blocked"
    blocked.write_text("a file, not a folder")  # impossible to create a folder here
    path = write_crash_report(make_error(), [blocked, tmp_path / "documents"])
    assert path == tmp_path / "documents" / REPORT_NAME


def test_returns_none_when_nothing_is_writable(tmp_path):
    blocked = tmp_path / "blocked"
    blocked.write_text("not a folder")
    assert write_crash_report(make_error(), [blocked]) is None


def test_native_crash_log_is_created_in_the_folder(tmp_path):
    folder = tmp_path / "logs"
    path = enable_native_crash_log(folder)
    assert path == folder / NATIVE_REPORT_NAME
    assert path.exists()
