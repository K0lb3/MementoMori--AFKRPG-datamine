import os

from api import API


def update_master(path: str, api: API):
    os.makedirs(path, exist_ok=True)
    new_catalog = api.get_master_catalog()

    catalog_fp = os.path.join(path, "master-catalog.json")
    if os.path.exists(catalog_fp):
        with open(catalog_fp, "rb") as f:
            old_catalog = json.load(f)["MasterBookInfoMap"]
    else:
        old_catalog = {}

    for name, item in new_catalog["MasterBookInfoMap"].items():
        fp = os.path.join(path, f"{name}.json")
        if (
            os.path.exists(fp)
            and name in old_catalog
            and item["Hash"] == old_catalog[name]["Hash"]
        ):
            continue
        print(f"Updating {name}")
        data = api.get_master(name)
        with open(fp, "wb") as f:
            f.write(json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8"))

    with open(catalog_fp, "wb") as f:
        f.write(json.dumps(new_catalog, indent=2, ensure_ascii=False).encode("utf-8"))


def update_assets(path: str, api: API, system="Android"):
    os.makedirs(path, exist_ok=True)
    new_catalog = api.get_asset_catalog()

    catalog_fp = os.path.join(path, "catalog_Remote.json")

    if os.path.exists(catalog_fp):
        with open(catalog_fp, "rb") as f:
            old_catalog = json.load(f)
            etags = old_catalog["_etags"]
    else:
        etags = {}

    # TODO - decode datastrings
    # for key, value in new_catalog.items():
    #     if key.endswith("DataString"):
    #         value = b64decode(value)
    #         print()

    for id in new_catalog["m_InternalIds"]:
        id = id[3:]  # strip 0#/ - 0# gets replaced by the system
        fp = os.path.join(path, id)

        etag = api.get_asset_etag(id, system)
        if id in etags:
            if etag == etags[id]:
                continue
        etags[id] = etag
        raw = api.get_asset(id, system=system)

        with open(fp, "wb") as f:
            f.write(raw)

    new_catalog["_etags"] = etags
    with open(catalog_fp, "wb") as f:
        f.write(json.dumps(new_catalog, indent=2, ensure_ascii=False).encode("utf-8"))


if __name__ == "__main__":
    api = API()
    print(api.getDataUri())
    update_master("master", api)
    update_assets("assets", api)
