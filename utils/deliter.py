import os
import shutil
from typing import Union
from pathlib import Path


async def delete_path(path: Union[str, Path]) -> bool:
    """
    Асинхронно удаляет файл или папку (рекурсивно) с обработкой ошибок

    :param path: Путь к файлу/папке (строка или Path-объект)
    :return: True если удаление успешно, False если ошибка
    """
    try:
        path_obj = Path(path) if isinstance(path, str) else path

        if not path_obj.exists():
            return False

        if path_obj.is_file():
            # Удаление файла
            os.remove(path_obj)
            return True
        elif path_obj.is_dir():
            # Рекурсивное удаление папки и всего содержимого
            shutil.rmtree(path_obj)
            return True


    except PermissionError as e:
        print(f"Ошибка прав доступа при удалении {path_obj}: {e}")
    except Exception as e:
        print(f"Неизвестная ошибка при удалении {path_obj}: {e}")

    return False