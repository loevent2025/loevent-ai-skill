"""海报文字可编辑链路:消字 + 文字图层渲染(替代原 loevent 前端那步)。

两个子命令:
  erase  —— 调 gemini-2.5-flash-image 把图上文字抹掉,得到干净底图(需计费档 image key)。
  render —— 用 Pillow 把文字图层按位置/颜色合成回干净底图,得到最终海报(纯本地,不需 key)。

中文字体走「B 方案」:运行时探测用户本机系统中文字体(不打包、不下载、只读用户已装的字),
和 loevent 前端"系统字体兜底"一致。探不到才提示用户装一个或放进 assets/fonts/。

典型编排(由 SKILL.md 指导 Claude 串):
  1) 出图得到 poster_N.png(文字已烤进像素)
  2) Claude 多模态看 poster_N.png → 写出文字图层 poster_text_layers.json
  3) erase poster_N.png → poster_N_clean.png
  4) render poster_N_clean.png + poster_text_layers.json → poster_N_final.png
  5) 用户要改字 → Claude 改 json → 再 render 一次
"""

import argparse
import asyncio
import base64
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from engine import context_local, get_llm_client  # noqa: E402
from engine.model_config import MODEL_POSTER_EDIT_IMAGE  # noqa: E402

ERASE_PROMPT = (
    "Using the provided image, remove all text elements only. "
    "Keep everything else exactly the same — preserve all colors, "
    "textures, background graphics, lighting, and layout. "
    "Do not change the aspect ratio."
)

# 系统中文字体候选(各平台,按观感优先级);.ttc 给出要用的 index。
# 探测时逐个试读,用第一个 Pillow 能打开的——和 loevent 前端的系统字体兜底同理。
SYSTEM_CJK_FONT_CANDIDATES = [
    ("/System/Library/Fonts/PingFang.ttc", 0),
    ("/System/Library/Fonts/Hiragino Sans GB.ttc", 0),
    ("/System/Library/Fonts/STHeiti Medium.ttc", 0),
    ("/System/Library/Fonts/Supplemental/Songti.ttc", 0),
    ("/System/Library/Fonts/Supplemental/Arial Unicode.ttf", 0),
    ("C:/Windows/Fonts/msyh.ttc", 0),
    ("C:/Windows/Fonts/msyhbd.ttc", 0),
    ("C:/Windows/Fonts/simhei.ttf", 0),
    ("C:/Windows/Fonts/simsun.ttc", 0),
    ("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", 0),
    ("/usr/share/fonts/opentype/noto/NotoSansCJKsc-Regular.otf", 0),
    ("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 0),
]


def ocr_text_blocks(image_path: Path) -> list:
    """调 Google Cloud Vision OCR,返回每块文字的内容 + 归一化精确框。

    返回 [{text, box:{x,y,w,h}}](x/y/w/h 都是 0~1,相对图片宽/高)。
    位置精度交给 OCR(本职),内容/角色/配色由上层(Claude)结合 event.json 再定。

    认证走 service account(和 loevent 后端一致):把 GOOGLE_APPLICATION_CREDENTIALS
    指到 GCV 服务账号 JSON 的路径,客户端库自动读取。该 JSON 是密钥,放仓库外或确保被
    .gitignore 挡掉,**绝不能提交**。
    """
    from PIL import Image

    if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "").strip():
        raise RuntimeError(
            "缺少 GOOGLE_APPLICATION_CREDENTIALS(指向 Google Cloud Vision 服务账号 JSON 的路径,"
            "独立于 GEMINI_API_KEY)。\n在 .env 里设 "
            "GOOGLE_APPLICATION_CREDENTIALS=/绝对路径/你的-vision-service-account.json;"
            "该 JSON 是密钥,别提交进仓库。"
        )
    try:
        from google.cloud import vision
    except ImportError as missing:
        raise RuntimeError("未安装 google-cloud-vision,先 pip install google-cloud-vision") from missing

    with Image.open(image_path) as poster:
        width, height = poster.size

    client = vision.ImageAnnotatorClient()  # 自动读取 GOOGLE_APPLICATION_CREDENTIALS
    response = client.document_text_detection(image=vision.Image(content=Path(image_path).read_bytes()))
    if response.error.message:
        raise RuntimeError(f"Google Cloud Vision 报错: {response.error.message}")

    blocks = []
    for annotation in response.text_annotations[1:]:  # [0] 是整图全文,跳过;[1:] 逐块带框
        vertices = annotation.bounding_poly.vertices
        xs = [vertex.x for vertex in vertices]
        ys = [vertex.y for vertex in vertices]
        if not xs or not ys:
            continue
        left, right, top, bottom = min(xs), max(xs), min(ys), max(ys)
        blocks.append({
            "text": annotation.description,
            "box": {
                "x": left / width,
                "y": top / height,
                "w": (right - left) / width,
                "h": (bottom - top) / height,
            },
        })
    return blocks


