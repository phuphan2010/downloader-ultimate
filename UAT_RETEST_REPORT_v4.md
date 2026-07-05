# UAT Retest Report — Downloader Ultimate (Lần 4)
**Ngày test:** 2026-07-05  
**Tester:** BA (End User perspective)  
**Server:** pphu@192.168.1.200  
**Branch tested:** `main` @ commit `a79424e`  
**Kết quả tổng:** ❌ **FAIL — Docker image quá lớn (6.37GB), server không đủ disk để chạy container**

---

## TÓM TẮT EXECUTIVE

> BUG-11 fix (Option A: `pip install openai-whisper --no-build-isolation`) đã giải quyết lỗi PEP 517. Docker **build thành công** — milestone đầu tiên qua được. Tuy nhiên, pip resolver kéo full PyTorch + CUDA stack không cần thiết, tạo ra image 6.37GB. Khi Docker cố gắng start container, nó cần extract ~8-10GB uncompressed layers vào `/var/lib/containerd/` nhưng `/var` partition (20GB) không đủ dung lượng. Trong khi đó `/data` có **196GB free** không được tận dụng.

---

## PHẦN 1 — XÁC NHẬN TIẾN TRIỂN

| Hạng mục | Lần 3 | Lần 4 |
|---------|-------|-------|
| Build thành công | ❌ FAIL | ✅ **PASS** — lần đầu tiên build qua! |
| BUG-11 (openai-whisper PEP 517) | ❌ BLOCKED | ✅ **FIXED** — build error đã hết |
| Container start được | ❌ N/A | ❌ FAIL — disk space |
| API accessible | ❌ N/A | ❌ FAIL |

**Tích cực: Lần đầu tiên build thành công sau 4 lần thử.**

---

## PHẦN 2 — BUG MỚI

---

### 🔴 BUG-12 | BLOCKER | Docker image 6.37GB — quá lớn để chạy trên server

| Trường | Giá trị |
|--------|---------|
| **Severity** | Blocker |
| **Nguyên nhân gốc** | `pip install openai-whisper` kéo full PyTorch + CUDA stack |
| **File ảnh hưởng** | `backend/Dockerfile` |
| **Server impact** | `/var` partition 20GB, không đủ chạy container |

**Nguyên nhân chuỗi:**

```
pip install openai-whisper==20231117 --no-build-isolation
    → pip resolver picks latest torch (PyTorch 2.3.1)
    → PyTorch 2.3.1 Linux phụ thuộc CUDA packages:
        - nvidia-cublas-cu12      (410 MB)
        - nvidia-cudnn-cu12       (731 MB)   ← file libcudnn_cnn_train.so.8 gây lỗi
        - nvidia-cufft-cu12       (121 MB)
        - nvidia-cusolver-cu12    (124 MB)
        - nvidia-cusparse-cu12    (196 MB)
        - nvidia-nccl-cu12        (176 MB)
        - triton                  (168 MB)
        → Tổng CUDA packages: ~2.5GB
    → Docker image size: 6.37GB (API) + 6.37GB (Worker)
```

**Disk space khi start container:**
```
/var partition total:          20 GB
containerd images stored:      9.1 GB  (compressed)
Available:                     ~11 GB
Needed để extract layers:      ~8-10 GB  (uncompressed)
← không đủ → "no space left on device"
```

**Server `/data` partition: 200GB, chỉ dùng 4GB — hoàn toàn bỏ phí!**

```
Error log thực tế:
Container downloader-api Error response from daemon: apply layer error for "":
failed to extract layer sha256:07be028e63931fe4bc88a9c98e1e5b16a0de79a1e58b7c319118fb7ec644d071:
write /var/lib/containerd/.../nvidia/cudnn/lib/libcudnn_cnn_train.so.8:
no space left on device
```

---

**Fix cho PM lead — chọn 1 trong 3 options (theo thứ tự khuyến nghị):**

---

**Option A — Khuyến nghị mạnh (code fix, 30 phút):** Thay `openai-whisper` bằng `faster-whisper`

