from typing import Any, Optional


class ContextManagerMock:
    def __enter__(self) -> "ContextManagerMock":
        return self

    def __exit__(self, *args: Any, **kwargs: Any) -> None:
        return


class URLOpenMock(ContextManagerMock):
    def __init__(self, data: bytes=b"", exception: Exception=None) -> None:
        self._data = data
        self._exception = exception

    def read(self, amt: Optional[int]=None) -> bytes:
        if self._exception:
            raise self._exception  # pylint: disable=raising-bad-type
        return self._data[:amt or len(self._data)]
