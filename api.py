#!/usr/bin/env python
from base64 import b64decode
from datetime import datetime
import json
import uuid

import requests
import msgpack


def generate_uuid():
    return str(uuid.uuid4()).replace("-", "")  # 32 characters


ASSET_HEADERS = {
    "accept-encoding": "gzip, identity",
    "user-agent": "BestHTTP/2 v2.3.0",
    "content-length": "0",
    "pragma": "no-cache",
    "cache-control": "no-cache",
}


class API:
    auth_api: str
    ortegauuid: str
    headers: dict

    session: requests.Session
    asset_catalog_uri_format: str
    master_uri_format: str
    notice_banner_image_uri_format: str

    def __init__(
        self, auth_api="https://prd1-auth.mememori-boi.com", ortegauuid: str = None
    ) -> None:
        self.session = requests.Session()
        self.auth_api = auth_api
        if ortegauuid is None:
            ortegauuid = generate_uuid()

        self.session.headers.update(
            {
                "content-type": "application/json; charset=UTF-8",
                "ortegaaccesstoken": "",
                "ortegaappversion": "1.0.0",
                "ortegadevicetype": "2",
                "ortegauuid": ortegauuid,
                "accept-encoding": "gzip, identity",
                "user-agent": "BestHTTP/2 v2.3.0",
                "pragma": "no-cache",
                "cache-control": "no-cache",
            }
        )

    def request(self, uri: str, data: dict = None, method: str = "POST") -> dict:
        if data is None:
            data = {}
        res = self.session.request(
            method,
            uri,
            data=msgpack.packb(data),
        )
        res.raise_for_status()
        if self.auth_api in uri:
            self.server = res.headers["server"]
            self.ortegastatuscode = int(res.headers["ortegastatuscode"])
            self.orteganextaccesstoken = res.headers["orteganextaccesstoken"]
            self.ortegaassetversion = res.headers["ortegaassetversion"]
            self.ortegamasterversion = res.headers["ortegamasterversion"]
            self.ortegautcnowtimestamp = datetime.fromtimestamp(
                float(res.headers["ortegautcnowtimestamp"]) / 1000
            )

        return msgpack.unpackb(res.content, timestamp=3), res.headers

    def getDataUri(self):
        data, headers = self.request(f"{self.auth_api}/api/auth/getDataUri")

        self.asset_catalog_uri_format = data["AssetCatalogUriFormat"]
        self.master_uri_format = data["MasterUriFormat"]
        self.notice_banner_image_uri_format = data["NoticeBannerImageUriFormat"]

        return data

    def get_asset(self, name: str, system: str = "Android"):
        uri = self.asset_catalog_uri_format.format(
            self.ortegaassetversion, f"{system}/{name}"
        )
        res = requests.get(uri, headers=ASSET_HEADERS)
        res.raise_for_status()
        return res.content

    def get_asset_etag(self, name: str, system: str = "Android"):
        uri = self.asset_catalog_uri_format.format(
            self.ortegaassetversion, f"{system}/{name}"
        )
        res = requests.head(uri, headers=ASSET_HEADERS)
        res.raise_for_status()
        return res.headers["etag"].strip('"')

    def get_master(self, name: str):
        uri = self.master_uri_format.format(self.ortegamasterversion, name)
        res = requests.get(uri, headers=ASSET_HEADERS)
        res.raise_for_status()
        return msgpack.unpackb(res.content, timestamp=3)

    def get_master_catalog(self):
        return self.get_master("master-catalog")

    def get_asset_catalog(self):
        return json.loads(self.get_asset("catalog_Remote.json"))
