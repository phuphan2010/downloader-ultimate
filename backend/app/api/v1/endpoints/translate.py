"""Translation API Endpoint."""
from fastapi import APIRouter, HTTPException, status

from app.core.logging import get_logger
from app.models.download import JobStatus
from app.models.translate import TranslateRequest, TranslateResponse
from app.services.job_store import get_job, update_job
from app.services.translator import translator_service, parse_srt
from app.storage.file_manager import file_manager

logger = get_logger(__name__)
router = APIRouter()


@router.post("", response_model=TranslateResponse)
async def translate_transcript(request: TranslateRequest):
    """Translate transcript SRT file to target language (default: Vietnamese) and generate VTT."""
    job = get_job(request.job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{request.job_id}' not found."
        )

    job_dir = file_manager.get_job_dir(request.job_id)
    srt_file = job_dir / "transcript.srt"
    if not srt_file.exists():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No transcript.srt found for this job. Please run transcription step first."
        )

    try:
        update_job(request.job_id, status=JobStatus.TRANSLATING, progress=50)

        original_srt = srt_file.read_text(encoding="utf-8")
        trans_srt, trans_vtt = translator_service.translate_srt(
            original_srt, target_lang=request.target_lang, provider=request.provider
        )

        out_srt = job_dir / f"translated_{request.target_lang}.srt"
        out_vtt = job_dir / f"translated_{request.target_lang}.vtt"

        out_srt.write_text(trans_srt, encoding="utf-8")
        out_vtt.write_text(trans_vtt, encoding="utf-8")

        # Extract full translated text
        parsed = parse_srt(trans_srt)
        full_text = " ".join([p["text"] for p in parsed])

        update_job(request.job_id, status=JobStatus.DONE, progress=100)

        return TranslateResponse(
            job_id=request.job_id,
            srt_url=f"/static/{request.job_id}/{out_srt.name}",
            vtt_url=f"/static/{request.job_id}/{out_vtt.name}",
            translated_text=full_text,
            target_lang=request.target_lang,
            provider=request.provider
        )
    except Exception as e:
        logger.error("translation_failed", job_id=request.job_id, error=str(e))
        update_job(request.job_id, status=JobStatus.FAILED, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Translation failed: {str(e)}"
        )
