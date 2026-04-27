import argparse
import hashlib
import json
import os
import re
import shutil
import tempfile
import time
import zipfile
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import requests

STANDARD_BASE_URL = "https://mineru.net/api/v4"
AGENT_BASE_URL = "https://mineru.net/api/v1/agent"
NOTICE = "文档由AI总结，可能有错误。"
DEFAULT_SYSTEM_PROMPT = "你是一名严谨的技术论文编辑。请严格保留原文信息，不要擅自删减，不要编造。"


@dataclass
class MinerUResult:
    markdown: str
    source_dir: Optional[Path]
    source_name: str


class MinerUError(RuntimeError):
    pass


class TranslatorError(RuntimeError):
    pass


class MinerUClient:
    def __init__(
        self,
        mode: str,
        token: Optional[str] = None,
        model_version: str = "vlm",
        language: str = "ch",
        enable_table: bool = True,
        enable_formula: bool = True,
        is_ocr: bool = False,
        page_ranges: Optional[str] = None,
        timeout: int = 900,
        interval: int = 3,
    ):
        self.mode = mode
        self.token = token
        self.model_version = model_version
        self.language = language
        self.enable_table = enable_table
        self.enable_formula = enable_formula
        self.is_ocr = is_ocr
        self.page_ranges = page_ranges
        self.timeout = timeout
        self.interval = interval

    def parse_file(self, file_path: Path) -> MinerUResult:
        if self.mode == "standard":
            if not self.token:
                raise MinerUError("标准 API 需要提供 MinerU Token，可通过 --token 或 MINERU_API_TOKEN 传入。")
            return self._parse_file_standard(file_path)
        if self.mode == "agent":
            return self._parse_file_agent(file_path)
        raise MinerUError(f"不支持的 MinerU 模式: {self.mode}")

    def _standard_headers(self) -> dict:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}",
            "Accept": "*/*",
        }

    def _agent_payload(self, file_path: Path) -> dict:
        payload = {
            "file_name": file_path.name,
            "language": self.language,
            "enable_table": self.enable_table,
            "is_ocr": self.is_ocr,
            "enable_formula": self.enable_formula,
        }
        if self.page_ranges:
            payload["page_ranges"] = self.page_ranges
            payload["page_range"] = self.page_ranges
        return payload

    def _standard_payload(self, file_path: Path) -> dict:
        file_entry = {
            "name": file_path.name,
            "data_id": file_path.stem,
        }
        if self.page_ranges:
            file_entry["page_ranges"] = self.page_ranges
        return {
            "files": [file_entry],
            "model_version": self.model_version,
            "language": self.language,
            "enable_table": self.enable_table,
            "enable_formula": self.enable_formula,
        }

    def _parse_file_standard(self, file_path: Path) -> MinerUResult:
        create_resp = requests.post(
            f"{STANDARD_BASE_URL}/file-urls/batch",
            headers=self._standard_headers(),
            json=self._standard_payload(file_path),
            timeout=60,
        )
        create_resp.raise_for_status()
        create_data = create_resp.json()
        if create_data.get("code") != 0:
            raise MinerUError(f"申请上传链接失败: {create_data.get('msg', '未知错误')}")

        batch_id = create_data["data"]["batch_id"]
        file_url = create_data["data"]["file_urls"][0]
        with file_path.open("rb") as f:
            upload_resp = requests.put(file_url, data=f, timeout=300)
        if upload_resp.status_code not in (200, 201):
            raise MinerUError(f"上传 PDF 到 MinerU 失败，HTTP {upload_resp.status_code}")

        deadline = time.time() + self.timeout
        while time.time() < deadline:
            poll_resp = requests.get(
                f"{STANDARD_BASE_URL}/extract-results/batch/{batch_id}",
                headers=self._standard_headers(),
                timeout=60,
            )
            poll_resp.raise_for_status()
            poll_data = poll_resp.json()
            if poll_data.get("code") != 0:
                raise MinerUError(f"查询任务结果失败: {poll_data.get('msg', '未知错误')}")

            result = poll_data["data"]["extract_result"][0]
            state = result.get("state")
            if state == "done":
                zip_url = result.get("full_zip_url")
                if not zip_url:
                    raise MinerUError("MinerU 返回完成状态，但缺少 full_zip_url。")
                return self._download_standard_zip(zip_url, file_path.stem)
            if state == "failed":
                raise MinerUError(f"MinerU 解析失败: {result.get('err_msg', '未知错误')}")
            time.sleep(self.interval)

        raise MinerUError("等待 MinerU 标准 API 结果超时。")

    def _download_standard_zip(self, zip_url: str, stem: str) -> MinerUResult:
        temp_root = Path(tempfile.mkdtemp(prefix=f"mineru-{stem}-"))
        zip_path = temp_root / "result.zip"
        with requests.get(zip_url, stream=True, timeout=300) as resp:
            resp.raise_for_status()
            with zip_path.open("wb") as f:
                for chunk in resp.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)

        extract_dir = temp_root / "extract"
        extract_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_dir)

        md_candidates = list(extract_dir.rglob("full.md"))
        if not md_candidates:
            raise MinerUError("MinerU 压缩包中未找到 full.md。")
        markdown = md_candidates[0].read_text(encoding="utf-8", errors="ignore")
        return MinerUResult(markdown=markdown, source_dir=extract_dir, source_name=stem)

    def _parse_file_agent(self, file_path: Path) -> MinerUResult:
        create_resp = requests.post(
            f"{AGENT_BASE_URL}/parse/file",
            json=self._agent_payload(file_path),
            timeout=60,
        )
        create_resp.raise_for_status()
        create_data = create_resp.json()
        if create_data.get("code") != 0:
            raise MinerUError(f"获取 Agent 上传链接失败: {create_data.get('msg', '未知错误')}")

        task_id = create_data["data"]["task_id"]
        file_url = create_data["data"]["file_url"]
        with file_path.open("rb") as f:
            upload_resp = requests.put(file_url, data=f, timeout=300)
        if upload_resp.status_code not in (200, 201):
            raise MinerUError(f"上传 PDF 到 MinerU Agent 失败，HTTP {upload_resp.status_code}")

        deadline = time.time() + self.timeout
        while time.time() < deadline:
            poll_resp = requests.get(f"{AGENT_BASE_URL}/parse/{task_id}", timeout=60)
            poll_resp.raise_for_status()
            poll_data = poll_resp.json()
            if poll_data.get("code") != 0:
                raise MinerUError(f"查询 Agent 任务结果失败: {poll_data.get('msg', '未知错误')}")

            result = poll_data["data"]
            state = result.get("state")
            if state == "done":
                markdown_url = result.get("markdown_url")
                if not markdown_url:
                    raise MinerUError("MinerU Agent 返回完成状态，但缺少 markdown_url。")
                md_resp = requests.get(markdown_url, timeout=300)
                md_resp.raise_for_status()
                return MinerUResult(markdown=md_resp.text, source_dir=None, source_name=file_path.stem)
            if state == "failed":
                raise MinerUError(f"MinerU Agent 解析失败: {result.get('err_msg', '未知错误')}")
            time.sleep(self.interval)

        raise MinerUError("等待 MinerU Agent 结果超时。")


