import os

import uvicorn

if __name__ == '__main__':
    if not os.path.exists('port.txt'):
        open('port.txt', 'w+').write('80')
    os.environ['PATH'] += ';' + os.getcwd()

    port = int(open('port.txt').read())
    uvicorn.run('app:app', host='0.0.0.0', port=port, workers=5)
