import hashlib

from exceptions.exceptions import ModProcessingError


class FileHasher:
    @staticmethod
    def calculate_sha1(file_path: str) -> str:
        """
        Calculates the SHA-1 hash of the specified file.

        Args:
            file_path (str): Path to the file.

        Returns:
            str: The SHA-1 hash of the file content.

        Raises:
            ModProcessingError: If there is an error reading the file.
        """
        sha1 = hashlib.sha1()
        try:
            with open(file_path, 'rb') as f:
                while True:
                    data = f.read(65536)
                    if not data:
                        break
                    sha1.update(data)
        except IOError as error:
            raise ModProcessingError(f"Error reading file {file_path}: {error.strerror}")
        return sha1.hexdigest()