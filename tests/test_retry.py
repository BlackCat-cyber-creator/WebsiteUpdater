import pytest
from pipeline.retry import retry, retry_call


def test_retry_success_first_attempt():
    """Verify that a successful function runs once without retries."""
    calls = 0

    @retry(max_attempts=3, initial_delay=0.01, jitter=False)
    def fast_op():
        nonlocal calls
        calls += 1
        return "success"

    res = fast_op()
    assert res == "success"
    assert calls == 1


def test_retry_recovers_after_transient_failure():
    """Verify that retry recovers after failures before max_attempts."""
    calls = 0

    @retry(max_attempts=3, initial_delay=0.01, backoff_factor=1.5, jitter=False)
    def flaky_op():
        nonlocal calls
        calls += 1
        if calls < 3:
            raise ConnectionError("Temporary network hiccup")
        return "recovered"

    res = flaky_op()
    assert res == "recovered"
    assert calls == 3


def test_retry_raises_when_retries_exhausted():
    """Verify that retry raises the final exception when attempts are exhausted."""
    calls = 0

    @retry(max_attempts=2, initial_delay=0.01, jitter=False)
    def failing_op():
        nonlocal calls
        calls += 1
        raise ValueError("Permanent invalid value")

    with pytest.raises(ValueError) as exc_info:
        failing_op()

    assert "Permanent invalid value" in str(exc_info.value)
    assert calls == 2  # max_attempts = 2


def test_retry_specific_exception():
    """Verify that retry only catches specified exceptions."""
    calls = 0

    @retry(max_attempts=3, initial_delay=0.01, exceptions=(ConnectionError,), jitter=False)
    def raises_unhandled():
        nonlocal calls
        calls += 1
        raise KeyError("Key not found")

    with pytest.raises(KeyError):
        raises_unhandled()

    assert calls == 1  # Fails immediately without retrying KeyError


def test_retry_call_helper():
    """Verify that retry_call executes callable with retries."""
    count = 0

    def target(a, b):
        nonlocal count
        count += 1
        if count < 2:
            raise TimeoutError("Timed out")
        return a + b

    val = retry_call(target, args=(10, 20), max_attempts=2, initial_delay=0.01)
    assert val == 30
    assert count == 2
