import lmdb

lmdb_write_client = lmdb.open("data.lmdb", map_size=256 * 1024 * 1024, max_dbs=1, subdir=True, lock=True)
lmdb_read_client = lmdb.open("data.lmdb", readonly=True)
