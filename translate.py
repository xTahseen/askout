import aiohttp
from langdetect import detect, LangDetectException

async def google_translate(query, source_lang="auto", target_lang="en"):
    url = "https://translate.google.com/translate_a/single"
    params = {
        "client": "gtx",
        "sl": source_lang,
        "tl": target_lang,
        "dt": "t",
        "q": query
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                translation = "".join([item[0] for item in data[0]])
                # Google's response contains the detected language at data[2]
                detected_lang = data[2] if len(data) > 2 else None
                return translation, detected_lang
            else:
                raise Exception("Failed to fetch translation.")

def detect_language(text):
    try:
        return detect(text)
    except LangDetectException:
        return "unknown"