`faster-whisper` dùng CTranslate2 backend, CPU-optimized, không kéo CUDA:
```toml
# pyproject.toml — thay:
openai-whisper = "20231117"
# bằng:
faster-whisper = "^1.0.3"
```

```python
# backend/app/services/transcriber.py — thay:
import whisper
model = whisper.load_model("base")
result = model.transcribe(audio_path)

# bằng:
from faster_whisper import WhisperModel
model = WhisperModel("base", device="cpu", compute_type="int8")
segments, _ = model.transcribe(audio_path)
result = {"text": " ".join([s.text for s in segments])}
```

**Kết quả dự kiến:** Image size giảm từ 6.37GB → ~1.5GB. Container start ngay.

---

**Option B — Quick infrastructure fix (15 phút, không đổi code):** Move Docker data-root sang `/data`

```bash
# /etc/docker/daemon.json
{
  "data-root": "/data/docker"
}
```
Sau đó `sudo systemctl restart docker` và rebuild images.

`/data` có 196GB free — đủ chạy thoải mái.

---

**Option C — Pinning CPU-only PyTorch (code fix, 20 phút):** Cài torch CPU trước openai-whisper

```dockerfile
# Dockerfile — thêm trước bước openai-whisper:
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu --no-cache-dir
RUN pip install openai-whisper==20231117 --no-build-isolation --no-deps
```

`--no-deps` tránh pytorch overwrite bằng CUDA version. Image size: ~2-3GB.

---

## PHẦN 3 — UAT TEST CASES SUMMARY

| # | Test Case | Lần 1 | Lần 2 | Lần 3 | Lần 4 | Ghi chú |
|---|-----------|-------|-------|-------|-------|---------|
| UC-01 | Download TikTok | ❌ | ❌ | ❌ | ❌ BLOCKED | App không start |
| UC-02 | Download Douyin | ❌ | ❌ | ❌ | ❌ BLOCKED | App không start |
| UC-03 | Subtitle tiếng Việt | ❌ | ❌ | ❌ | ❌ BLOCKED | App không start |
| UC-04 | Lồng tiếng | ❌ | ❌ | ❌ | ❌ BLOCKED | App không start |
| UC-05 | Logo overlay | ❌ | ❌ | ❌ | ❌ BLOCKED | App không start |
| UC-06 | n8n Integration | ❌ | ❌ | ❌ | ❌ BLOCKED | App không start |
| UC-07 | Security check | ❌ | ❌ | ❌ | ❌ BLOCKED | App không start |

**0/7 test cases pass (lần 4).**

---

## PHẦN 4 — PRIORITY FIX LIST cho PM Lead (Lần 4)

Chỉ còn **1 bug** để unblock toàn bộ UAT:

| Priority | Bug ID | Fix | Thời gian |
|----------|--------|-----|-----------|
| **P0** | BUG-12 | Chọn Option A, B hoặc C ở trên | 15–30 phút |

---

## PHẦN 5 — NHẬN XÉT

### Điểm tích cực ✅
- **Build lần này thành công** — đây là milestone lớn nhất từ đầu dự án. 11/12 bugs cũ đã fix đúng
- Fix BUG-11 (Option A) đúng hướng, chỉ thiếu bước pin PyTorch CPU-only
- PM lead phản hồi nhanh qua 4 vòng

### Điểm cần cải thiện ⚠️
- **Test `docker compose up` (không chỉ `docker compose build`) trước khi báo cáo BA** — lần này build pass nhưng run fail
- `openai-whisper` là package rất nặng cho CPU server — Option A (`faster-whisper`) nên là default architecture decision ngay từ đầu
- Recommend: sau khi fix BUG-12, PM lead test cả `docker compose up -d` → `curl /health` trên server staging trước khi báo cáo

---

*BA sẵn sàng retest ngay khi PM lead fix BUG-12. Lần này nếu container start được, sẽ test đầy đủ 7 UAT cases trong ngày.*
