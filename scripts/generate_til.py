import os
import glob
import markdown
import yaml
from collections import defaultdict
from datetime import datetime, timedelta, timezone
import re

POSTS_DIR = 'til/posts'
TAGS_DIR = 'til/tags'
INDEX_FILE = 'til/index.html'
STYLE_FILE = 'til/til-style.css'

os.makedirs(TAGS_DIR, exist_ok=True)

posts = []
tags_dict = defaultdict(list)

# Helper for IST
IST = timezone(timedelta(hours=5, minutes=30))

def slugify(text):
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')

def parse_slug_from_filename(filename):
    # expects yyyy-mm-dd-slug.md or slug.md
    base = os.path.basename(filename)
    if base.count('-') >= 3 and base[:4].isdigit():
        parts = base.split('-')
        slug = '-'.join(parts[3:]).replace('.md', '')
    else:
        slug = base.replace('.md', '')
    return slug

def parse_date_from_filename(filename):
    # expects yyyy-mm-dd-slug.md
    base = os.path.basename(filename)
    parts = base.split('-')
    if len(parts) >= 3 and parts[0].isdigit() and parts[1].isdigit() and parts[2].isdigit():
        year, month, day = parts[0], parts[1], parts[2]
        return datetime(int(year), int(month), int(day), tzinfo=IST)
    else:
        return datetime.now(IST)

# Parse all TIL markdown files
for md_file in sorted(glob.glob(f"{POSTS_DIR}/*.md")):
    with open(md_file, encoding="utf-8") as f:
        content = f.read()
    try:
        _, fm, body = content.split('---', 2)
    except ValueError:
        print(f"Skipping {md_file}: invalid frontmatter")
        continue
    meta = yaml.safe_load(fm)
    # Get slug from filename
    slug = parse_slug_from_filename(md_file)
    # Get date from filename if present, else use now
    date_obj = parse_date_from_filename(md_file)
    html_body = markdown.markdown(body, extensions=['fenced_code', 'codehilite'])
    post = {
        'title': meta['title'],
        'date': date_obj,
        'date_str': date_obj.strftime('%Y-%m-%d'),
        'tags': meta.get('tags', []),
        'collection': meta.get('collection', None),
        'body': html_body,
        'filename': os.path.basename(md_file),
        'slug': slug
    }
    posts.append(post)
    for tag in post['tags']:
        tags_dict[tag].append(post)

# Sort posts by date ascending for navigation (oldest to newest)
posts.sort(key=lambda p: p['date'])

# Generate tag pages
for tag, tag_posts in tags_dict.items():
    tag_posts_sorted = sorted(tag_posts, key=lambda p: p['date'], reverse=True)
    with open(f"{TAGS_DIR}/{tag}.html", 'w', encoding="utf-8") as f:
        f.write(f"""<!DOCTYPE html>
<html>
<head>
  <link rel="stylesheet" href="../til-style.css">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/themes/prism.min.css">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
  <script defer src="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/prism.min.js"></script>
  <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
  <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"></script>
  <script>
    document.addEventListener("DOMContentLoaded", function() {{
      if (window.renderMathInElement) {{
        renderMathInElement(document.body, {{
          delimiters: [
            {{left: '$$', right: '$$', display: true}},
            {{left: '$', right: '$', display: false}}
          ]
        }});
      }}
    }});
  </script>
  <title>TIL: {tag}</title>
</head>
<body>
  <h1>#{tag}</h1>
  <ul class="til-list"><li><a href="../">← TIL</a></li>
""")
        for post in tag_posts_sorted:
            url = f"../posts/{post['slug']}/"
            f.write(f'<li><a href="{url}">{post["title"]}</a> <span class="til-date">{post["date_str"]}</span></li>\n')
        f.write("</ul>\n</body></html>")

