import os
import json
import time
import requests
from datawizard_core.exceptions import LLMError

VALID_PROVIDERS = ["openai", "anthropic"]

DEFAULT_MODELS = {
    "openai": "gpt-4o-mini",
    "anthropic": "claude-sonnet-4-20250514",
}

API_URLS = {
    "openai": "https://api.openai.com/v1/chat/completions",
    "anthropic": "https://api.anthropic.com/v1/messages",
}

ENV_KEYS = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
}

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"

DEFAULT_TEMPERATURE = 0.3
DEFAULT_MAX_TOKENS = 1000
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 2  # seconds

SYSTEM_MESSAGE = (
    "Sen DataWizard platformunun yapay zeka asistanısın. "
    "Kullanıcılar teknik bilgisi olmayan akademisyenler, öğrenciler ve "
    "küçük işletme sahipleridir. Görevin, veri analizi ve makine öğrenmesi "
    "sonuçlarını sade, anlaşılır Türkçe ile açıklamaktır. "
    "Teknik jargondan kaçın. Somut örnekler ve benzetmeler kullan. "
    "Yanıtlarını madde işaretleri ile yapılandır."
)

def build_statistics_prompt(summary_data: dict, column_stats: dict) -> str:

    # Format numeric column summaries
    numeric_summary_lines = []
    for col, stats in column_stats.get("numeric", {}).items():
        numeric_summary_lines.append(
            f"  - {col}: ortalama={stats['mean']}, medyan={stats['median']}, "
            f"std={stats['std']}, min={stats['min']}, max={stats['max']}, "
            f"çarpıklık={stats['skewness']}"
        )

    # Format categorical column summaries
    categorical_summary_lines = []
    for col, stats in column_stats.get("categorical", {}).items():
        top_vals = ", ".join(
            f"{v['value']}({v['count']})" for v in stats.get("top_values", [])[:3]
        )
        categorical_summary_lines.append(
            f"  - {col}: en sık={stats['mode']}, benzersiz={stats['unique_count']}, "
            f"dağılım: {top_vals}"
        )

    prompt = f"""Aşağıda bir veri setinin özet istatistikleri verilmiştir. 
Bu istatistikleri teknik bilgisi olmayan bir kullanıcıya sade Türkçe ile açıkla.

## Veri Seti Özeti
- Toplam satır: {summary_data.get('row_count', 'N/A')}
- Toplam sütun: {summary_data.get('column_count', 'N/A')}
- Sayısal sütun: {summary_data.get('numeric_column_count', 'N/A')}
- Kategorik sütun: {summary_data.get('categorical_column_count', 'N/A')}
- Eksik veri oranı: %{summary_data.get('missing_pct', 'N/A')}
- Tekrar eden satır: {summary_data.get('duplicate_row_count', 'N/A')}

## Sayısal Sütun İstatistikleri
{chr(10).join(numeric_summary_lines) if numeric_summary_lines else '  Sayısal sütun yok.'}

## Kategorik Sütun İstatistikleri
{chr(10).join(categorical_summary_lines) if categorical_summary_lines else '  Kategorik sütun yok.'}

## İstenen Çıktı
3-5 madde halinde şu konularda içgörüler sun:
1. Veri setinin genel durumu ve kalitesi
2. Dikkat çekici istatistiksel özellikler (çarpıklık, dağılım)
3. Eksik veri durumu ve öneriler
4. Olası veri kalitesi sorunları
5. Veri seti hakkında genel değerlendirme"""

    return prompt

def build_correlation_prompt(corr_data: dict) -> str:

    columns = corr_data.get("columns", [])
    matrix = corr_data.get("matrix", [])
    method = corr_data.get("method", "pearson")

    # Build readable correlation pairs (upper triangle only)
    corr_pairs = []
    for i in range(len(columns)):
        for j in range(i + 1, len(columns)):
            val = matrix[i][j]
            corr_pairs.append({
                "var1": columns[i],
                "var2": columns[j],
                "correlation": val,
            })

    # Sort by absolute correlation descending
    corr_pairs.sort(key=lambda x: abs(x["correlation"]), reverse=True)

    pairs_text = "\n".join(
        f"  - {p['var1']} & {p['var2']}: {p['correlation']}"
        for p in corr_pairs
    )

    prompt = f"""Aşağıda bir veri setindeki sayısal değişkenler arasındaki {method} korelasyon değerleri verilmiştir.
Bu korelasyonları teknik bilgisi olmayan bir kullanıcıya sade Türkçe ile açıkla.

## Değişkenler
{', '.join(columns)}

## Korelasyon Çiftleri (mutlak değere göre sıralı)
{pairs_text}

## İstenen Çıktı
3-5 madde halinde şu konularda içgörüler sun:
1. En güçlü pozitif ve negatif korelasyonları açıkla (pratik anlamlarıyla)
2. Birbirine çok bağlı (yüksek korelasyon) değişkenleri belirt
3. Bağımsız görünen (düşük korelasyon) değişkenleri belirt
4. Makine öğrenmesi modeli için en iyi özellik (feature) adaylarını öner
5. Korelasyonun nedensellik olmadığını hatırlat

Korelasyon katsayılarını açıklarken şu ölçeği kullan:
- 0.0-0.3: Zayıf ilişki
- 0.3-0.7: Orta düzey ilişki
- 0.7-1.0: Güçlü ilişki"""

    return prompt

