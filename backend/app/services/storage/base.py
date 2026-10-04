"""
Abstract Base Class for Document and Resume Storage Services.
"""

from abc import ABC, abstractmethod


class BaseStorageService(ABC):
    @abstractmethod
    def upload_file(self, bucket: str, destination_path: str, content: bytes, content_type: str = "application/octet-stream") -> str:
        """Uploads file content and returns its canonical storage path."""
        pass

    @abstractmethod
    def download_file(self, bucket: str, storage_path: str) -> bytes:
        """Retrieves raw file bytes from storage."""
        pass

    @abstractmethod
    def delete_file(self, bucket: str, storage_path: str) -> bool:
        """Deletes a file from storage."""
        pass
