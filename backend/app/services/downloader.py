"""yt-dlp Service wrapper with temporary writable cookie copy and Douyin GET JSON API fallback (BUG-22, BUG-17C Fix)."""
import asyncio
import re
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import yt_dlp
import httpx

from app.core.config import settings
from app.core.logging import get_logger
from app.models.download import PlatformType, VideoQuality

logger = get_logger(__name__)

# ImpersonateTarget for yt-dlp Python API (BUG-21 Fix)
try:
    from yt_dlp.networking.impersonate import ImpersonateTarget
    IMPERSONATE_CHROME = ImpersonateTarget("chrome")
except Exception:
    IMPERSONATE_CHROME = "chrome"

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
        """Download video from TikTok/Douyin asynchronously with retry & error capture."""
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
            "quiet": False,
            "no_warnings": False,
            "ignoreerrors": False,
            "impersonate": IMPERSONATE_CHROME,
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "http_headers": {
                "Referer": "https://www.douyin.com/" if platform == PlatformType.DOUYIN else "https://www.tiktok.com/"
            }
        }

        # Proxy configuration (BUG-18 Fix)
        if settings.PROXY_URL:
            ydl_opts["proxy"] = settings.PROXY_URL
            logger.info("using_proxy_url", proxy=settings.PROXY_URL)

        # Writable cookie file copy (BUG-22 Fix: avoids Read-only file system error)
        temp_cookie_path: Optional[Path] = None
        cookie_candidates = [
            Path(settings.COOKIES_FILE),
            Path("/app/cookies/douyin_cookies.txt"),
            Path("/app/cookies/cookies.txt"),
            Path("/data/cookies.txt"),
            Path("/data/douyin_cookies.txt"),
        ]
        cookie_file = next((p for p in cookie_candidates if p.exists()), None)
        if cookie_file:
            try:
                tmp_fd, tmp_name = tempfile.mkstemp(suffix="_cookies.txt")
                temp_cookie_path = Path(tmp_name)
                with open(tmp_fd, "wb") as f_out, open(cookie_file, "rb") as f_in:
                    f_out.write(f_in.read())
                ydl_opts["cookiefile"] = str(temp_cookie_path)
                logger.info("using_writable_temp_cookie_file", source=str(cookie_file), temp=str(temp_cookie_path))
            except Exception as e:
                logger.warning("copy_cookie_file_failed_using_original", error=str(e))
                ydl_opts["cookiefile"] = str(cookie_file)

        # Attempt download with backoff retry
        last_exception_msg = ""
        try:
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
                    err_str = str(e).strip()
                    if not err_str:
                        err_str = getattr(e, 'msg', '') or type(e).__name__
                    last_exception_msg = err_str

                    logger.warning("download_attempt_failed", job_id=job_id, attempt=attempt, error=last_exception_msg)
                    if attempt < settings.DOWNLOAD_RETRY_COUNT:
                        await asyncio.sleep(2 ** attempt)
        finally:
            if temp_cookie_path and temp_cookie_path.exists():
                temp_cookie_path.unlink(missing_ok=True)

        # Douyin API Service fallback if yt-dlp fails (BUG-17C Fix)
        if platform == PlatformType.DOUYIN and settings.DOUYIN_API_SERVICE_URL:
            try:
                logger.info("attempting_douyin_api_service_fallback", job_id=job_id)
                fallback_file = await self._download_via_douyin_api(url, job_folder)
                if fallback_file and fallback_file.exists():
                    logger.info("douyin_fallback_success", job_id=job_id, file_path=str(fallback_file))
                    return fallback_file
            except Exception as fe:
                logger.warning("douyin_fallback_failed", error=str(fe))

        raise RuntimeError(f"Download failed after {settings.DOWNLOAD_RETRY_COUNT} attempts: {last_exception_msg}")

    @staticmethod
    def _exec_yt_dlp(opts: Dict[str, Any], url: str) -> None:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])

    async def _download_via_douyin_api(self, url: str, job_folder: Path) -> Path:
        """Fallback method sending GET request with ?url= query parameter to douyin_tiktok_api service (BUG-17C Fix)."""
        headers = {}
        if settings.DOUYIN_API_KEY:
            headers["X-API-Key"] = settings.DOUYIN_API_KEY

        base_url = settings.DOUYIN_API_SERVICE_URL.rstrip('/')

        async with httpx.AsyncClient(timeout=60.0, headers=headers, follow_redirects=True) as client:
            logger.info("douyin_api_get_request", base_url=base_url, target_url=url)
            resp = await client.get(base_url, params={"url": url})
            if resp.status_code != 200:
                raise RuntimeError(f"Douyin API service returned HTTP {resp.status_code}: {resp.text[:200]}")

            data = resp.json()
            logger.info("douyin_api_json_response_received", keys=list(data.keys()) if isinstance(data, dict) else "not_dict")

            # Extract video URL from JSON response dynamically
            video_url = None
            if isinstance(data, dict):
                # Try direct keys
                for k in ["video_url", "download_url", "url", "nwm_url", "play_addr"]:
                    if data.get(k) and isinstance(data[k], str) and data[k].startswith("http"):
                        video_url = data[k]
                        break

                # Try nested data keys if not found
                if not video_url and isinstance(data.get("data"), dict):
                    nested = data["data"]
                    for k in ["video_url", "download_url", "url", "nwm_url", "play_addr"]:
                        if nested.get(k) and isinstance(nested[k], str) and nested[k].startswith("http"):
                            video_url = nested[k]
                            break

            if not video_url:
                raise RuntimeError(f"Could not extract video_url from Douyin API JSON response: {data}")

            logger.info("downloading_binary_from_parsed_url", video_url=video_url)
            video_resp = await client.get(video_url)
            if video_resp.status_code == 200 and len(video_resp.content) > 1024:
                target_file = job_folder / "input_video.mp4"
                target_file.write_bytes(video_resp.content)
                return target_file

            raise RuntimeError(f"Failed to fetch binary video from parsed URL: status {video_resp.status_code}")
