import pathlib
import tempfile
import uuid
import imgkit
import re
import random

COLOR_PALETTES = [
    {
        "background": "#FFF5EF",
        "card_background": "#FFFFFF",
        "border": "#D44A52",
        "shadow": "rgba(212, 74, 82, 0.08)",
        "sender_name": "#1F2933",
        "menu_dots": "#D0D5DD",
        "message_color": "#1F2933",
        "hashtag": "#3A9EC7",
        "heart_badge_bg": "#D44A52",
        "heart_badge_shadow": "rgba(212, 74, 82, 0.25)"
    },
    {
        "background": "#E0F7FA",
        "card_background": "#FFFFFF",
        "border": "#00BCD4",
        "shadow": "rgba(0, 188, 212, 0.08)",
        "sender_name": "#263238",
        "menu_dots": "#B2EBF2",
        "message_color": "#263238",
        "hashtag": "#0097A7",
        "heart_badge_bg": "#00BCD4",
        "heart_badge_shadow": "rgba(0, 188, 212, 0.25)"
    },
    {
        "background": "#F3E5F5",
        "card_background": "#FFFFFF",
        "border": "#9C27B0",
        "shadow": "rgba(156, 39, 176, 0.08)",
        "sender_name": "#4A148C",
        "menu_dots": "#E1BEE7",
        "message_color": "#4A148C",
        "hashtag": "#7B1FA2",
        "heart_badge_bg": "#9C27B0",
        "heart_badge_shadow": "rgba(156, 39, 176, 0.25)"
    },
    {
        "background": "#FFFDE7",
        "card_background": "#FFFFFF",
        "border": "#FFC107",
        "shadow": "rgba(255, 193, 7, 0.08)",
        "sender_name": "#FF6F00",
        "menu_dots": "#FFECB3",
        "message_color": "#FF6F00",
        "hashtag": "#FFA000",
        "heart_badge_bg": "#FFC107",
        "heart_badge_shadow": "rgba(255, 193, 7, 0.25)"
    },
    {
        "background": "#E8F5E9",
        "card_background": "#FFFFFF",
        "border": "#4CAF50",
        "shadow": "rgba(76, 175, 80, 0.08)",
        "sender_name": "#2E7D32",
        "menu_dots": "#C8E6C9",
        "message_color": "#2E7D32",
        "hashtag": "#388E3C",
        "heart_badge_bg": "#4CAF50",
        "heart_badge_shadow": "rgba(76, 175, 80, 0.25)"
    },
    {
        "background": "#F0F4F8",
        "card_background": "#FFFFFF",
        "border": "#607D8B",
        "shadow": "rgba(96, 125, 139, 0.08)",
        "sender_name": "#263238",
        "menu_dots": "#CFD8DC",
        "message_color": "#263238",
        "hashtag": "#455A64",
        "heart_badge_bg": "#607D8B",
        "heart_badge_shadow": "rgba(96, 125, 139, 0.25)"
    },
    {
        "background": "#FCE4EC",
        "card_background": "#FFFFFF",
        "border": "#E91E63",
        "shadow": "rgba(233, 30, 99, 0.08)",
        "sender_name": "#880E4F",
        "menu_dots": "#F8BBD0",
        "message_color": "#880E4F",
        "hashtag": "#C2185B",
        "heart_badge_bg": "#E91E63",
        "heart_badge_shadow": "rgba(233, 30, 99, 0.25)"
    },
    {
        "background": "#E3F2FD",
        "card_background": "#FFFFFF",
        "border": "#2196F3",
        "shadow": "rgba(33, 150, 243, 0.08)",
        "sender_name": "#1565C0",
        "menu_dots": "#BBDEFB",
        "message_color": "#1565C0",
        "hashtag": "#1976D2",
        "heart_badge_bg": "#2196F3",
        "heart_badge_shadow": "rgba(33, 150, 243, 0.25)"
    },
    {
        "background": "#FBE9E7",
        "card_background": "#FFFFFF",
        "border": "#FF5722",
        "shadow": "rgba(255, 87, 34, 0.08)",
        "sender_name": "#D84315",
        "menu_dots": "#FFCCBC",
        "message_color": "#D84315",
        "hashtag": "#E64A19",
        "heart_badge_bg": "#FF5722",
        "heart_badge_shadow": "rgba(255, 87, 34, 0.25)"
    },
    {
        "background": "#F1F8E9",
        "card_background": "#FFFFFF",
        "border": "#8BC34A",
        "shadow": "rgba(139, 195, 74, 0.08)",
        "sender_name": "#558B2F",
        "menu_dots": "#DCEDC8",
        "message_color": "#558B2F",
        "hashtag": "#689F38",
        "heart_badge_bg": "#8BC34A",
        "heart_badge_shadow": "rgba(139, 195, 74, 0.25)"
    }
]

HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Askout Message Card</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            color-scheme: light;
        }}
        * {{
            box-sizing: border-box;
        }}
        body {{
            margin: 0;
            padding: 0;
            font-family: 'Inter', sans-serif;
            background: {background}; /* Use dynamic background color */
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }}
        .stage {{
            position: relative;
            width: 1200px;
            padding: 96px 88px 120px;
            background: {background}; /* Use dynamic background color */
            border-radius: 56px;
        }}
        .stage::before {{
            content: "";
            position: absolute;
            top: 28px;
            left: 50%;
            transform: translateX(-50%);
            width: 160px;
            height: 20px;
            border-radius: 999px;
            background: rgba(15, 23, 42, 0.08);
        }}
        .card {{
            position: relative;
            background: {card_background}; /* Use dynamic card background color */
            border: 3px solid {border}; /* Use dynamic border color */
            border-radius: 36px;
            padding: 72px 76px 96px;
            display: flex;
            flex-direction: column;
            gap: 48px;
            box-shadow: 0 28px 70px {shadow}; /* Use dynamic shadow color */
        }}
        .profile {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 32px;
        }}
        .profile-left {{
            display: flex;
            align-items: center;
            gap: 28px;
        }}
        .profile-meta {{
            display: flex;
            flex-direction: column;
            gap: 6px;
        }}
        .sender-name {{
            font-size: 44px;
            font-weight: 700;
            color: {sender_name}; /* Use dynamic sender name color */
            letter-spacing: -0.015em;
            text-wrap: balance;
        }}
        .sender-handle {{
            font-size: 26px;
            font-weight: 500;
            color: {sender_handle_color}; /* Use dynamic sender handle color */
        }}
        .menu-dots {{
            display: flex;
            flex-direction: row;
            gap: 20px;
            margin-top: 16px;
        }}
        .menu-dots span {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: {menu_dots}; /* Use dynamic menu dots color */
        }}
        .message {{
            font-size: 42px;
            line-height: 1.65;
            color: {message_color}; /* Use dynamic message color */
            font-weight: 500;
            word-break: break-word;
        }}
        .profile + .message {{
            margin-top: 40px;
        }}
        .message .hashtag {{
            color: {hashtag}; /* Use dynamic hashtag color */
            font-weight: 600;
        }}
        .heart-badge {{
            position: absolute;
            right: 84px;
            bottom: -38px;
            width: 96px;
            height: 96px;
            border-radius: 50%;
            background: {heart_badge_bg}; /* Use dynamic heart badge background color */
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 20px 40px {heart_badge_shadow}; /* Use dynamic heart badge shadow color */
        }}
        .heart-badge svg {{
            width: 40px;
            height: 40px;
            fill: #FFFFFF;
        }}
        img.emoji {{
            height: 1.1em;
            width: 1.1em;
            margin: 0 .05em;
            vertical-align: -0.15em;
        }}
    </style>
    <script src="https://twemoji.maxcdn.com/v/latest/twemoji.min.js" crossorigin="anonymous"></script>
