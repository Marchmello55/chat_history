import os
import zipfile
from datetime import datetime
import asyncio
import aiofiles  # pip install aiofiles


async def add_file_to_zip(zipf, file_path, arcname):
    """Асинхронно добавляет файл в архив"""
    async with aiofiles.open(file_path, 'rb') as f:
        contents = await f.read()
    zipf.writestr(arcname, contents)

async def async_zip_folder(folder_path):
    """
    Асинхронно архивирует папку в ZIP-файл

    :param folder_path: Путь к папке для архивации
    :param output_path: Путь для сохранения архива
    :return: Путь к созданному архиву
    """

    folder_name = os.path.basename(folder_path)
    output_path = f"{folder_name}.zip"

    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        tasks = []
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, start=folder_path)
                tasks.append(add_file_to_zip(zipf, file_path, arcname))

        await asyncio.gather(*tasks)
    return output_path