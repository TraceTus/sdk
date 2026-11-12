"""When the Python client tries again.

The policy is pure and the jitter comes in as an argument, so every case here
is exact rather than approximate. It is the same policy as the JavaScript
client's, down to the numbers: the two SDKs behave alike on purpose, so a team
that uses both does not have to learn two sets of rules.
"""

from tracetus import RetryLimits, decide_retry
from tracetus.retry import read_retry_after

LIMITS = RetryLimits()


def ask(method="POST", status=None, retry_after_s=None, attempt=1, limits=LIMITS, random=None):
    return decide_retry(
        method=method,
        status=status,
        retry_after_s=retry_after_s,
        attempt=attempt,
        limits=limits,
        random=random or (lambda: 0.5),
    )


def test_tries_again_when_nothing_answered():
    decision = ask(status=None)

    assert decision.retry is True
    assert decision.wait_s == 0.125


def test_doubles_the_wait_on_each_attempt():
    assert ask(status=None, attempt=2).wait_s == 0.25


def test_never_waits_more_than_the_backoff_ceiling():
    decision = ask(status=None, attempt=20, limits=RetryLimits(attempts=50), random=lambda: 1.0)

    assert decision.wait_s == LIMITS.max_backoff_s


def test_waits_exactly_what_retry_after_says_on_429():
    assert ask(status=429, retry_after_s=2).wait_s == 2


def test_waits_exactly_what_retry_after_says_on_503():
    assert ask(status=503, retry_after_s=5).wait_s == 5


def test_falls_back_to_the_backoff_without_a_retry_after():
    assert ask(status=503).wait_s == 0.125


def test_stops_instead_of_sitting_on_a_wait_above_the_ceiling():
    assert ask(status=429, retry_after_s=3600).retry is False


def test_does_not_retry_a_post_answered_500():
    assert ask(method="POST", status=500).retry is False


def test_retries_a_get_answered_500():
    assert ask(method="GET", status=500).retry is True


def test_does_not_retry_a_refusal_by_contract():
    assert ask(status=422).retry is False


def test_does_not_retry_a_success():
    assert ask(status=201).retry is False


def test_stops_once_the_attempts_are_spent():
    assert ask(status=503, retry_after_s=1, attempt=3).retry is False


def test_never_retries_with_one_attempt():
    assert ask(status=None, limits=RetryLimits(attempts=1)).retry is False


def test_reads_retry_after_in_seconds():
    assert read_retry_after("12") == 12


def test_ignores_a_retry_after_that_is_not_a_count_of_seconds():
    assert read_retry_after("Wed, 21 Oct 2026 07:28:00 GMT") is None
    assert read_retry_after(None) is None
    assert read_retry_after("-1") is None
