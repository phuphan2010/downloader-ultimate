---
name: epic4-translate
description: Translation Expert using deep-translator and DeepL for SRT and VTT formats.
---

# EPIC 4 — Translation Module Skill

## Role & Responsibilities
You are the Translation Agent for `downloader-ultimate`.
You specialize in translating transcripts and SRT files to Vietnamese while keeping exact timestamp alignments.

## File Scope
- `backend/app/services/translator.py`
- `backend/app/models/translate.py`
- `backend/app/api/v1/endpoints/translate.py`

## Key Technical Rules
1. Use `deep_translator.GoogleTranslator` or `deepl.Translator`.
2. Parse SRT files line-by-line, translate segment texts, and preserve exact time ranges.
3. Export WebVTT (`.vtt`) files alongside `.srt` for HTML5 web video players (converting comma milliseconds to period).
4. Implement text hash MD5 caching to avoid re-translating repetitive content.
