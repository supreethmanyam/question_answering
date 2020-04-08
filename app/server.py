from starlette.applications import Starlette
from starlette.responses import HTMLResponse, JSONResponse
from starlette.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
import uvicorn, aiohttp, asyncio
from pathlib import Path
import sys
import os
from zipfile import ZipFile
from transformers import BertTokenizer
import tensorflow as tf
import tensorflow_hub as hub

path = Path(__file__).parent

app = Starlette()
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_headers=['X-Requested-With', 'Content-Type'])
app.mount('/static', StaticFiles(directory='app/static'))

tokenizer_file_url = "https://github.com/supreethmanyam/question_answering/releases/download/v1.0/tokenizer_tf2_qa.zip"
tokenizer_file_name = "tokenizer_tf2_qa"
model_file_url = "https://github.com/supreethmanyam/question_answering/releases/download/v1.0/model.tar.gz"

async def download_file(url, dest):
    if dest.exists(): return
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.read()
            with open(dest, 'wb') as f: f.write(data)

async def setup_model():
    model = hub.load(model_file_url)
    return model

async def setup_tokenizer():
    models_path = path/'models'
    models_path.mkdir(exist_ok=True)
    tokenizer_path = models_path/f'{tokenizer_file_name}'
    tokenizer_zip_path = models_path/f'{tokenizer_file_name}.zip'
    await download_file(tokenizer_file_url, tokenizer_zip_path)
    os.system(f'unzip {str(tokenizer_zip_path)} -d {models_path}')
    tokenizer = BertTokenizer.from_pretrained(str(tokenizer_path))
    return tokenizer

loop = asyncio.get_event_loop()
tokenizer = loop.run_until_complete(asyncio.ensure_future(setup_tokenizer()))
model = loop.run_until_complete(asyncio.ensure_future(setup_model()))
loop.close()

@app.route('/')
def index(request):
    html = path/'view'/'index.html'
    return HTMLResponse(html.open().read())

@app.route('/answer', methods=['POST'])
async def analyze(request):
    data = await request.form()
    article = data['article']
    question = data['question']

    question_tokens = tokenizer.tokenize(question)
    article_tokens = tokenizer.tokenize(article)
    tokens = ['[CLS]'] + question_tokens + ['[SEP]'] + article_tokens + ['[SEP]']
    input_word_ids = tokenizer.convert_tokens_to_ids(tokens)
    input_mask = [1] * len(input_word_ids)
    input_type_ids = [0] * (1 + len(question_tokens) + 1) + [1] * (len(article_tokens) + 1)

    input_word_ids, input_mask, input_type_ids = map(lambda t: tf.expand_dims(
        tf.convert_to_tensor(t, dtype=tf.int32), 0), (input_word_ids, input_mask, input_type_ids))
    outputs = model([input_word_ids, input_mask, input_type_ids])
    # using `[1:]` will enforce an answer. `outputs[:][0][0]` is the ignored '[CLS]' token logit.
    short_start = tf.argmax(outputs[0][0][1:]) + 1
    short_end = tf.argmax(outputs[1][0][1:]) + 1
    answer_tokens = tokens[short_start: short_end + 1]
    answer = tokenizer.convert_tokens_to_string(answer_tokens)
    return JSONResponse({'answer': str(answer)})

if __name__ == '__main__':
    if 'serve' in sys.argv: uvicorn.run(app, host='0.0.0.0', port=8080)

