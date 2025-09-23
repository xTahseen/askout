import asyncio
import pathlib
import tempfile
import uuid
from playwright.async_api import async_playwright

# Paths to local Poppins font files in the fonts directory
BASE_DIR = pathlib.Path(__file__).parent.resolve()
FONTS_DIR = BASE_DIR / "fonts"
POPPINS_REGULAR = FONTS_DIR / "Poppins-Regular.ttf"
POPPINS_MEDIUM = FONTS_DIR / "Poppins-Medium.ttf"
POPPINS_SEMIBOLD = FONTS_DIR / "Poppins-SemiBold.ttf"

HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Generate PNG</title>
    <style>
        @font-face {{
            font-family: 'Poppins';
            src: url('file://{poppins_regular}') format('truetype');
            font-weight: 400;
        }}
        @font-face {{
            font-family: 'Poppins';
            src: url('file://{poppins_medium}') format('truetype');
            font-weight: 500;
        }}
        @font-face {{
            font-family: 'Poppins';
            src: url('file://{poppins_semibold}') format('truetype');
            font-weight: 600;
        }}
        body {{
            margin: 0;
            padding: 0;
            font-family: 'Poppins', 'Noto Color Emoji', 'Apple Color Emoji', 'Segoe UI Emoji', 'Twemoji', 'EmojiOne', sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            background: transparent;
        }}
        .container {{
            width: 400px;
            padding: 24px;
            background: linear-gradient(135deg, #f8fafc 0%, #e0f2fe 50%, #e0e7ff 100%);
        }}
    </style>
</head>
<body>
    <div class="container" id="message-card">
        <div style="background: rgba(255, 255, 255, 0.9); border-radius: 16px; padding: 24px; box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1); backdrop-filter: blur(10px);">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px;">
                <div style="background: linear-gradient(135deg, #3b82f6, #6366f1); color: white; padding: 6px 12px; border-radius: 12px; font-size: 12px; font-weight: 600;">
                    {sender}
                </div>
                <div style="background: #f1f5f9; color: #64748b; padding: 4px 8px; border-radius: 12px; font-size: 11px; font-weight: 500;">
                    {timestamp}
                </div>
            </div>
            <div style="position: relative;">
                <div style="position: absolute; left: 0; top: 0; width: 4px; height: 100%; background: linear-gradient(to bottom, #3b82f6, #6366f1); border-radius: 2px;"></div>
                <div style="padding-left: 24px; color: #334155; line-height: 1.6; font-weight: 500; font-size: 16px;">
                    {message}
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""

async def generate_message_image(text: str, name: str = "Askoutbot", compact: bool = True) -> str:
    import datetime

    sender = name if (name and isinstance(name, str)) else "Askoutbot"
    timestamp = "Just now"
    html_content = HTML_TEMPLATE.format(
        poppins_regular=POPPINS_REGULAR.as_posix(),
        poppins_medium=POPPINS_MEDIUM.as_posix(),
        poppins_semibold=POPPINS_SEMIBOLD.as_posix(),
        sender=sender,
        timestamp=timestamp,
        message=text.replace("\n", "<br>")
    )

    # Create temp HTML file
    temp_dir = tempfile.gettempdir()
    file_id = uuid.uuid4().hex
    html_path = pathlib.Path(temp_dir) / f"msg_{file_id}.html"
    png_path = pathlib.Path(temp_dir) / f"msg_{file_id}.png"
    html_path.write_text(html_content, encoding="utf-8")

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page(
                viewport={"width": 500, "height": 600},
                device_scale_factor=3
            )
            await page.goto(html_path.absolute().as_uri())
            await page.wait_for_function("document.fonts.ready")
            element = await page.query_selector("#message-card")
            await element.screenshot(path=str(png_path), scale="device")
            await browser.close()
        return str(png_path)
    except Exception as ex:
        print(f"❌ Image generation failed: {ex}")
        return None
    finally:
        try:
            html_path.unlink(missing_ok=True)
        except Exception:
            pass
