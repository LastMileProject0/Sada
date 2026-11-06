"""Small, uncompressed JSON only, including for direct loopback requests."""
from starlette.responses import JSONResponse

MAX_REQUEST_BYTES = 4096


class EvaluationRequestBoundary:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if (scope['type'] != 'http' or scope['method'] != 'POST'
                or scope['path'].rstrip('/') not in ('/api/evaluations', '/api/policy/explain')):
            return await self.app(scope, receive, send)
        headers = dict(scope['headers'])
        encoding = headers.get(b'content-encoding', b'identity').lower()
        media_type = headers.get(b'content-type', b'').split(b';')[0].strip().lower()
        status, detail = 0, ''
        if encoding != b'identity':
            status, detail = 415, 'Compressed request bodies are not supported.'
        elif media_type != b'application/json':
            status, detail = 415, 'Evaluation requests require application/json.'
        body = bytearray()
        if not status:
            while True:
                message = await receive()
                if message['type'] == 'http.disconnect':
                    return
                chunk = message.get('body', b'')
                if len(body) + len(chunk) > MAX_REQUEST_BYTES:
                    status, detail = 413, 'Request body exceeds the 4 KiB limit.'
                    break
                body.extend(chunk)
                if not message.get('more_body'):
                    break
        if status:
            return await JSONResponse({'detail': detail}, status_code=status,
                                      headers={'Cache-Control': 'no-store'})(scope, receive, send)

        async def replay():
            return {'type': 'http.request', 'body': bytes(body), 'more_body': False}
        await self.app(scope, replay, send)