def build_model_results_prompt(
    metrics: dict,
    feature_importance: list,
    model_type: str,
    algorithm: str,
) -> str:

    # Format metrics section
    if model_type == "classification":
        metrics_text = f"""- Doğruluk (Accuracy): %{round(metrics.get('accuracy', 0) * 100, 1)}
- Kesinlik (Precision): %{round(metrics.get('precision', 0) * 100, 1)}
- Duyarlılık (Recall): %{round(metrics.get('recall', 0) * 100, 1)}
- F1-Score: %{round(metrics.get('f1_score', 0) * 100, 1)}
- Confusion Matrix: {metrics.get('confusion_matrix', 'N/A')}
- Sınıf etiketleri: {metrics.get('class_labels', 'N/A')}"""

    else:  # regression
        metrics_text = f"""- MSE (Ortalama Kare Hata): {metrics.get('mse', 'N/A')}
- RMSE (Kök Ortalama Kare Hata): {metrics.get('rmse', 'N/A')}
- R² Skoru: {metrics.get('r2_score', 'N/A')}"""

    # Format feature importance
    if feature_importance:
        importance_text = "\n".join(
            f"  - {fi['feature']}: %{fi['importance_pct']}"
            for fi in feature_importance[:10]
        )
    else:
        importance_text = "  Özellik önemi bu model tipi için mevcut değil."

    # Algorithm display name
    algo_names = {
        "logistic_regression": "Lojistik Regresyon",
        "random_forest_classifier": "Random Forest (Sınıflandırma)",
        "decision_tree": "Karar Ağacı",
        "knn": "K-En Yakın Komşu (KNN)",
        "linear_regression": "Doğrusal Regresyon",
        "random_forest_regressor": "Random Forest (Regresyon)",
    }
    algo_display = algo_names.get(algorithm, algorithm)

    model_type_tr = "Sınıflandırma" if model_type == "classification" else "Regresyon"

    prompt = f"""Aşağıda bir makine öğrenmesi modelinin eğitim sonuçları verilmiştir.
Bu sonuçları teknik bilgisi olmayan bir kullanıcıya sade Türkçe ile açıkla.

## Model Bilgileri
- Algoritma: {algo_display}
- Problem Tipi: {model_type_tr}

## Performans Metrikleri
{metrics_text}

## Özellik Önem Sıralaması
{importance_text}

## İstenen Çıktı
Yanıtını şu başlıklar altında yapılandır:

### Genel Performans Değerlendirmesi
Modelin genel başarısını 2-3 cümle ile değerlendir.

### Güçlü Yönler
Modelin iyi performans gösterdiği noktaları listele.

### Dikkat Edilmesi Gerekenler
Potansiyel sorunları veya iyileştirme alanlarını belirt.
{"Confusion matrix'teki hataları yorumla." if model_type == "classification" else "R² skorunu ve hata metriklerini yorumla."}

### Sonraki Adımlar
Kullanıcının modeli geliştirmek için yapabileceği 3-4 öneri sun.
Örneğin: farklı algoritma denemek, hiperparametre ayarı, çapraz doğrulama, veri artırma."""

    return prompt

