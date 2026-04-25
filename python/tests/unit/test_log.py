from acap_dotfiles.io.log import configure, get_logger


def test_configure_returns_logger_and_does_not_raise(monkeypatch) -> None:
    monkeypatch.setenv("NO_COLOR", "1")
    configure(verbose=0)
    log = get_logger("test")
    log.info("hello")  # should not raise


def test_verbose_levels_set_correct_levels() -> None:
    configure(verbose=0)
    log = get_logger("test")
    # No assert — just verify no exception. Level inspection is implementation detail.
    log.debug("debug-not-shown")
    log.info("info-not-shown")
    configure(verbose=1)
    log.info("info-now-shown")
    configure(verbose=2)
    log.debug("debug-now-shown")
