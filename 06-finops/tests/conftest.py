import os

# Tests may use the public dev salt; real runs refuse without LP_HASH_SALT (see ingest.schema.resolve_salt).
os.environ.setdefault("LP_ALLOW_DEV_SALT", "1")
