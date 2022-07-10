import os, getpass

import numpy as np
import replicate


class DalleImageGenerator:
    """Dall-e model using Replicate API"""
    def __init__(self):
        if "REPLICATE_API_TOKEN" not in os.environ:
            print(f"Please go to https://replicate.com/docs/api for your Replicate API token.")
            os.environ["REPLICATE_API_TOKEN"] = getpass.getpass(f"Input Replicate API Token:")

        self.dalle = replicate.models.get("kuprel/min-dalle")

    def generate_images(self, text, grid_size, text_adherence=2):
        urls = self.dalle.predict(text=text, grid_size=grid_size, log2_supercondition_factor=text_adherence)
        images = get_image(list(urls)[-1])
        h, w = images.shape[:2]
        h, w = h // grid_size, w // grid_size
        return blockshaped(images, h, w)


def get_image(url):
    """download image from a url"""
    from urllib.request import Request, urlopen
    import io
    import PIL.Image as Image
    hdr = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
        'Accept-Encoding': 'none',
        'Accept-Language': 'en-US,en;q=0.8',
        'Connection': 'keep-alive'}

    # urllib.request.urlretrieve(url, f"local-filename.jpg")
    req = Request(url, headers=hdr)
    page = urlopen(req)
    return np.array(Image.open(io.BytesIO(page.read())))


def blockshaped(arr, nrows, ncols):
    """
    Return an array of shape (n, nrows, ncols) where
    n * nrows * ncols = arr.size

    If arr is a 2D array, the returned array should look like n subblocks with
    each subblock preserving the "physical" layout of arr.
    """
    h, w, c = arr.shape
    assert h % nrows == 0, f"{h} rows is not evenly divisible by {nrows}"
    assert w % ncols == 0, f"{w} cols is not evenly divisible by {ncols}"
    return (arr.reshape(h//nrows, nrows, w//ncols, ncols, - 1)
               .swapaxes(1,2)
               .reshape(-1, nrows, ncols, 3))