class OpenAICompatibleTranslator:
    def __init__(self, api_key: Optional[str], base_url: Optional[str], model: Optional[str]):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY") or os.getenv("MINERU_TRANSLATE_API_KEY")
        self.base_url = (base_url or os.getenv("OPENAI_BASE_URL") or os.getenv("MINERU_TRANSLATE_BASE_URL") or "https://api.openai.com/v1").rstrip("/")
        self.model = model or os.getenv("OPENAI_MODEL") or os.getenv("MINERU_TRANSLATE_MODEL")

    @property
    def enabled(self) -> bool:
        return bool(self.api_key and self.model)

    def _extract_chat_content(self, data: dict) -> Optional[str]:
        choices = data.get("choices") or []
        if not choices:
            return None
        message = choices[0].get("message") or {}
        content = message.get("content")
        if isinstance(content, str) and content.strip():
            return content.strip()
        if isinstance(content, list):
            texts = []
            for item in content:
                if isinstance(item, dict):
                    text = item.get("text") or item.get("content")
                    if isinstance(text, str) and text.strip():
                        texts.append(text.strip())
            if texts:
                return "\n".join(texts)
        for key in ("reasoning_content", "text"):
            value = message.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return None

    def _extract_responses_content(self, data: dict) -> Optional[str]:
        output = data.get("output") or []
        texts = []
        for item in output:
            if not isinstance(item, dict):
                continue
            content = item.get("content") or []
            for part in content:
                if not isinstance(part, dict):
                    continue
                text = part.get("text") or part.get("content")
                if isinstance(text, str) and text.strip():
                    texts.append(text.strip())
        if texts:
            return "\n".join(texts)
        output_text = data.get("output_text")
        if isinstance(output_text, str) and output_text.strip():
            return output_text.strip()
        return None

    def _sanitize_translation_output(self, user_prompt: str, content: str) -> str:
        cleaned = content.strip()
        if cleaned.startswith(user_prompt.strip()):
            cleaned = cleaned[len(user_prompt.strip()):].lstrip()
        cleaned = re.sub(r"^论文标题：.*(?:\n|$)", "", cleaned, count=1)
        cleaned = re.sub(r"^这是第 \d+/\d+ 段 Markdown。请逐句翻译为中文，并保持 Markdown 结构不变。(?:\n\n|\n|$)", "", cleaned, count=1)
        cleaned = re.sub(r"^请翻译为中文并保留 Markdown 结构：\n\n", "", cleaned, count=1)
        return cleaned.strip()

    def _chat(self, system_prompt: str, user_prompt: str, temperature: float = 0.2) -> str:
        if not self.enabled:
            raise TranslatorError("未配置翻译模型。请提供 OPENAI_API_KEY / OPENAI_MODEL，或对应的 MINERU_TRANSLATE_* 环境变量。")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        chat_payload = {
            "model": self.model,
            "temperature": temperature,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": 1600,
        }

        last_error = None
        for attempt in range(3):
            try:
                resp = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=chat_payload,
                    timeout=90,
                )
                resp.raise_for_status()
                data = resp.json()
                content = self._extract_chat_content(data)
                if content:
                    return self._sanitize_translation_output(user_prompt, content)

                responses_payload = {
                    "model": self.model,
                    "temperature": temperature,
                    "input": [
                        {"role": "system", "content": [{"type": "input_text", "text": system_prompt}]},
                        {"role": "user", "content": [{"type": "input_text", "text": user_prompt}]},
                    ],
                }
                fallback_resp = requests.post(
                    f"{self.base_url}/responses",
                    headers=headers,
                    json=responses_payload,
                    timeout=180,
                )
                fallback_resp.raise_for_status()
                fallback_data = fallback_resp.json()
                fallback_content = self._extract_responses_content(fallback_data)
                if fallback_content:
                    return self._sanitize_translation_output(user_prompt, fallback_content)

                last_error = TranslatorError(
                    "翻译模型返回格式异常: "
                    f"chat={json.dumps(data, ensure_ascii=False)[:500]} | responses={json.dumps(fallback_data, ensure_ascii=False)[:500]}"
                )
            except requests.RequestException as exc:
                last_error = exc
            if attempt < 2:
                time.sleep(2 * (attempt + 1))

        if isinstance(last_error, TranslatorError):
            raise last_error
        raise TranslatorError(f"翻译请求失败: {last_error}")


    def translate_markdown_to_chinese(self, title: str, markdown_text: str) -> str:
        system_prompt = (
            DEFAULT_SYSTEM_PROMPT
            + "\n你需要将英文技术论文 Markdown 全文翻译为中文。必须保留全部信息与 Markdown 结构，保留标题层级、列表、表格、代码块、图片链接、数学公式和引用，不要总结，不要省略。"
        )

        def translate_part(part: str, label: str, max_chars: int) -> list[str]:
            user_prompt = (
                f"论文标题：{title}\n"
                f"这是 {label} 段 Markdown。请逐句翻译为中文，并保持 Markdown 结构不变。\n\n{part}"
            )
            try:
                return [self._chat(system_prompt, user_prompt)]
            except TranslatorError:
                if max_chars <= 300 or len(part) <= 300:
                    raise
                smaller_limit = max(300, max_chars // 2)
                smaller_parts = split_long_block(part, smaller_limit)
                if len(smaller_parts) <= 1:
                    raise
                translated = []
                for child_index, child_part in enumerate(smaller_parts, start=1):
                    child_label = f"{label}.{child_index}/{len(smaller_parts)}"
                    translated.extend(translate_part(child_part, child_label, smaller_limit))
                return translated

        parts = split_markdown(markdown_text, max_chars=1200)
        translated_parts = []
        for index, part in enumerate(parts, start=1):
            label = f"第 {index}/{len(parts)}"
            translated_parts.extend(translate_part(part, label, 1200))
        return "\n\n".join(p.strip() for p in translated_parts if p.strip())

    def generate_intro(self, title: str, markdown_text: str) -> str:
        excerpt = markdown_text[:6000]
        system_prompt = (
            DEFAULT_SYSTEM_PROMPT
            + "\n你需要基于论文内容，为外行写一段简明导读。导读必须用中文，说明研究问题、应用场景中的具体问题，以及作者大致如何解决。控制在 120 到 220 字之间。只输出导读正文，不要输出标题，不要输出项目符号。"
        )
        user_prompt = f"论文标题：{title}\n\n论文内容节选：\n{excerpt}"
        return self._chat(system_prompt, user_prompt, temperature=0.4)


def split_text_by_sentences(text: str, max_chars: int) -> list[str]:
    text = text.strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]

    sentence_endings = "。！？；.!?;"
    pieces = []
    current = []
    current_len = 0
    start = 0
    for index, char in enumerate(text):
        if char not in sentence_endings:
            continue
        sentence = text[start:index + 1].strip()
        start = index + 1
        if not sentence:
            continue
        sentence_len = len(sentence) + 1
        if current and current_len + sentence_len > max_chars:
            pieces.append("".join(current).strip())
            current = [sentence]
            current_len = sentence_len
        else:
            current.append(sentence)
            current_len += sentence_len
    tail = text[start:].strip()
    if tail:
        if len(tail) > max_chars:
            if current:
                pieces.append("".join(current).strip())
                current = []
                current_len = 0
            for i in range(0, len(tail), max_chars):
                pieces.append(tail[i:i + max_chars].strip())
        else:
            if current and current_len + len(tail) + 1 > max_chars:
                pieces.append("".join(current).strip())
                current = [tail]
                current_len = len(tail)
            else:
                current.append(tail)
                current_len += len(tail)
    if current:
        pieces.append("".join(current).strip())
    return [piece for piece in pieces if piece]


