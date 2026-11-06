"""Server-only transport for the explicitly approved model; no model fallback."""
from __future__ import annotations

import json
import os
from urllib import error, request

MODEL = 'qwen/qwen-2.5-7b-instruct'
ENDPOINT = 'https://openrouter.ai/api/v1/chat/completions'
TIMEOUT_SECONDS = 30
MAX_OUTPUT_TOKENS = 700
MAX_RESPONSE_BYTES = 65_536
MAX_PROMPT_CHARS = 24_000


class ProviderUnavailable(RuntimeError):
    """Deliberately contains neither upstream body nor credentials."""


class _NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def openrouter_provider(prompt: str, model_id: str) -> str:
    key = os.environ.get('OPENROUTER_API_KEY', '').strip()
    if not key or model_id != MODEL or not prompt or len(prompt) > MAX_PROMPT_CHARS:
        raise ProviderUnavailable('OpenRouter configuration unavailable')
    # This prompt is built by the unchanged original explainer, with facts={}.
    # No cookies, owner hashes, evaluation records, user IDs, tools or plugins.
    payload = {
        'model': MODEL, 'messages': [{'role': 'user', 'content': prompt}],
        'temperature': 0, 'max_tokens': MAX_OUTPUT_TOKENS, 'stream': False,
        'provider': {
            'data_collection': 'deny', 'zdr': True,
            'allow_fallbacks': False, 'require_parameters': True,
            # Public OpenRouter ZDR catalog lists this exact-model endpoint as
            # safety_retention=false. Fail closed rather than pick another host.
            'only': ['phala'],
        },
    }
    req = request.Request(
        ENDPOINT, data=json.dumps(payload, ensure_ascii=False).encode('utf-8'),
        headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'},
        method='POST',
    )
    try:
        # Reject redirects rather than forwarding authorization to another host.
        with request.build_opener(_NoRedirect()).open(req, timeout=TIMEOUT_SECONDS) as response:
            if response.status != 200:
                raise ProviderUnavailable('OpenRouter unavailable')
            raw = response.read(MAX_RESPONSE_BYTES + 1)
        if len(raw) > MAX_RESPONSE_BYTES:
            raise ProviderUnavailable('OpenRouter response limit exceeded')
        data = json.loads(raw)
        if data.get('error') or data.get('model') != MODEL:
            raise ProviderUnavailable('OpenRouter model response rejected')
        choice = data['choices'][0]
        text = choice['message']['content']
        if (choice.get('finish_reason') != 'stop' or not isinstance(text, str)
                or not text.strip() or len(text) > 16_000 or key in text):
            raise ProviderUnavailable('OpenRouter response rejected')
        return text.strip()
    except error.HTTPError as exc:
        # Never read or forward upstream error bodies/headers.
        exc.close()
        raise ProviderUnavailable('OpenRouter unavailable') from None
    except (error.URLError, OSError, ValueError, KeyError, IndexError, TypeError, AttributeError):
        raise ProviderUnavailable('OpenRouter unavailable') from None
