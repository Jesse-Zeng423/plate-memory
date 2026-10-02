"""Bounded explicit local import. No URL fetch and no preference side effects."""
import json
from pathlib import Path
from ..domain.friend_pack import validate_friend_pack
from ..file_io import read_text
from ..json_contract import loads
from ..storage.private_file import write_private


def load_friend_pack(path):
    return validate_friend_pack(loads(read_text(Path(path),maximum=24000)))


def save_friend_pack(path,pack):
    validate_friend_pack(pack)
    write_private(path,json.dumps(pack,ensure_ascii=False,indent=2)+'\n')