def split_long_block(block: str, max_chars: int) -> list[str]:
    block = block.strip("\n")
    if not block:
        return []
    if len(block) <= max_chars:
        return [block]

    paragraphs = [part.strip("\n") for part in re.split(r"\n\s*\n", block) if part.strip()]
    if len(paragraphs) > 1:
        pieces = []
        current = []
        current_len = 0
        for paragraph in paragraphs:
            paragraph_len = len(paragraph) + 2
            if current and current_len + paragraph_len > max_chars:
                pieces.append("\n\n".join(current))
                current = [paragraph]
                current_len = paragraph_len
            else:
                current.append(paragraph)
                current_len += paragraph_len
        if current:
            pieces.append("\n\n".join(current))
        result = []
        for piece in pieces:
            result.extend(split_long_block(piece, max_chars))
        return result

    lines = [line for line in block.splitlines() if line.strip()]
    if len(lines) > 1:
        pieces = []
        current = []
        current_len = 0
        for line in lines:
            line_len = len(line) + 1
            if current and current_len + line_len > max_chars:
                pieces.append("\n".join(current))
                current = [line]
                current_len = line_len
            else:
                current.append(line)
                current_len += line_len
        if current:
            pieces.append("\n".join(current))
        result = []
        for piece in pieces:
            result.extend(split_long_block(piece, max_chars))
        return result

    if re.search(r"[\u4e00-\u9fffA-Za-z]", block):
        return split_text_by_sentences(block, max_chars)

    text = block
    return [text[i:i + max_chars] for i in range(0, len(text), max_chars)]