def find_cjk_font():
    """返回一个 Pillow 能打开的中文字体 (path, index)。

    优先级:LOEVENT_POSTER_FONT 环境变量 → 仓库 assets/fonts/ 里自带的 → 系统字体候选。
    都没有则抛错并提示用户怎么补。
    """
    from PIL import ImageFont

    def _loadable(path, index):
        try:
            ImageFont.truetype(path, 32, index=index)
            return True
        except Exception:
            return False

    override = os.environ.get("LOEVENT_POSTER_FONT", "").strip()
    if override and _loadable(override, 0):
        return override, 0

    bundled_dir = Path(__file__).resolve().parent.parent / "assets" / "fonts"
    if bundled_dir.is_dir():
        for font_file in sorted(bundled_dir.glob("*.[ot]t[fc]")):
            if _loadable(str(font_file), 0):
                return str(font_file), 0

    for path, index in SYSTEM_CJK_FONT_CANDIDATES:
        if os.path.exists(path) and _loadable(path, index):
            return path, index

    raise RuntimeError(
        "没找到可用的中文字体。请任选其一:\n"
        "  ① 装一个系统中文字体(Mac/Windows 一般自带);\n"
        "  ② 放一只 .otf/.ttf 到 skill-poster/assets/fonts/;\n"
        "  ③ 设环境变量 LOEVENT_POSTER_FONT=/绝对路径/某字体.otf。"
    )


async def erase_text_from_poster(image_path: Path) -> Path:
    """调图像编辑模型把海报上的文字抹掉,存成 <name>_clean.png 返回其路径。"""
    from PIL import Image

    source_image = Image.open(image_path).convert("RGB")
    width, height = source_image.size

    client = get_llm_client(image_model=MODEL_POSTER_EDIT_IMAGE)
    # 注:消字模型 gemini-2.5-flash-image 原生 ~1K,不支持 2K/4K,故只传它认的 aspect_ratio;
    # 这也意味着「文字可编辑」成品被这一步限到 ~1K(见 SKILL.md 取舍说明)。
    response = await client.generate_image(
        module="poster_text_erase",
        prompt=[ERASE_PROMPT, source_image],
        aspect_ratio=_closest_aspect_ratio(width, height),
    )

    clean_path = image_path.with_name(f"{image_path.stem}_clean.png")
    clean_path.write_bytes(response.image_bytes)
    return clean_path