# Generate main index.html (recent TILs: newest first)
posts_desc = sorted(posts, key=lambda p: p['date'], reverse=True)
with open(INDEX_FILE, 'w', encoding="utf-8") as f:
    f.write(f"""<!DOCTYPE html>
<html>
<head>
  <link rel="stylesheet" href="til-style.css">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/themes/prism.min.css">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
  <script defer src="https://cdn.jsdelivr.net/npm/prismjs@1.29.0/prism.min.js"></script>
  <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
  <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"></script>
  <script>
    document.addEventListener("DOMContentLoaded", function() {{
      if (window.renderMathInElement) {{
        renderMathInElement(document.body, {{
          delimiters: [
            {{left: '$$', right: '$$', display: true}},
            {{left: '$', right: '$', display: false}}
          ]
        }});
      }}
    }});
  </script>
  <title>🧠 TIL</title>
</head>
<body>
  <h1>Gaurav: TIL</h1>
  <p>A TIL: <strong>Today I Learned</strong>, also check out my <a href="https://gaurv.me/blog/">blog</a>.</p>
  <div class="til-search-container">
    <form onsubmit="filterTILs(); return false;" style="display: flex; width: 100%;">
      <input type="search" id="til-search" placeholder="Search TILs..." autofocus>
      <button id="til-search-btn" type="submit">Search</button>
    </form>
  </div>
  <div class="til-tags">\n""")
    # Tags bar
    for tag, tag_posts in sorted(tags_dict.items()):
        f.write(f'<a class="til-tag" href="tags/{tag}.html">{tag} ({len(tag_posts)})</a><span class="til-tag-sep">• </span>')
    f.write("</div>\n")

    # Recent TILs
    f.write('<h2>Recent TILs</h2>\n<ul class="til-list" id="til-list">\n')
    for post in posts_desc[:10]:
        url = f"posts/{post['slug']}/"
        f.write(f'<li><a href="{url}">{post["title"]}</a> <span class="til-date">{post["date_str"]}</span></li>\n')
    f.write("</ul>\n")

    # All TILs (hidden, for search)
    f.write('<h2 style="display:none;">All TILs</h2>\n<ul class="til-list" id="all-tils" style="display:none;">\n')
    for post in posts_desc:
        url = f"posts/{post['slug']}/"
        f.write(f'<li><a href="{url}">{post["title"]}</a> <span class="til-date">{post["date_str"]}</span></li>\n')
    f.write("</ul>\n")

    # Minimal JS for search (optional, can be removed for pure HTML)
    f.write("""
<script>
function filterTILs() {
  var input = document.getElementById('til-search');
  var filter = input.value.toLowerCase();
  var ul = document.getElementById('til-list');
  ul.innerHTML = '';
  var allLis = document.getElementById('all-tils').getElementsByTagName('li');
  var count = 0;
  for (var i = 0; i < allLis.length; i++) {
    var txt = allLis[i].textContent || allLis[i].innerText;
    if (txt.toLowerCase().indexOf(filter) > -1 && count < 10) {
      ul.appendChild(allLis[i].cloneNode(true));
      count++;
    }
  }
}
</script>
""")
    f.write("</body></html>")

