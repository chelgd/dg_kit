from __future__ import annotations
from typing import Optional


class NotionFormater:
    @staticmethod
    def _safe_title(prop: dict) -> str:
        items = prop.get("title") or []
        return (items[0].get("plain_text") or "") if items else ""

    @staticmethod
    def _safe_rich_text(prop: dict) -> str:
        items = prop.get("rich_text") or []
        return (items[0].get("plain_text") or "") if items else ""

    @staticmethod
    def _rt_text(text: str, url: Optional[str] = None) -> dict:
        rt = {"type": "text", "text": {"content": text}}
        if url:
            rt["text"]["link"] = {"url": url}
        return rt

    @staticmethod
    def _rt_user_mention(user_id: str) -> dict:
        return {"type": "mention", "mention": {"user": {"id": user_id}}}

    @staticmethod
    def _rt_page_mention(page_id: str) -> dict:
        return {"type": "mention", "mention": {"page": {"id": page_id}}}

    @staticmethod
    def _h2(text: str) -> dict:
        return {
            "object": "block",
            "type": "heading_2",
            "heading_2": {"rich_text": [NotionFormater._rt_text(text)]},
        }

    @staticmethod
    def _para(text: str) -> dict:
        return {
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": [NotionFormater._rt_text(text)]},
        }

    @staticmethod
    def _para_rich_text(rich_text: list[dict]) -> dict:
        return {
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": rich_text},
        }

    @staticmethod
    def _bullet(rich_text: list[dict]) -> dict:
        return {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": rich_text},
        }

    @staticmethod
    def _cell(text: str) -> list[dict]:
        return [{"type": "text", "text": {"content": text or ""}}]
