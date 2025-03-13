import json
from dish_manager.dish_utils.json_utils import decode_dataclass

    
# loaded_obj = json.loads(, object_hook=decode_dataclass)

file_path = "/media/ben/Analysis/Python/A1_manager/config/calib_96well.json"
with open(file_path, "r") as file:
    content = file.read().strip()
    if content:
        data = json.loads(content, object_hook=decode_dataclass)
    else:
        raise ValueError("File is empty")

for key, val in data.items():
    print(f"{key}: {type(val)}")