def split_markdown(text: str, max_chars: int = 1200) -> list[str]:
    blocks = re.split(r"\n(?=#|```)", text)
    chunks = []
    current = []
    current_len = 0
    for raw_block in blocks:
        raw_block = raw_block.strip("\n")
        if not raw_block:
            continue
        for block in split_long_block(raw_block, max_chars):
            block_len = len(block) + 2
            if current and current_len + block_len > max_chars:
                chunks.append("\n\n".join(current))
                current = [block]
                current_len = block_len
            else:
                current.append(block)
                current_len += block_len
    if current:
        chunks.append("\n\n".join(current))
    return chunks or [text]


def detect_primary_language(markdown_text: str) -> str:
    cjk = len(re.findall(r"[\u4e00-\u9fff]", markdown_text))
    latin = len(re.findall(r"[A-Za-z]", markdown_text))
    if latin > cjk * 2 and latin > 500:
        return "en"
    return "zh"


def normalize_title_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip("# ").strip()
    return text.strip("：:·•-— ")


def is_bad_title_candidate(text: str) -> bool:
    normalized = normalize_title_text(text)
    if len(normalized) < 6:
        return True
    blacklist_patterns = [
        r"学位论文$",
        r"硕士学位论文$",
        r"博士学位论文$",
        r"学术学位论文$",
        r"^摘要$",
        r"^abstract$",
        r"^目录$",
        r"^contents$",
        r"^参考文献$",
        r"^结论$",
        r"^dissertation for",
        r"^candidate:",
        r"^supervisor:",
        r"^academic degree",
        r"^speciality:",
        r"^affiliation:",
        r"^date of defence:",
        r"^degree-conferring-institution:",
        r"^哈尔滨工业大学$",
        r"^郑宇辰$",
    ]
    lowered = normalized.lower()
    return any(re.search(pattern, lowered) for pattern in blacklist_patterns)


