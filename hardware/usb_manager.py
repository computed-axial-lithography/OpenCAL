import os

class MP4Driver:
    def __init__(self, mount_point="/media/opencal"):
        self.mount_point = mount_point

    def list_mp4_files(self):
        """
        List all MP4 files in the USB storage device directory.
        Returns a list of file names (strings).
        """
        mp4_files = []
        # Check if the mount point exists
        if not os.path.exists(self.mount_point):
            raise FileNotFoundError(f"Mount point {self.mount_point} not found.")
        
        # Walk through the directory and find mp4 files
        for root, dirs, files in os.walk(self.mount_point):
            for file in files:
                if file.lower().endswith('.mp4'):  # Case-insensitive check
                    mp4_files.append(os.path.join(root, file))  # Full path of the file
        
        return mp4_files

    def get_file_names(self):
        """
        Return only the file names (without paths).
        """
        mp4_files = self.list_mp4_files()
        return [os.path.basename(file) for file in mp4_files]

    def print_mp4_files(self):
        """
        Print the names of all MP4 files found.
        """
        mp4_files = self.get_file_names()
        if not mp4_files:
            print("No MP4 files found.")
        else:
            print("MP4 Files found:")
            for file in mp4_files:
                print(file)
    def get_full_path(self, filename):
        """
        Given a filename (as returned by get_file_names), return the full path to the file.
        Raises FileNotFoundError if the file is not found.
        """
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