</head>
<body>
    <div class="stage" role="presentation">
        <article class="card" aria-labelledby="sender-name">
            <header class="profile">
                <div class="profile-left">
                    <div class="profile-meta">
                        <div class="sender-name" id="sender-name">{sender}</div>
                        <div class="sender-handle">{sender_handle}</div>
                    </div>
                </div>
                <div class="menu-dots" aria-hidden="true">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </header>
            <div class="message">{message_content}</div> <!-- Changed placeholder to message_content -->
            <div class="heart-badge" aria-hidden="true">
                <svg viewBox="0 0 24 24">
                    <path d="M12 21s-5.7-4.46-8.4-7.18C1.86 11.08 1 9.37 1 7.5 1 4.42 3.42 2 6.5 2 8.24 2 9.91 2.81 11 4.09 12.09 2.81 13.76 2 15.5 2 18.58 2 21 4.42 21 7.5c0 1.87-.86 3.58-2.6 6.32C17.7 16.54 12 21 12 21z"/>
                </svg>
            </div>
        </article>
    </div>
    <script>
      document.addEventListener("DOMContentLoaded", function() {{
          twemoji.parse(document.body, {{folder: "svg", ext: ".svg"}});
      }});
    </script>
</body>
</html>
"""

def generate_message_image(text: str, name: str = "Askout Bot") -> str:
    sender = name if (name and isinstance(name, str)) else "Askout Bot"
    timestamp = "Just now"
    sender_clean = sender.strip()
    sender_initial = sender_clean[:1].upper() if sender_clean else "A"
    slug_source = sender_clean if sender_clean and sender_clean.lower() != "anonymous" else "askoutbot"
    handle_slug = re.sub(r"[^a-z0-9]+", "", slug_source.lower().replace(" ", "")) or "askoutbot"
    sender_handle = f"@{handle_slug}"
    hashtagged = re.sub(r"(?<!\w)#([A-Za-z0-9_]+)", r'<span class="hashtag">#\1</span>', text)
    formatted_message = hashtagged.replace("\n", "<br>")

    selected_palette = random.choice(COLOR_PALETTES)
    sender_handle_color = selected_palette["sender_handle_color"] if "sender_handle_color" in selected_palette else "#3A9EC7" # Get sender_handle_color from palette or use default
    message_color = selected_palette["message_color"] # Get message_color from palette

    html_content = HTML_TEMPLATE.format(
        sender=sender,
        sender_initial=sender_initial,
        sender_handle=sender_handle,
        timestamp=timestamp,
        message_content=formatted_message, # Pass message_content instead of message
        sender_handle_color=sender_handle_color,
        message_color=message_color, # Pass message_color
        **{k: v for k, v in selected_palette.items() if k not in ['sender_handle_color', 'message_color']}
    )

    temp_dir = tempfile.gettempdir()
    file_id = uuid.uuid4().hex
    html_path = pathlib.Path(temp_dir) / f"msg_{file_id}.html"
    png_path = pathlib.Path(temp_dir) / f"msg_{file_id}.png"
    html_path.write_text(html_content, encoding="utf-8")

    options = {
        "format": "png",
        "width": "1300",
        "encoding": "UTF-8",
        "quiet": "",
    }

    try:
        imgkit.from_file(str(html_path), str(png_path), options=options)
        if not png_path.exists() or png_path.stat().st_size == 0:
            print("❌ Image generation failed: Output PNG not created.")
            return None
        return str(png_path)
    except Exception as ex:
        print(f"❌ Image generation failed: {ex}")
        return None
    finally:
        try:
            html_path.unlink(missing_ok=True)
        except Exception:
            pass


if __name__ == "__main__":
    img = generate_message_image("Hello 😃🔥✨🚀 This looks strong & modern!", "Copilot")
    print("Generated image path:", img)
