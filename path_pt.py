from pathlib import Path

root = Path("./dataBase")
for file_path in root.glob('*'):
    print(file_path)
