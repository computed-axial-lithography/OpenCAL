import os


class MP4Driver:
    def __init__(self, mount_point: str = "/media/opencal"):
        # Initialize the MP4Driver with a specified mount point for the USB storage
        # TODO: use Path
        self.mount_point: str = mount_point

    def list_mp4_files(self) -> list[str]:
        """
        List all MP4 files in the USB storage device directory.
        Returns a list of file names (strings).
        """

        # TODO: Use Path
        mp4_files: list[str] = []
        # Check if the mount point exists
        if not os.path.exists(self.mount_point):
            raise FileNotFoundError(f"Mount point {self.mount_point} not found.")

        # Walk through the directory and find mp4 files
        for root, _dirs, files in os.walk(self.mount_point):
            for file in files:
                # Case-insensitive check for .mp4 file extension
                if file.lower().endswith(".mp4"):
                    # Append the full path of the file to the list
                    mp4_files.append(os.path.join(root, file))

        return mp4_files

    def get_file_names(self):
        """
        Return only the file names (without paths).
        """
        # Get the list of full MP4 file paths and extract just the file names
        mp4_files = self.list_mp4_files()
        return [os.path.basename(file) for file in mp4_files]

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

    def get_full_path(self, filename: str) -> str:
        """
        Given a filename (as returned by get_file_names), return the full path to the file.
        Raises FileNotFoundError if the file is not found.
        """
        # TODO: Use Path?

        # Search for the full path of the specified file name
        for full_path in self.list_mp4_files():
            if os.path.basename(full_path) == filename:
                return full_path
        raise FileNotFoundError(f"File {filename} not found in {self.mount_point}")


# Example Usage:
if __name__ == "__main__":
    # Create an MP4Driver instance with the USB mount point
    driver = MP4Driver(mount_point="/media/opencal")

    # List MP4 file names
    mp4_files = driver.get_file_names()
    print(mp4_files)

    # Or print them directly
    driver.print_mp4_files()
