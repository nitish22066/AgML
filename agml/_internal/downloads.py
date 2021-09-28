import os
import sys
import zipfile

import boto3
import botocore.exceptions
from tqdm import tqdm

def download_dataset(dataset_name, dest_dir):
    """
    Downloads dataset from agdata-data s3 file storage.

    Parameters
    ----------
    dataset_name : str
        name of dataset to download
    dest_dir : str
        path for saving downloaded dataset
    """
    # Establish connection with s3 via boto
    s3 = boto3.client('s3')
    s3_resource = boto3.resource('s3')

    # Setup progress bar
    try:
        ds_size = float(s3_resource.ObjectSummary(
            bucket_name = 'agdata-data', key = dataset_name + '.zip').size)
        pg = tqdm(
            total = ds_size, file = sys.stdout,
            desc = f"Downloading {dataset_name} (size = {round(ds_size / 1000000, 1)} MB)")
    except botocore.exceptions.ClientError as ce:
        if "Not Found" in str(ce):
            raise ValueError(
                f"The dataset '{dataset_name}' could not be found in "
                f"the bucket, perhaps it has not been uploaded yet.")
        raise ce

    # File path of zipped dataset
    dataset_download_path = os.path.join(dest_dir, dataset_name + '.zip')

    # Upload data to agdata-data bucket
    try:
        with open(dataset_download_path, 'wb') as data:
            s3.download_fileobj(Bucket = 'agdata-data',
                                Key = dataset_name + '.zip',
                                Fileobj = data,
                                Callback = lambda x: pg.update(x))
        pg.close()
    except BaseException as e:
        pg.close()
        if os.path.exists(dataset_download_path):
            os.remove(dataset_download_path)
        raise e

    # Unzip downloaded dataset
    with zipfile.ZipFile(dataset_download_path, 'r') as z:
        z.printdir()
        print('Extracting files...')
        z.extractall(path = dest_dir)
        print('Done!')

    # Delete zipped file
    os.remove(dataset_download_path)