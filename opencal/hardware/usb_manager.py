import os
from pathlib import Path


class MP4Driver:
    def __init__(self, mount_point: Path = Path("/media/opencal/")):
        self.mount_point = mount_point

    def list_mp4_files(self) -> list[Path]:
        """
        List all MP4 files in the USB storage device directory.
        Returns a list of file names (strings).
        """

        mp4_paths = []

        if not self.mount_point.exists():
            raise FileNotFoundError(f"USB mount point {self.mount_point} does not exist")

        for dir_path, _dirs, files in os.walk(self.mount_point):
            for file in files:
                file_path = Path(dir_path) / file
                if file_path.suffix == ".mp4":
                    mp4_paths.append(file_path)

        return mp4_paths

    def get_file_names(self) -> list[str]:
        """
        Return only the file names (without paths).
        """
        # Get the list of full MP4 file paths and extract just the file names
        mp4_paths = self.list_mp4_files()
        return [path.name for path in mp4_paths]

    def print_mp4_files(self):
        """
        Print the names of all MP4 files found.
        """
        # Retrieve the list of MP4 file names
        mp4_files = self.get_file_names()
        if not mp4_files:
            print("No MP4 files found.")
        else:
            print("MP4 Files found:")
            # Print each file name
            for file in mp4_files:
                print(file)

    def get_full_path(self, filename: str) -> Path:
        """
        Given a filename (as returned by get_file_names), return the full path to the file.
        Raises FileNotFoundError if the file is not found.
        """

        # Search for the full path of the specified file name
        for full_path in self.list_mp4_files():
            if full_path.name == filename:
                return full_path
        raise FileNotFoundError(f"File {filename} not found in {self.mount_point}")


# Example Usage:
if __name__ == "__main__":
    # Create an MP4Driver instance with the USB mount point
    driver = MP4Driver()

    # List MP4 file names
    mp4_files = driver.get_file_names()
    print(mp4_files)

    # Or print them directly
    driver.print_mp4_files()
