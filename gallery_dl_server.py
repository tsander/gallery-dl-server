# /Library/Frameworks/Python.framework/Versions/3.7/bin/python3

import argparse
import os
import gallery_dl

from gallery_dl import config
from bottle import route, run, Bottle, request, static_file
from queue import Queue
from threading import Thread
from zipfile import ZipFile
from concurrent.futures import ThreadPoolExecutor

parser = argparse.ArgumentParser()
parser.add_argument("--zip_downloads", 
                    nargs='?',
                    const=1,
                    default='True',
                    choices=['False', 'True'], 
                    help="Zip files into CBZ after download")
args = parser.parse_args()
config.load()

app = Bottle()
DL_THREAD = ThreadPoolExecutor(max_workers=2)

DEFAULT_HOST = '0.0.0.0'
DEFAULT_PORT = 8080

GALLERY_PATH = './gallery-dl/'
ZIP_SUFFIX = 'cbz'

class NoPathExists(Exception):
    pass

@app.route('/')
def gallery_main():
    return static_file('index.html', root='./')


@app.route('/gallery-dl', method='POST')
def gallery_post():
    url = request.forms.get('url')

    if not url:
        return {'Missing URL'}

    DL_THREAD.submit(call_gallery_dl, url)

    return {"successfully_added_to_queue": True}


def call_gallery_dl(url):
    try:
        download_job = gallery_dl.job.DownloadJob
        downloader = download_job(url)
        downloader.run()

        if args.zip_downloads == 'True':
            download_path = downloader.pathfmt.directory
            zip_directories(download_path)
        print('Finished downloading!')
    except gallery_dl.exception.NoExtractorError as gd:
        print(gd)

@app.route('/gallery-dl/create_zip', method='GET')
def find_directories_and_zip():
    if not os.path.exists(GALLERY_PATH):
        raise NoPathExists("GALLERY PATH does not exist; Download something and try again")

    top_dir = os.listdir(GALLERY_PATH)
    for each_dir in top_dir:
        each_dir_path = os.path.join(GALLERY_PATH, each_dir)
        zip_directories(each_dir_path)

    return {'successful_created_zips': True}


def zip_directories(path_to_zip):
    for root_path, dirct, files in os.walk(path_to_zip):

        # Check if there are photos in the files, if not skip directory
        photos_in_directory = [x for x in files if x.rsplit('.', 1)[1] in ('jpg', 'png')]
        if not photos_in_directory:
            print('No photos in directory: ' + root_path)
            continue

        # Remove trailing / if it exists
        zip_path, zip_file = root_path.rstrip('/').rsplit('/', 1)
        zip_file_name = zip_file + '.' + ZIP_SUFFIX
        zip_file_path = os.path.join(zip_path, zip_file_name)

        # Check if zip file has already been created and skip if already created
        # TODO: Allow ability to ignore check and re-zip folders.
        if os.path.exists(zip_file_path):
            existing_zip = ZipFile(zip_file_path)
            items_in_zip = existing_zip.namelist()

            # If the photos in the directory is less than or equal to items in zip; skip
            if len(photos_in_directory) <= len(items_in_zip):
                print('Files have already been zipped.')
                print('Skipping')
                continue

        print('Creating file: ' + zip_file_path)
        with ZipFile(zip_file_path, 'w') as myzip:
            for each_photo in photos_in_directory:
                each_photo_path = os.path.join(root_path, each_photo)
                myzip.write(each_photo_path)
        print('Finished creating zip for: ' + root_path)


if __name__ == '__main__':

    app.run(host=DEFAULT_HOST, port=DEFAULT_PORT, debug=True)