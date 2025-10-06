from flask import Flask, render_template_string, request, jsonify
import re

app = Flask(__name__)

# -------------------------------
# Helper Functions
# -------------------------------

def normalize_color(name):
    if not name: return ""
    name = name.strip().replace("-", "").replace(" ", "")
    mapping = {
        'darkgray':'#555555','darkgrey':'#555555','gray':'#888888','grey':'#888888',
        'lightgray':'#cccccc','lightgrey':'#cccccc',
        'purple':'purple','black':'black','white':'white','red':'red',
        'yellow':'yellow','blue':'blue','green':'green','cyan':'cyan','orange':'orange',
        'pink':'pink','brown':'brown','magenta':'magenta'
    }
    return mapping.get(name.lower(), name)

def extract_angle_bracket(text):
    matches = re.findall(r'<\s*([^>]+?)\s*>', text)
    for match in matches:
        if match.strip():
            return match.strip()
    return None

def extract_quoted(text):
    matches = re.findall(r'"([^"]*?)"', text)
    for match in matches:
        if match.strip():
            return match
    return None

# -------------------------------
# Shx Parser - SIMPLIFIED
# -------------------------------

def parse_shx(code):
    title = "My Website"
    bg_style = "background: linear-gradient(135deg, #3b82f6, #8b5cf6);"
    elements = []

    lines = code.splitlines()
    for line in lines:
        line = line.strip()
        if not line: continue

        # Page title
        if line.lower().startswith("page"):
            q = extract_quoted(line)
            if q: title = q
            continue

        # Background
        if line.lower().startswith("bg/color"):
            inside = extract_angle_bracket(line)
            if inside:
                parts = [normalize_color(p.strip()) for p in inside.split("/")]
                if len(parts) == 1:
                    bg_style = f"background-color: {parts[0]};"
                else:
                    bg_style = f"background: linear-gradient(135deg, {', '.join(parts)});"
            continue

        # Header
        if line.lower().startswith("header"):
            text = extract_quoted(line) or "Welcome"
            style = "color: white; text-align: center; font-size: 2.5rem; margin: 20px 0;"
            color = extract_angle_bracket(line)
            if color: style += f"color: {normalize_color(color)};"
            elements.append(f"<h1 style='{style}'>{text}</h1>")
            continue

        # Text
        if line.lower().startswith("text"):
            text = extract_quoted(line) or ""
            style = "color: white; margin: 10px 0; font-size: 1.1rem;"
            color = extract_angle_bracket(line)
            if color: style += f"color: {normalize_color(color)};"
            if "(center)" in line.lower(): style += "text-align: center;"
            elements.append(f"<p style='{style}'>{text}</p>")
            continue

        # List
        if line.lower().startswith("list"):
            text = extract_quoted(line) or extract_angle_bracket(line) or ""
            style = "color: white; margin: 5px 0;"
            color = extract_angle_bracket(line)
            if color: style += f"color: {normalize_color(color)};"
            elements.append(f"<li style='{style}'>{text}</li>")
            continue

        # Link
        if line.lower().startswith("link"):
            text = extract_quoted(line) or "Click Here"
            url = extract_angle_bracket(line) or "#"
            elements.append(f"<a href='{url}' target='_blank' style='color: #60a5fa; text-decoration: none; font-size: 1.1rem; display: block; margin: 10px 0;'>{text}</a>")
            continue

        # Image
        if line.lower().startswith("image"):
            url = extract_angle_bracket(line) or "https://via.placeholder.com/400x200"
            elements.append(f"<img src='{url}' style='max-width: 100%; height: auto; margin: 20px 0; border-radius: 10px;'>")
            continue

    # Wrap list items in ul if any
    if any('<li' in element for element in elements):
        new_elements = []
        temp_list = []
        for element in elements:
            if '<li' in element:
                temp_list.append(element)
            else:
                if temp_list:
                    new_elements.append(f"<ul style='color: white;'>{''.join(temp_list)}</ul>")
                    temp_list = []
                new_elements.append(element)
        if temp_list:
            new_elements.append(f"<ul style='color: white;'>{''.join(temp_list)}</ul>")
        elements = new_elements

    html = f"""
    <div style="{bg_style} padding: 40px 20px; min-height: 100vh; font-family: Arial, sans-serif;">
        <div style="max-width: 800px; margin: 0 auto;">
            {''.join(elements)}
        </div>
    </div>
    """
    return html, title

# -------------------------------
# SIMPLE Editor HTML Template
# -------------------------------

EDITOR_HTML = r"""
<!DOCTYPE html>
<html>
<head>
    <title>SHX Editor</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            margin: 0;
            padding: 20px;
            background: #1a1a1a;
            color: white;
            font-family: Arial, sans-serif;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .editor-area {
            background: #2d2d2d;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        #editor {
            width: 100%;
            height: 300px;
            background: #1a1a1a;
            color: white;
            border: 1px solid #444;
            border-radius: 5px;
            padding: 15px;
            font-family: monospace;
            font-size: 14px;
            resize: vertical;
        }
        button {
            background: #3b82f6;
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 5px;
            font-size: 16px;
            cursor: pointer;
            margin-top: 10px;
        }
        button:hover {
            background: #2563eb;
        }
        .preview-area {
            background: #2d2d2d;
            padding: 20px;
            border-radius: 10px;
        }
        #preview {
            background: white;
            border-radius: 5px;
            min-height: 500px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1 style="text-align: center; color: #3b82f6;">✨ SHX Editor ✨</h1>
        
        <div class="editor-area">
            <h3>Edit Your SHX Code:</h3>
            <textarea id="editor" placeholder="Enter your SHX code here...">page "My Awesome Website"
bg/color <blue/purple>
header "Welcome to SHX!" <white> (center)
text "This is a simple website builder" <white> (center)
list "Easy to use"
list "No coding required"
list "Beautiful results"
link "Learn More" <https://example.com>
image <https://via.placeholder.com/400x200/3b82f6/ffffff?text=Beautiful+Image></textarea>
            <button onclick="runCode()">🚀 Run Code</button>
        </div>

        <div class="preview-area">
            <h3>Live Preview:</h3>
            <div id="preview">
                <div style="padding: 20px; text-align: center; color: #666;">
                    Click "Run Code" to see your website here!
                </div>
            </div>
        </div>
    </div>

    <script>
        function runCode() {
            const code = document.getElementById('editor').value;
            const preview = document.getElementById('preview');
            
            // Show loading
            preview.innerHTML = '<div style="padding: 20px; text-align: center; color: #666;">Loading...</div>';
            
            fetch('/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: 'code=' + encodeURIComponent(code)
            })
            .then(response => response.json())
            .then(data => {
                preview.innerHTML = data.html;
            })
            .catch(error => {
                preview.innerHTML = '<div style="padding: 20px; color: red;">Error: ' + error + '</div>';
            });
        }

        // Run code when page loads
        setTimeout(runCode, 1000);
    </script>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def editor():
    if request.method == "POST":
        code = request.form.get("code", "")
        try:
            html, title = parse_shx(code)
            return jsonify({'html': html, 'title': title})
        except Exception as e:
            return jsonify({'html': f'<div style="color: red; padding: 20px;">Error: {str(e)}</div>', 'title': 'Error'})
    
    # Default code for GET request
    return render_template_string(EDITOR_HTML)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)