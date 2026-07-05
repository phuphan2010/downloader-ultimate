"""yt-dlp Service wrapper with TikTok & Douyin no-watermark support and exponential backoff retry."""
import asyncio
import re
import shutil
from pathlib import Path
from typing import Dict, Any, Tuple
import yt_dlp

from app.core.config import settings
from app.core.logging import get_logger
from app.models.download import PlatformType, VideoQuality

logger = get_logger(__name__)

TIKTOK_REGEX = re.compile(r"https?://(?:www\.|vm\.|vt\.)?tiktok\.com/.*")
DOUYIN_REGEX = re.compile(r"https?://(?:www\.|v\.)?douyin\.com/.*|https?://v\.douyin\.com/.*")


def validate_and_detect_platform(url: str) -> Tuple[bool, PlatformType]:
    """Validate if URL is supported and detect platform."""
    if TIKTOK_REGEX.match(url):
        return True, PlatformType.TIKTOK
    if DOUYIN_REGEX.match(url):
        return True, PlatformType.DOUYIN
    return False, PlatformType.UNKNOWN


class VideoDownloader:
    """Downloader service managing yt-dlp execution."""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _check_disk_usage(self) -> None:
        """Check disk usage before downloading."""
        disk = shutil.disk_usage(self.output_dir)
        disk_percent = (disk.used / disk.total) * 100
        if disk_percent > settings.MAX_DISK_USAGE_PERCENT:
            raise RuntimeError(f"Disk storage critical ({disk_percent:.1f}% used). Rejecting job.")

    async def download_video(self, url: str, job_id: str, quality: VideoQuality = VideoQuality.BEST) -> Path:
        """Download video from TikTok/Douyin asynchronously with retry."""
        self._check_disk_usage()
        is_valid, platform = validate_and_detect_platform(url)
        if not is_valid:
            raise ValueError("Invalid or unsupported URL. Only TikTok and Douyin URLs are accepted.")

        job_folder = self.output_dir / job_id
        job_folder.mkdir(parents=True, exist_ok=True)
        output_template = str(job_folder / "input_video.%(ext)s")

        ydl_opts: Dict[str, Any] = {
            "outtmpl": output_template,
            "format": "bestvideo+bestaudio/best" if quality == VideoQuality.BEST else f"best[height<={quality.value[:-1]}]/best",
            "quiet": not settings.DEBUG,
            "no_warnings": True,
            "ignoreerrors": False,
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "http_headers": {
                "Referer": "https://www.douyin.com/" if platform == PlatformType.DOUYIN else "https://www.tiktok.com/"
            }
        }

        # Attempt download with backoff retry
        last_exception = None
        for attempt in range(1, settings.DOWNLOAD_RETRY_COUNT + 1):
            try:
                logger.info("download_attempt_start", job_id=job_id, attempt=attempt, platform=platform)
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self._exec_yt_dlp, ydl_opts, url)

                # Locate downloaded file
                downloaded_files = list(job_folder.glob("input_video.*"))
                if downloaded_files:
                    target_file = downloaded_files[0]
                    logger.info("download_success", job_id=job_id, file_path=str(target_file))
                    return target_file
                raise RuntimeError("File downloaded but not found in output folder.")
            except Exception as e:
                last_exception = e
                logger.warning("download_attempt_failed", job_id=job_id, attempt=attempt, error=str(e))
                if attempt < settings.DOWNLOAD_RETRY_COUNT:
                    await asyncio.sleep(2 ** attempt)

        raise RuntimeError(f"Download failed after {settings.DOWNLOAD_RETRY_COUNT} attempts: {str(last_exception)}")

    @staticmethod
    def _exec_yt_dlp(opts: Dict[str, Any], url: str) -> None:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
