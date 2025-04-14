from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import base64
import numpy as np
import cv2

app = FastAPI()




def bradley_threshold(src, width, height, t):
    S = max(width // 8, 1)
    s2 = S // 2

    integral_image = np.zeros((height, width), dtype=np.int64)

    for i in range(width):
        sum_ = 0
        for j in range(height):
            sum_ += int(src[j, i])
            if i == 0:
                integral_image[j, i] = sum_
            else:
                integral_image[j, i] = integral_image[j, i - 1] + sum_

    res = np.zeros((height, width), dtype=np.uint8)

    for i in range(width):
        for j in range(height):
            x1 = max(i - s2, 0)
            x2 = min(i + s2, width - 1)
            y1 = max(j - s2, 0)
            y2 = min(j + s2, height - 1)

            count = max((x2 - x1) * (y2 - y1), 1)

            a = integral_image[y2, x2]
            b = integral_image[y1, x2] if y1 > 0 else 0
            c = integral_image[y2, x1] if x1 > 0 else 0
            d = integral_image[y1, x1] if x1 > 0 and y1 > 0 else 0

            sum_ = int(a - b - c + d)

            res[j, i] = 0 if int(src[j, i]) * count < sum_ * (1.0 - t) else 255

    return res


def decode_image_from_base64(base64_string):
    image_data = base64.b64decode(base64_string)

    np_array = np.frombuffer(image_data, dtype=np.uint8)
    img = cv2.imdecode(np_array, cv2.IMREAD_GRAYSCALE)

    if img is None:
        raise ValueError("Не удалось декодировать изображение.")
    return img


def encode_image_to_base64(image):
    _, buffer = cv2.imencode('.png', image)
    img_base64 = base64.b64encode(buffer).decode('utf-8')
    return img_base64


class Base64Image(BaseModel):
    data_image: str


@app.post("/binary_image")
async def image(data: Base64Image):
    try:
        base64_data = data.data_image.split(",")[1]
        # Шаг 1: Декодируем base64 в изображение
        img = decode_image_from_base64(base64_data)
        height, width = img.shape
        # Шаг 2: Применяем метод Брэдли для бинаризации
        binary_img = bradley_threshold(img, width, height, t=0.15)
        # Шаг 3: Кодируем бинаризованное изображение в base64
        img_base64 = encode_image_to_base64(binary_img)

        return {"message": "Изображение бинаризовано", "binary_image": img_base64}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