def score_title_candidate(text: str) -> tuple[int, int, int]:
    normalized = normalize_title_text(text)
    cjk_count = len(re.findall(r"[\u4e00-\u9fff]", normalized))
    latin_count = len(re.findall(r"[A-Za-z]", normalized))
    has_fpga = 1 if "FPGA" in normalized.upper() else 0
    return (has_fpga, cjk_count, len(normalized) + latin_count)


def guess_title(file_path: Path, markdown_text: str) -> str:
    candidates = []
    for index, line in enumerate(markdown_text.splitlines()[:120]):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            candidate = normalize_title_text(stripped.lstrip("#"))
        else:
            candidate = normalize_title_text(stripped)
        if is_bad_title_candidate(candidate):
            continue
        if len(candidate) > 80:
            continue
        candidates.append((index, candidate))

    if candidates:
        preferred = sorted(candidates, key=lambda item: (score_title_candidate(item[1]), -item[0]), reverse=True)
        return preferred[0][1]
    return file_path.stem.replace("_", " ").strip()


def trim_leading_pages(markdown_text: str) -> str:
    lines = markdown_text.splitlines()
    markers = [
        r"^#\s*摘要$",
        r"^摘要$",
        r"^#\s*Abstract$",
        r"^Abstract$",
        r"^#\s*第.?1章",
        r"^第.?1章",
    ]
    for index, line in enumerate(lines):
        stripped = line.strip()
        if any(re.match(pattern, stripped, re.IGNORECASE) for pattern in markers):
            return "\n".join(lines[index:]).strip() + "\n"
    return markdown_text