# Generate HTML for each TIL post with slug-based URLs and sidebar with prev/next links
for i, post in enumerate(posts):
    slug = post['slug']
    out_dir = f"til/posts/{slug}"
    os.makedirs(out_dir, exist_ok=True)
    prev_post = posts[i+1] if i < len(posts)-1 else None
    next_post = posts[i-1] if i > 0 else None
    # Use the post's date for display, not current time
    display_time = post['date'].strftime('%d %B %Y (IST)')
    with open(f"{out_dir}/index.html", "w", encoding="utf-8") as f_post:
        f_post.write(f"""<!DOCTYPE html>
<html>
<head>
   <meta name=\"fediverse:creator\" content=\"@wiredguy@mastodon.social\">                  
  <link rel=\"stylesheet\" href=\"../../til-style.css\">
  <link rel=\"stylesheet\" href=\"https://cdn.jsdelivr.net/npm/prismjs@1.29.0/themes/prism.min.css\">
  <link rel=\"stylesheet\" href=\"https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css\">
  <script defer src=\"https://cdn.jsdelivr.net/npm/prismjs@1.29.0/prism.min.js\"></script>
  <script defer src=\"https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js\"></script>
  <script defer src=\"https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js\"></script>
  <script src=\"https://challenges.cloudflare.com/turnstile/v0/api.js\" async defer></script>
  <script>
    document.addEventListener(\"DOMContentLoaded\", function() {{
      if (window.renderMathInElement) {{
        renderMathInElement(document.body, {{
          delimiters: [
            {{left: '$$', right: '$$', display: true}},
            {{left: '$', right: '$', display: false}}
          ]
        }});
      }}
    }});
  </script>
  <title>{post['title']}</title>
  <style>
    .upvote-btn {{
      display: inline-flex;
      align-items: center;
      cursor: pointer;
      border: none;
      background: none;
      padding: 0.2em 0.4em;
      margin-left: 0.5em;
      transition: color 0.2s, transform 0.1s;
      color: #aaa;
      font-size: 1.5em;
      outline: none;
    }}
    .upvote-btn:active {{
      transform: scale(1.18);
    }}
    .upvote-btn.upvoted {{
      color: #4b4e50;
      font-weight: bold;
      /* transform: scale(1.2); -- handled by JS for pop effect */
    }}
    .upvote-arrow {{
      width: 1.2em;
      height: 1.2em;
      display: inline-block;
      vertical-align: middle;
      transition: stroke 0.18s, fill 0.18s;
      fill: #d1d1d1;
      stroke: #7d8082;
    }}
    .upvote-btn.upvoted .upvote-arrow {{
      stroke: #4b4e50;
      fill: #4b4e50;
    }}
    .upvote-btn.pop {{
      animation: upvote-pop 0.18s cubic-bezier(.4,1.6,.6,1) 1;
    }}
    @keyframes upvote-pop {{
      0% {{ transform: scale(1); }}
      60% {{ transform: scale(1.28); }}
      100% {{ transform: scale(1); }}
    }}
    /* ...existing code... */
  </style>
</head>
<body>
<main>
  <h1>{post['title']}</h1>
  <div class=\"til-body\">{post['body']}

  <!-- Perlin noise image row (only for the perlin-noise post) -->
  {'' if post['slug'] != 'perlin-noise' else '''
  <div style=\"display: flex; justify-content: center; gap: 2em; margin: 2em 0;\">
    <figure style=\"flex: 1; text-align: center; max-width: 200px;\">
      <img src=\"https://pub-91e1a485198740aabff1705e89606dc3.r2.dev/perlin%20noise/input_image.jpg\" alt=\"Input Image\" style=\"width: 100%; height: auto; border-radius: 8px; box-shadow: 0 2px 8px #0001;\">
      <figcaption style=\"margin-top: 0.7em; font-size: 1em; color: #555;\">Input Image (400x400)</figcaption>
    </figure>
    <figure style=\"flex: 1; text-align: center; max-width: 200px;\">
      <img src=\"https://pub-91e1a485198740aabff1705e89606dc3.r2.dev/perlin%20noise/fractal_terrain_400x400.png\" alt=\"x Perlin noise\" style=\"width: 100%; height: auto; border-radius: 8px; box-shadow: 0 2px 8px #0001;\">
      <figcaption style=\"margin-top: 0.7em; font-size: 1em; color: #555;\">x Perlin noise</figcaption>
    </figure>
    <figure style=\"flex: 1; text-align: center; max-width: 200px;\">
      <img src=\"https://pub-91e1a485198740aabff1705e89606dc3.r2.dev/perlin%20noise/output_distorted_400x400.png\" alt=\"Output Image\" style=\"width: 100%; height: auto; border-radius: 8px; box-shadow: 0 2px 8px #0001;\">
      <figcaption style=\"margin-top: 0.7em; font-size: 1em; color: #555;\">= Output Image</figcaption>
    </figure>
  </div>
  '''}
  </div>
  <div class=\"til-date\">Posted on {display_time} · Follow me on <a href=\"https://x.com/wiredguys\">Twitter</a> or <a rel=\"me\" href=\"https://mastodon.social/@wiredguy\">Mastodon</a></div>
  <button class="upvote-btn" id="upvote-btn" title="Upvote this TIL" aria-pressed="false">
  <svg class="upvote-arrow" viewBox="0 0 24 24" fill="#d1d1d1" stroke="#7d8082" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <polygon points="12,4 19,20 5,20" />
  </svg>
</button>

<button class="share-btn" id="share-btn" title="Share this TIL">
  <svg class="share-icon" viewBox="0 0 24 24" fill="none" stroke="#555" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <circle cx="18" cy="5" r="3" />
    <circle cx="6" cy="12" r="3" />
    <circle cx="18" cy="19" r="3" />
    <line x1="8.59" y1="13.51" x2="15.42" y2="17.49" />
    <line x1="15.41" y1="6.51" x2="8.59" y2="10.49" />
  </svg>
</button>

<div id="turnstile-container">
  <div id="cf-turnstile" class="cf-turnstile" data-sitekey="0x4AAAAAABiDRLV2JxUJ_Qv6"></div>
</div>
  <ul class=\"til-list\">
    <li><a href=\"../../index.html\">← TIL</a></li>
  </ul>
  <div class=\"til-sidebar\">
    <h5>Jump to</h5>
    <ul>
""")
        if prev_post:
            prev_slug = prev_post['slug']
            prev_url = f"../{prev_slug}/"
            f_post.write(f'      <li><a href="{prev_url}">Next: {prev_post["title"]} →</a></li>\n')
        if next_post:
            next_slug = next_post['slug']
            next_url = f"../{next_slug}/"
            f_post.write(f'      <li><a href="{next_url}">← Previous: {next_post["title"]}</a></li>\n')
        f_post.write("""    </ul>
  </div>
  <script>
    // --- Upvote logic ---
    const slug = "{slug}";
    const upvoteBtn = document.getElementById('upvote-btn');
    const shareBtn = document.getElementById('share-btn');
    const turnstileContainer = document.getElementById('turnstile-container');
    const sessionKey = 'cf_upvote_verified';
    const upvotedKey = 'til_upvoted_' + slug;
    function isSessionVerified() {{
      return localStorage.getItem(sessionKey) === '1';
    }}
    function setSessionVerified() {{
      localStorage.setItem(sessionKey, '1');
    }}
    function isUpvoted() {{
      return localStorage.getItem(upvotedKey) === '1';
    }}
    function setUpvoted() {{
      localStorage.setItem(upvotedKey, '1');
      upvoteBtn.classList.add('upvoted');
      upvoteBtn.setAttribute('aria-pressed', 'true');
      // Animate arrow fill and pop
      const svg = upvoteBtn.querySelector('.upvote-arrow');
      if (svg) {{
        svg.setAttribute('fill', '#4b4e50');
        svg.setAttribute('stroke', '#4b4e50');
      }}
      upvoteBtn.classList.add('pop');
      setTimeout(() => upvoteBtn.classList.remove('pop'), 180);
    }}
    function resetUpvoteBtn() {{
      upvoteBtn.classList.remove('upvoted');
      upvoteBtn.setAttribute('aria-pressed', 'false');
      const svg = upvoteBtn.querySelector('.upvote-arrow');
      if (svg) {{
        svg.setAttribute('fill', '#d1d1d1');
        svg.setAttribute('stroke', '#7d8082');
      }}
    }}
    if (isUpvoted()) {{
      setUpvoted();
      upvoteBtn.disabled = true;
    }} else {{
      resetUpvoteBtn();
      upvoteBtn.disabled = false;
    }}
    upvoteBtn.addEventListener('click', function() {{
      if (isUpvoted()) return;
      // Animate pop even before upvote completes
      upvoteBtn.classList.add('pop');
      setTimeout(() => upvoteBtn.classList.remove('pop'), 180);
      if (isSessionVerified()) {{
        sendUpvote();
      }} else {{
        turnstileContainer.style.display = 'block';
      }}
    }});
    shareBtn.addEventListener('click', function() {{
      if (navigator.share) {{
        navigator.share({{
          title: document.title,
          url: window.location.href
        }});
      }} else {{
        navigator.clipboard.writeText(window.location.href);
        shareBtn.classList.add('shared');
        shareBtn.title = 'Copied!';
        setTimeout(() => {{ shareBtn.classList.remove('shared'); shareBtn.title = 'Share this TIL'; }}, 1200);
      }}
    }});
    window.turnstileCallback = function(token) {
      // POST to backend for verification and upvote
      fetch('/api/upvote', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({slug: slug, token: token})
      }).then(r => r.json()).then(data => {
        if (data.success) {
          setSessionVerified();
          setUpvoted();
          upvoteBtn.disabled = true;
          // Fire Cloudflare Analytics event
          if (window.cfAnalytics && window.cfAnalytics.trackEvent) {
            window.cfAnalytics.trackEvent('upvote', {slug: slug, type: 'til'});
          }
        } else {
          alert('Verification failed.');
        }
        turnstileContainer.style.display = 'none';
      });
    }
    function sendUpvote() {
      fetch('/api/upvote', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({slug: slug})
      }).then r => r.json()).then(data => {
        if (data.success) {
          setUpvoted();
          upvoteBtn.disabled = true;
          if (window.cfAnalytics && window.cfAnalytics.trackEvent) {
            window.cfAnalytics.trackEvent('upvote', {slug: slug, type: 'til'});
          }
        } else {
          alert('Upvote failed.');
        }
      });
    }
    // Cloudflare Turnstile callback
    window.onloadTurnstile = function() {
      if (window.turnstile) {
        window.turnstile.render('#cf-turnstile', {
          sitekey: '0x4AAAAAABiDRLV2JxUJ_Qv6',
          callback: window.turnstileCallback
        });
      }
    }
    // Listen for Turnstile ready
    document.addEventListener('DOMContentLoaded', function() {
      if (window.turnstile) window.onloadTurnstile();
    });
  </script>
</main>
</body>
</html>
""")
