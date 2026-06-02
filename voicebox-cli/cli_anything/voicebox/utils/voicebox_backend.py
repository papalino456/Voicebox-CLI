"""HTTP adapter for the real Voicebox backend."""

from __future__ import annotations

import json
import mimetypes
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


class VoiceboxBackendError(RuntimeError):
    """Raised when the Voicebox backend rejects or fails a request."""


class VoiceboxBackend:
    """Small standard-library HTTP client for Voicebox's REST API."""

    def __init__(self, base_url: str = "http://127.0.0.1:17493", timeout: float = 30.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def request(
        self,
        method: str,
        path: str,
        *,
        query: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> Any:
        url = self._url(path, query)
        body = None
        headers = {"Accept": "application/json"}
        if json_body is not None:
            body = json.dumps(json_body).encode("utf-8")
            headers["Content-Type"] = "application/json"

        request = urllib.request.Request(url, data=body, headers=headers, method=method.upper())
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return self._decode_response(response)
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise VoiceboxBackendError(f"{method.upper()} {path} failed: {exc.code} {detail}") from exc
        except urllib.error.URLError as exc:
            raise VoiceboxBackendError(f"Cannot reach Voicebox backend at {self.base_url}: {exc.reason}") from exc

    def upload_file(
        self,
        path: str,
        *,
        file_path: str | Path,
        fields: dict[str, str] | None = None,
    ) -> Any:
        file_path = Path(file_path)
        if not file_path.is_file():
            raise VoiceboxBackendError(f"File not found: {file_path}")

        boundary = "cli-anything-voicebox-boundary"
        parts: list[bytes] = []
        for key, value in (fields or {}).items():
            parts.extend(
                [
                    f"--{boundary}\r\n".encode(),
                    f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode(),
                    str(value).encode(),
                    b"\r\n",
                ]
            )

        content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        parts.extend(
            [
                f"--{boundary}\r\n".encode(),
                f'Content-Disposition: form-data; name="file"; filename="{file_path.name}"\r\n'.encode(),
                f"Content-Type: {content_type}\r\n\r\n".encode(),
                file_path.read_bytes(),
                b"\r\n",
                f"--{boundary}--\r\n".encode(),
            ]
        )
        body = b"".join(parts)
        request = urllib.request.Request(
            self._url(path),
            data=body,
            headers={
                "Accept": "application/json",
                "Content-Type": f"multipart/form-data; boundary={boundary}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return self._decode_response(response)
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise VoiceboxBackendError(f"POST {path} failed: {exc.code} {detail}") from exc
        except urllib.error.URLError as exc:
            raise VoiceboxBackendError(f"Cannot reach Voicebox backend at {self.base_url}: {exc.reason}") from exc

    def get(self, path: str, *, query: dict[str, Any] | None = None) -> Any:
        return self.request("GET", path, query=query)

    def post(self, path: str, *, json_body: dict[str, Any] | None = None) -> Any:
        return self.request("POST", path, json_body=json_body)

    def put(self, path: str, *, json_body: dict[str, Any] | None = None) -> Any:
        return self.request("PUT", path, json_body=json_body)

    def delete(self, path: str) -> Any:
        return self.request("DELETE", path)

    def _url(self, path: str, query: dict[str, Any] | None = None) -> str:
        clean_path = path if path.startswith("/") else f"/{path}"
        url = f"{self.base_url}{clean_path}"
        if query:
            filtered = {key: value for key, value in query.items() if value is not None}
            if filtered:
                url = f"{url}?{urllib.parse.urlencode(filtered)}"
        return url

    @staticmethod
    def _decode_response(response: Any) -> Any:
        raw = response.read()
        if not raw:
            return {}
        content_type = response.headers.get("Content-Type", "")
        if "application/json" in content_type:
            return json.loads(raw.decode("utf-8"))
        try:
            return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            return raw.decode("utf-8", errors="replace")
