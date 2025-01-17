from pathlib import Path

import arrow
import pytest

from virtool.example import example_path as virtool_example_path


class MockRequest:
    def __init__(self):
        self.app = {}
        self._state = {}

    def __getitem__(self, key):
        return self._state.get(key)

    def __setitem__(self, key, value):
        self._state[key] = value


class StaticTime:
    datetime = arrow.Arrow(2015, 10, 6, 20, 0, 0).naive
    iso = "2015-10-06T20:00:00Z"


@pytest.fixture
def mock_req():
    return MockRequest()


@pytest.fixture
def test_files_path():
    return Path(__file__).parent.parent / "test_files"


@pytest.fixture
def test_random_alphanumeric(mocker):
    class RandomAlphanumericTester:
        def __init__(self):
            self.choices = [
                "aB67nm89jL56hj34AL90",
                "fX1l90Rt45JK34bA7890",
                "kl84Fg067jJa109lmQ021",
                "yGlirXr7TSv4x6byFLUJ",
                "G5cPJjvKH7g9lB9tpb3Q",
                "v4xrYERY71lJD1JbIdcX",
                "KfVw9vD27KGMly2qf45K",
                "xjQVxIGHKsTQrVisJiKo",
                "U3cuWAoQ3TDsy0wU7z0l",
                "9PfsOM1B99KfaMz2Wu3C",
            ]

            self.history = []

            self.last_choice = None

        def __call__(self, length=6, mixed_case=False, excluded=None):
            string = self.choices.pop()[:length]

            if not mixed_case:
                string = string.lower()

            excluded = excluded or []

            if string in excluded:
                string = self.__call__(length, mixed_case, excluded)

            self.history.append(string)
            self.last_choice = string

            return string

        @property
        def next_choice(self):
            return self.choices[-1]

    return mocker.patch(
        "virtool.utils.random_alphanumeric", new=RandomAlphanumericTester()
    )


@pytest.fixture(scope="session")
def static_time_obj():
    return StaticTime()


@pytest.fixture
def static_time(mocker, static_time_obj):
    mocker.patch("virtool.utils.timestamp", return_value=static_time_obj.datetime)
    return static_time_obj


def get_sam_lines():
    path = Path(__file__).parent.parent / "test_files" / "sam_50.sam"

    with open(path, "r") as handle:
        return handle.read().split("\n")[0:-1]


@pytest.fixture
def example_path():
    return virtool_example_path