def extract_intro_source(markdown_text: str) -> str:
    lines = markdown_text.splitlines()
    capture = []
    capturing = False
    for line in lines:
        stripped = line.strip()
        if re.match(r"^#\s*(摘要|Abstract)$", stripped, re.IGNORECASE) or re.match(r"^(摘要|Abstract)$", stripped, re.IGNORECASE):
            capturing = True
            continue
        if capturing and stripped.startswith("#") and not re.match(r"^#\s*(摘要|Abstract)$", stripped, re.IGNORECASE):
            break
        if capturing:
            capture.append(line)
    source = "\n".join(capture).strip()
    return source or markdown_text[:6000]


def fallback_intro(title: str, markdown_text: str) -> str:
    source = extract_intro_source(markdown_text)
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", source) if p.strip()]
    summary = " ".join(paragraphs[:2])
    summary = re.sub(r"\s+", " ", summary)
    if len(summary) > 220:
        summary = summary[:220].rstrip("，。；;,:： ") + "。"
    if summary:
        return summary
    return f"这篇论文研究《{title}》所涉及的问题、应用场景与实现方法，正文对其设计思路、实现过程和实验验证进行了完整展开。"


def normalize_markdown(markdown_text: str) -> str:
    lines = markdown_text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    cleaned = []
    prev_blank = False
    for line in lines:
        if line.strip():
            cleaned.append(line.rstrip())
            prev_blank = False
        else:
            if not prev_blank:
                cleaned.append("")
            prev_blank = True
    return "\n".join(cleaned).strip() + "\n"


def download_remote_assets(markdown_text: str, asset_dir: Path, asset_prefix: str) -> str:
    asset_dir.mkdir(parents=True, exist_ok=True)

    def local_name_from_url(url: str) -> str:
        parsed = urlparse(url)
        suffix = Path(parsed.path).suffix or ".bin"
        digest = hashlib.sha256(url.encode("utf-8")).hexdigest()
        return f"remote/{digest}{suffix}"

    def replace(match: re.Match) -> str:
        prefix, url, suffix = match.group(1), match.group(2), match.group(3)
        if not re.match(r"^https?://", url):
            return match.group(0)
        rel_path = Path(local_name_from_url(url))
        target = asset_dir / rel_path
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            with requests.get(url, stream=True, timeout=120) as resp:
                resp.raise_for_status()
                with target.open("wb") as f:
                    for chunk in resp.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            f.write(chunk)
        local_url = Path(asset_prefix, rel_path.as_posix()).as_posix()
        return f"{prefix}{local_url}{suffix}"

    pattern = r"(!?\[[^\]]*\]\()([^\)]+)(\))"
    return re.sub(pattern, replace, markdown_text)


def rewrite_relative_assets(markdown_text: str, asset_prefix: str, source_dir: Optional[Path]) -> str:
    if not source_dir:
        return markdown_text

    def replace(match: re.Match) -> str:
        prefix, url, suffix = match.group(1), match.group(2), match.group(3)
        if re.match(r"^(?:[a-zA-Z][a-zA-Z0-9+.-]*:|/|#)", url):
            return match.group(0)
        candidate = source_dir / url
        if candidate.exists():
            normalized = Path(asset_prefix, url).as_posix()
            return f"{prefix}{normalized}{suffix}"
        return match.group(0)

    pattern = r"(!?\[[^\]]*\]\()([^\)]+)(\))"
    return re.sub(pattern, replace, markdown_text)


