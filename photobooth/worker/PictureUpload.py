#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Photobooth - a flexible photo booth software
# Copyright (C) 2018  Balthasar Reuter <photobooth at re - web dot eu>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import logging
import requests

from pathlib import Path
try:
    from google.cloud.storage import Client
except:
    logging.warn("GCP dependency not installed")

from .WorkerTask import WorkerTask


class PictureUpload(WorkerTask):

    def __init__(self, config):

        super().__init__()

        self._webdav_enabled = config.getBool('Upload', 'webdav_enable')
        self._gcp_enabled = config.getBool('Upload', 'gcp_enable')

        if self._webdav_enabled:
            self._baseurl = config.get('Upload', 'webdav_url')
            if config.getBool('Upload', 'webdav_use_auth'):
                self._auth = (config.get('Upload', 'webdav_user'),
                              config.get('Upload', 'webdav_password'))
            else:
                self._auth = None
        if self._gcp_enabled:
            print("Initialized GCP!")
            self._bucket_name = config.get('Upload', 'gcp_bucket')
            self._service_account_location = config.get('Upload', 'gcp_service_account_path')
            try:
                self._client = Client.from_service_account_json(self._service_account_location)
            except:
                self._client = None



    def do(self, picture, filename):

        if self._webdav_enabled:
            url = self._baseurl + '/' + Path(filename).name
            logging.info('Uploading picture as %s', url)

            r = requests.put(url, data=picture.getbuffer(), auth=self._auth)
            if r.status_code in range(200, 300):
                logging.warn(('PictureUpload: Upload failed with '
                              'status code {}').format(r.status_code))

        if self._gcp_enabled:
            # Do not use the logger here, since the root logger somehow gets set to WARN instead of INFO here
            print("Uploading the picture now to GCP!")
            storage_client = self._client
            if self._client is not None:
                try:
                    bucket = storage_client.bucket(self._bucket_name)
                    blob = bucket.blob(filename)
                    blob.upload_from_string(picture.getvalue(), content_type='image/jpeg', timeout=30)
                    print(f"uploaded {blob.id} to {self._bucket_name}")
                except:
                    logging.warn("Could not upload the image to GCP")
            else:
                logging.warn("Something went wrong initiating the GCP Storage client")