def call_llm_api(
    prompt: str,
    provider: str = "openai",
    model: str = None,
    temperature: float = DEFAULT_TEMPERATURE,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> dict:
    
    # Validate provider
    if provider not in VALID_PROVIDERS:
        raise LLMError(
            message=f"Invalid provider '{provider}'. Valid: {VALID_PROVIDERS}",
            details={"provider": provider, "valid": VALID_PROVIDERS},
        )

    # Resolve model
    if model is None:
        model = DEFAULT_MODELS[provider]

    # Get API key
    env_key = ENV_KEYS[provider]
    api_key = os.environ.get(env_key)
    if not api_key:
        raise LLMError(
            message=f"API key not found. Set the '{env_key}' environment variable.",
            details={"env_key": env_key, "provider": provider},
        )

    # Build request
    if provider == "openai":
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_MESSAGE},
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

    elif provider == "anthropic":
        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }
        payload = {
            "model": model,
            "system": SYSTEM_MESSAGE,
            "messages": [
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

    api_url = API_URLS[provider]

    # Retry loop with exponential backoff
    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(
                api_url,
                headers=headers,
                json=payload,
                timeout=REQUEST_TIMEOUT,
            )

            if response.status_code == 200:
                return _parse_api_response(response.json(), provider, model)

            # Rate limit: wait and retry
            if response.status_code == 429:
                wait_time = RETRY_BACKOFF_BASE ** (attempt + 1)
                time.sleep(wait_time)
                last_error = f"Rate limited (429). Attempt {attempt + 1}/{MAX_RETRIES}."
                continue

            # Other HTTP errors
            error_body = response.text[:500]
            last_error = (
                f"API returned status {response.status_code}: {error_body}"
            )

            # Don't retry on client errors (4xx) except 429
            if 400 <= response.status_code < 500:
                break

            # Server errors (5xx): retry
            wait_time = RETRY_BACKOFF_BASE ** (attempt + 1)
            time.sleep(wait_time)

        except requests.exceptions.Timeout:
            last_error = f"Request timed out after {REQUEST_TIMEOUT}s. Attempt {attempt + 1}/{MAX_RETRIES}."
            wait_time = RETRY_BACKOFF_BASE ** (attempt + 1)
            time.sleep(wait_time)

        except requests.exceptions.ConnectionError as e:
            last_error = f"Connection error: {str(e)}. Attempt {attempt + 1}/{MAX_RETRIES}."
            wait_time = RETRY_BACKOFF_BASE ** (attempt + 1)
            time.sleep(wait_time)

        except Exception as e:
            last_error = f"Unexpected error: {str(e)}"
            break

    raise LLMError(
        message=f"LLM API call failed after {MAX_RETRIES} attempts. Last error: {last_error}",
        details={
            "provider": provider,
            "model": model,
            "last_error": last_error,
            "attempts": MAX_RETRIES,
        },
    )


def _parse_api_response(response_json: dict, provider: str, model: str) -> dict:
    try:
        if provider == "openai":
            text = response_json["choices"][0]["message"]["content"]
            usage = {
                "prompt_tokens": response_json.get("usage", {}).get("prompt_tokens", 0),
                "completion_tokens": response_json.get("usage", {}).get("completion_tokens", 0),
            }

        elif provider == "anthropic":
            # Anthropic returns content as a list of blocks
            content_blocks = response_json.get("content", [])
            text = "".join(
                block.get("text", "")
                for block in content_blocks
                if block.get("type") == "text"
            )
            usage = {
                "prompt_tokens": response_json.get("usage", {}).get("input_tokens", 0),
                "completion_tokens": response_json.get("usage", {}).get("output_tokens", 0),
            }

        else:
            text = str(response_json)
            usage = {"prompt_tokens": 0, "completion_tokens": 0}

    except (KeyError, IndexError, TypeError) as e:
        raise LLMError(
            message=f"Failed to parse API response: {str(e)}",
            details={"provider": provider, "response_keys": list(response_json.keys())},
        )

    return {
        "text": text.strip(),
        "provider": provider,
        "model": model,
        "usage": usage,
    }

def parse_llm_response(response_text: str) -> dict:
    
    if not response_text or not response_text.strip():
        return {
            "summary": "",
            "sections": [],
            "bullet_points": [],
            "raw_text": "",
        }

    raw_text = response_text.strip()
    lines = raw_text.split("\n")

    sections = []
    bullet_points = []
    current_section_title = None
    current_section_lines = []
    summary_lines = []
    found_first_section = False

    for line in lines:
        stripped = line.strip()

        # Detect section headers: ### Header or **Header**
        is_header = False
        header_title = ""

        if stripped.startswith("###"):
            is_header = True
            header_title = stripped.lstrip("#").strip()
        elif stripped.startswith("**") and stripped.endswith("**") and len(stripped) > 4:
            is_header = True
            header_title = stripped.strip("*").strip()

        if is_header:
            # Save previous section
            if current_section_title is not None:
                sections.append({
                    "title": current_section_title,
                    "content": "\n".join(current_section_lines).strip(),
                })
            current_section_title = header_title
            current_section_lines = []
            found_first_section = True
            continue

        # Detect bullet points
        if stripped.startswith(("- ", "• ", "* ", "· ")):
            bullet_text = stripped.lstrip("-•*· ").strip()
            if bullet_text:
                bullet_points.append(bullet_text)

        # Numbered items (1. 2. etc.)
        if len(stripped) > 2 and stripped[0].isdigit() and stripped[1] in (".", ")"):
            bullet_text = stripped[2:].strip().lstrip(". )")
            if bullet_text:
                bullet_points.append(bullet_text)

        # Accumulate lines
        if found_first_section:
            current_section_lines.append(stripped)
        else:
            if stripped:  # Skip empty lines before first section
                summary_lines.append(stripped)

    # Save last section
    if current_section_title is not None:
        sections.append({
            "title": current_section_title,
            "content": "\n".join(current_section_lines).strip(),
        })

    # Build summary
    summary = "\n".join(summary_lines).strip()

    # If no sections were found, use full text as summary
    if not sections and not summary:
        summary = raw_text

    return {
        "summary": summary,
        "sections": sections,
        "bullet_points": bullet_points,
        "raw_text": raw_text,
    }

def call_groq(prompt: str) -> str:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise LLMError(
            message="GROQ_API_KEY not set.",
            details={"env_key": "GROQ_API_KEY"},
        )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_MESSAGE},
            {"role": "user", "content": prompt},
        ],
        "temperature": DEFAULT_TEMPERATURE,
        "max_tokens": DEFAULT_MAX_TOKENS,
    }

    response = requests.post(
        GROQ_API_URL,
        headers=headers,
        json=payload,
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]