def render_text_layers(clean_image_path: Path, layers: list, output_path: Path) -> Path:
    """用 Pillow 把文字图层合成到干净底图上。

    每个 layer:{text, x, y, font_scale, color, bold, align}
      x / y      —— 文字锚点的归一化坐标(0~1),相对图片宽/高
      font_scale —— 字号占图片高度的比例(如 0.07)
      align      —— left / center / right(决定锚点在文字框的哪侧)
    """
    from PIL import Image, ImageDraw, ImageFont

    poster = Image.open(clean_image_path).convert("RGB")
    width, height = poster.size
    draw = ImageDraw.Draw(poster)
    font_path, font_index = find_cjk_font()

    anchor_by_align = {"left": "la", "center": "ma", "right": "ra"}

    for layer in layers:
        text = str(layer.get("text", "")).strip()
        if not text:
            continue
        font_size = max(8, int(float(layer.get("font_scale", 0.05)) * height))
        font = ImageFont.truetype(font_path, font_size, index=font_index)
        # 防溢出:文字超过图宽 92% 就按比例缩字,别让标题顶到/裁出边缘
        max_text_width = width * 0.92
        text_width = draw.textlength(text, font=font)
        if text_width > max_text_width:
            font_size = max(8, int(font_size * max_text_width / text_width))
            font = ImageFont.truetype(font_path, font_size, index=font_index)
        # y 补 +font_size*0.05:对齐 HTML/canvas 里 line-height 1.1 的半行距,保证"编辑器拖好位置→render"竖直一致
        position = (float(layer.get("x", 0.5)) * width,
                    float(layer.get("y", 0.5)) * height + font_size * 0.05)
        align = layer.get("align", "center")
        anchor = anchor_by_align.get(align, "ma")
        color = layer.get("color", "#FFFFFF")
        stroke = max(1, font_size // 24) if layer.get("bold") else 0

        draw.text(
            position, text, font=font, fill=color, anchor=anchor,
            stroke_width=stroke, stroke_fill=color,
        )

    poster.save(output_path)
    return output_path


_EDIT_HTML_TEMPLATE = """<!doctype html>
<html lang="zh"><head><meta charset="utf-8"><title>海报文字编辑</title>
<style>
  body{margin:0;background:#1b1b1f;color:#e8e8ea;font-family:-apple-system,'PingFang SC',sans-serif}
  #bar{position:sticky;top:0;background:#111;padding:10px 14px;display:flex;gap:10px;align-items:center;flex-wrap:wrap;z-index:10}
  #bar button{padding:6px 12px;border:0;border-radius:6px;background:#3b6df0;color:#fff;cursor:pointer}
  #hint{opacity:.7;font-size:13px}
  #wrap{padding:16px;display:flex;gap:16px;align-items:flex-start;flex-wrap:wrap}
  #stage{position:relative;background:#000;flex:none;box-shadow:0 4px 24px rgba(0,0,0,.5)}
  #stage img{display:block;width:100%;height:100%;pointer-events:none}
  .layer{position:absolute;white-space:nowrap;cursor:move;outline:1px dashed rgba(255,255,255,.25);line-height:1.1}
  .layer:focus{outline:1px solid #4af;background:rgba(60,120,240,.12)}
  #out{flex:1;min-width:280px;height:60vh;background:#0d0d10;color:#9fe89f;border:1px solid #333;border-radius:6px;padding:10px;font-family:monospace;font-size:12px}
</style></head>
<body>
<div id="bar">
  <strong>海报文字编辑</strong>
  <span id="hint">点字→改内容 · 拖字→改位置 · 改完点按钮</span>
  <button onclick="saveImage()">★ 保存为图片</button>
  <button onclick="exportJSON()">① 导出图层 JSON</button>
  <button onclick="copyOut()">② 复制(贴回 Claude 重渲高清成品)</button>
</div>
<div id="wrap">
  <div id="stage" style="width:__W__px;height:__H__px"><img src="data:image/png;base64,__IMG__"></div>
  <textarea id="out" readonly placeholder="点「导出图层 JSON」后这里出现更新后的图层,复制它发给 Claude。"></textarea>
</div>
<script>
const W=__W__, H=__H__, layers=__LAYERS__;
const stage=document.getElementById('stage');
const anchorTx={left:'translateX(0)',center:'translateX(-50%)',right:'translateX(-100%)'};
layers.forEach(L=>{
  const d=document.createElement('div');
  d.className='layer'; d.contentEditable='true'; d.spellcheck=false; d.textContent=L.text||'';
  d.dataset.align=L.align||'center'; d.dataset.color=L.color||'#FFFFFF';
  d.style.left=(L.x*W)+'px'; d.style.top=(L.y*H)+'px';
  d.style.transform=anchorTx[L.align||'center'];
  d.style.fontSize=((L.font_scale||0.05)*H)+'px';
  d.style.color=L.color||'#FFFFFF'; d.style.fontWeight=L.bold?'700':'400'; d.style.textAlign=L.align||'center';
  enableDrag(d); stage.appendChild(d);
});
function enableDrag(d){
  d.addEventListener('mousedown',e=>{
    if(document.activeElement===d) return;
    let moved=false, sx=e.clientX, sy=e.clientY, ox=parseFloat(d.style.left), oy=parseFloat(d.style.top);
    const mv=ev=>{ if(Math.abs(ev.clientX-sx)+Math.abs(ev.clientY-sy)>3){moved=true; d.blur();}
      if(moved){d.style.left=(ox+ev.clientX-sx)+'px'; d.style.top=(oy+ev.clientY-sy)+'px';} };
    const up=()=>{document.removeEventListener('mousemove',mv);document.removeEventListener('mouseup',up);};
    document.addEventListener('mousemove',mv); document.addEventListener('mouseup',up);
  });
}
function exportJSON(){
  const out=[...stage.querySelectorAll('.layer')].map(d=>({
    text:d.textContent,
    x:+(parseFloat(d.style.left)/W).toFixed(4), y:+(parseFloat(d.style.top)/H).toFixed(4),
    font_scale:+(parseFloat(d.style.fontSize)/H).toFixed(4),
    color:d.dataset.color, bold:d.style.fontWeight==='700', align:d.dataset.align
  }));
  document.getElementById('out').value=JSON.stringify({layers:out},null,2);
}
function copyOut(){exportJSON(); const t=document.getElementById('out'); t.select(); document.execCommand('copy');}
function saveImage(){
  const img=stage.querySelector('img');
  const c=document.createElement('canvas'); c.width=W; c.height=H;
  const ctx=c.getContext('2d');
  ctx.drawImage(img,0,0,W,H);
  stage.querySelectorAll('.layer').forEach(d=>{
    const fs=parseFloat(d.style.fontSize);
    ctx.font=(d.style.fontWeight==='700'?'700 ':'400 ')+fs+"px -apple-system,'PingFang SC',sans-serif";
    ctx.fillStyle=d.dataset.color||'#FFFFFF';
    ctx.textAlign=d.dataset.align||'center';
    ctx.textBaseline='top';
    // y 补 line-height(1.1) 的半行距,对齐编辑器里 CSS 文字的视觉顶部(否则会偏上 ~5% 字号)
    const x=parseFloat(d.style.left), y=parseFloat(d.style.top)+fs*0.05;
    (d.innerText||d.textContent||'').split('\\n').forEach((ln,i)=>ctx.fillText(ln,x,y+i*fs*1.1));
  });
  const a=document.createElement('a'); a.download='poster.png';
  a.href=c.toDataURL('image/png'); a.click();
}
</script></body></html>"""


def render_edit_html(clean_image_path: Path, layers: list, output_path: Path) -> Path:
    """生成自包含 HTML:干净底图当背景 + 文字层可改内容/可拖位 + 导出更新后的图层 JSON。

    底图以 base64 内嵌,单文件可直接在浏览器打开,不依赖任何相对路径(避免"图找不到")。
    用户在浏览器里改完,点导出/复制把图层 JSON 贴回 Claude,再 render 出高清成品 PNG。
    """
    from PIL import Image

    with Image.open(clean_image_path) as poster:
        width, height = poster.size
    image_b64 = base64.b64encode(Path(clean_image_path).read_bytes()).decode("ascii")

    html = (_EDIT_HTML_TEMPLATE
            .replace("__W__", str(width))
            .replace("__H__", str(height))
            .replace("__IMG__", image_b64)
            # 注入 <script> 前转义 < > &:防文字含 </script> 闭合脚本块/XSS(< 在 JS 里仍解析回 <,JSON 合法)
            .replace("__LAYERS__", json.dumps(layers, ensure_ascii=False)
                     .replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")))
    output_path.write_text(html, encoding="utf-8")
    return output_path


def _closest_aspect_ratio(width: int, height: int) -> str:
    ratio = width / height if height else 1.0
    options = {"1:1": 1.0, "9:16": 9 / 16, "16:9": 16 / 9, "4:5": 4 / 5, "3:4": 3 / 4}
    best = min(options, key=lambda name: abs(options[name] - ratio))
    return best


def _resolve_layers(args) -> list:
    if args.layers:
        data = json.loads(Path(args.layers).read_text(encoding="utf-8"))
    else:
        data = context_local.load_json("poster_text_layers") or {}
    return data.get("layers", data if isinstance(data, list) else [])


def main() -> int:
    parser = argparse.ArgumentParser(description="海报消字 + 文字图层渲染")
    sub = parser.add_subparsers(dest="command", required=True)

    ocr_parser = sub.add_parser("ocr", help="GCV OCR:取文字内容 + 精确归一化框")
    ocr_parser.add_argument("--image", required=True, help="带文字的海报 PNG 路径")

    erase_parser = sub.add_parser("erase", help="抹掉海报上的文字,得到干净底图")
    erase_parser.add_argument("--image", required=True, help="带文字的海报 PNG 路径")

    render_parser = sub.add_parser("render", help="把文字图层合成到干净底图")
    render_parser.add_argument("--image", required=True, help="干净底图 PNG 路径")
    render_parser.add_argument("--layers", help="文字图层 JSON(缺省读工作目录 poster_text_layers.json)")
    render_parser.add_argument("--out", help="输出路径(缺省 <image 去掉 _clean>_final.png)")

    preview_parser = sub.add_parser("preview", help="生成可在浏览器里改字/拖位的 HTML 预览")
    preview_parser.add_argument("--image", required=True, help="干净底图 PNG(poster_N_clean.png)")
    preview_parser.add_argument("--layers", help="文字图层 JSON(缺省读工作目录 poster_text_layers.json)")
    preview_parser.add_argument("--out", help="输出 HTML(缺省 <image 去掉 _clean>_edit.html)")

    args = parser.parse_args()

    if args.command == "ocr":
        blocks = ocr_text_blocks(Path(args.image))
        context_local.save_json("poster_ocr", {"blocks": blocks})
        print(json.dumps({"ok": True, "blocks": blocks, "count": len(blocks)}, ensure_ascii=False))
        return 0

    if args.command == "erase":
        clean_path = asyncio.run(erase_text_from_poster(Path(args.image)))
        print(json.dumps({"ok": True, "clean_image": str(clean_path)}, ensure_ascii=False))
        return 0

    if args.command == "render":
        clean_image_path = Path(args.image)
        layers = _resolve_layers(args)
        if args.out:
            output_path = Path(args.out)
        else:
            stem = clean_image_path.stem.replace("_clean", "")
            output_path = clean_image_path.with_name(f"{stem}_final.png")
        render_text_layers(clean_image_path, layers, output_path)
        print(json.dumps({"ok": True, "final_image": str(output_path), "layers": len(layers)},
                         ensure_ascii=False))
        return 0

    if args.command == "preview":
        clean_image_path = Path(args.image)
        layers = _resolve_layers(args)
        if args.out:
            output_path = Path(args.out)
        else:
            stem = clean_image_path.stem.replace("_clean", "")
            output_path = clean_image_path.with_name(f"{stem}_edit.html")
        render_edit_html(clean_image_path, layers, output_path)
        print(json.dumps({"ok": True, "edit_html": str(output_path), "layers": len(layers)},
                         ensure_ascii=False))
        return 0

    return 1


if __name__ == "__main__":
    # 顶层兜底:别甩 traceback,缺凭据/字体/依赖给人话 + 规范退出码(对齐 AGENTS 协议与其它脚本的 run_skill_main)
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(130)
    except RuntimeError as missing:
        print(json.dumps({"ok": False, "error": "MissingInput", "message": str(missing),
                          "hint": "按 message 补齐(GCV 凭据 / 计费档 image Key / 中文字体)再重试。"},
                         ensure_ascii=False))
        raise SystemExit(2)
    except Exception as failure:
        print(json.dumps({"ok": False, "error": type(failure).__name__, "message": str(failure),
                          "hint": "可能是 Key 权限/配额或网络;先跑 python engine/doctor.py 自检。"},
                         ensure_ascii=False))
        raise SystemExit(1)
