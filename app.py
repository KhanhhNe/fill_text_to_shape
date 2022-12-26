import os
import time
from io import BytesIO

import requests
from PIL import Image
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel

import image_processing

app = FastAPI()


@app.on_event('startup')
def init_application():
    os.makedirs('output', exist_ok=True)


class FitTextInput(BaseModel):
    urlImage: str
    urlFont: str
    text: str
    color: str
    width: float = None
    height: float = None


@app.post('/fit-text')
def fit_text(inp: FitTextInput, request: Request):
    """
    Fit text to shape.

    :return: Image URL for rendered image
    """
    image_content = BytesIO(requests.get(inp.urlImage).content)
    image = Image.open(image_content)
    font = BytesIO(requests.get(inp.urlFont).content)
    color_hex = inp.color.lstrip('#').ljust(8, 'f')
    color = tuple(int(color_hex[i:i + 2], 16) for i in (0, 2, 4, 6))

    if os.environ.get('DEBUG'):
        import cProfile
        with cProfile.Profile() as pr:
            # noinspection PyTypeChecker
            output_image = image_processing.fit_text_to_image(image, inp.text,
                                                              font, color)
        pr.print_stats()
    else:
        # noinspection PyTypeChecker
        output_image = image_processing.fit_text_to_image(image, inp.text,
                                                          font, color)

    if inp.width and inp.height:
        output_image = output_image.resize((int(inp.width), int(inp.height)),
                                           Image.ANTIALIAS)
    else:
        output_image = output_image.resize((image.width, image.height),
                                           Image.ANTIALIAS)

    if os.environ.get('DEBUG'):
        output_image.show()

    output_name = (f"{time.time()}-"
                   f"{str(time.perf_counter()).replace('.', '')}" + '.png')
    output_path = f'output/{output_name}'
    output_image.save(output_path, format='PNG')

    return {
        "imageSrc": f"{request.base_url}fit-text?name={output_name}"
    }


@app.get('/fit-text')
def get_output(name: str):
    """
    Get rendered image by name.
    """
    filepath = f'output/{name}'
    if os.path.exists(filepath):
        return FileResponse(filepath, media_type='image/png')
    else:
        return PlainTextResponse('')
