from pathlib import Path

import boto3
from tqdm import tqdm

# Configure S3 bucket
BUCKET_NAME = "nba-data-storage-analyticsapp"  # Replace with your bucket name
LOCAL_FOLDER = Path("data/")  # Path to the local folder
S3_PREFIX = "data/"  # Path in S3 (acts like a root "folder")

s3 = boto3.client("s3")


def upload_folder_to_s3(local_folder: Path, bucket_name: str, s3_prefix: str = ""):
    """
    Uploads all files in a folder to S3, preserving directory structure.

    :param local_folder: Path object pointing to the local folder.
    :param bucket_name: Name of the S3 bucket.
    :param s3_prefix: Folder path inside S3.
    """

    total_tasks = len(list(local_folder.rglob("*")))
    progress_bar = tqdm(total=total_tasks, desc="Progress", unit="task")

    for file in local_folder.rglob("*"):  # Recursively find all files
        if file.is_file():  # Ignore directories
            if file.name.startswith("."):
                progress_bar.update(1)
                continue
            # Generate S3 key (relative path in S3)
            s3_key = f"{s3_prefix}{file.relative_to(local_folder).as_posix()}"

            # Upload the file to S3
            s3.upload_file(str(file), bucket_name, s3_key)
            progress_bar.set_description(f"Uploaded {file.name}")
            progress_bar.update(1)


if __name__ == "__main__":
    upload_folder_to_s3(LOCAL_FOLDER, BUCKET_NAME, S3_PREFIX)