def copy_extracted_assets(source_dir: Optional[Path], asset_dir: Path) -> None:
    if not source_dir:
        return
    asset_dir.mkdir(parents=True, exist_ok=True)
    for item in source_dir.rglob("*"):
        if item.is_dir():
            continue
        rel = item.relative_to(source_dir)
        if rel.name == "full.md":
            continue
        target = asset_dir / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, target)


def build_front_matter(title: str) -> str:
    today = date.today().isoformat()
    return "\n".join(
        [
            "---",
            f"title: 论文阅读：{title}",
            f"date: {today}",
            "tags:",
            "- 论文阅读",
            "---",
            "",
        ]
    )


def build_output_markdown(title: str, body: str) -> str:
    sections = [
        build_front_matter(title),
        normalize_markdown(body),
    ]
    return "\n".join(sections).strip() + "\n"


def process_single_pdf(file_path: Path, output_dir: Path, asset_root: Path, client: MinerUClient, output_suffix: str = ".md") -> Path:
    result = client.parse_file(file_path)
    raw_markdown = normalize_markdown(result.markdown)
    title = guess_title(file_path, raw_markdown)
    asset_dir = asset_root / file_path.stem
    asset_prefix = f"mineru_assets/{file_path.stem}"
    body = rewrite_relative_assets(raw_markdown, asset_prefix, result.source_dir)
    body = download_remote_assets(body, asset_dir, asset_prefix)
    body = trim_leading_pages(normalize_markdown(body))

    final_markdown = build_output_markdown(title, body)
    output_dir.mkdir(parents=True, exist_ok=True)
    copy_extracted_assets(result.source_dir, asset_dir)

    output_path = output_dir / f"{file_path.stem}{output_suffix}"
    output_path.write_text(final_markdown, encoding="utf-8")
    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="使用 MinerU 将 PDF 转为 Markdown，并将图片资源保存到本地。")
    parser.add_argument("pdf", nargs="+", help="待处理的 PDF 文件路径")
    parser.add_argument("--output-dir", default="posts/论文阅读", help="输出 Markdown 目录")
    parser.add_argument("--asset-root", default="posts/论文阅读/mineru_assets", help="提取资源输出目录")
    parser.add_argument("--output-suffix", default=".md", help="输出 Markdown 文件后缀，例如 .md 或 .en.md")
    parser.add_argument("--mode", choices=["standard", "agent"], default="standard", help="MinerU API 模式")
    parser.add_argument("--token", default=os.getenv("MINERU_API_TOKEN"), help="MinerU 标准 API Token")
    parser.add_argument("--model-version", default="vlm", help="标准 API 模型版本，默认 vlm")
    parser.add_argument("--language", default="ch", help="MinerU 解析语言，默认 ch")
    parser.add_argument("--page-ranges", default=None, help="可选页码范围，例如 1-10")
    parser.add_argument("--enable-table", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--enable-formula", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--is-ocr", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--interval", type=int, default=3)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    client = MinerUClient(
        mode=args.mode,
        token=args.token,
        model_version=args.model_version,
        language=args.language,
        enable_table=args.enable_table,
        enable_formula=args.enable_formula,
        is_ocr=args.is_ocr,
        page_ranges=args.page_ranges,
        timeout=args.timeout,
        interval=args.interval,
    )

    output_dir = Path(args.output_dir).resolve()
    asset_root = Path(args.asset_root).resolve()
    for pdf in args.pdf:
        pdf_path = Path(pdf).resolve()
        if not pdf_path.exists():
            raise FileNotFoundError(f"未找到 PDF 文件: {pdf_path}")
        if pdf_path.suffix.lower() != ".pdf":
            raise ValueError(f"仅支持 PDF 文件: {pdf_path}")
        output_path = process_single_pdf(pdf_path, output_dir, asset_root, client, output_suffix=args.output_suffix)
        print(f"已生成: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
