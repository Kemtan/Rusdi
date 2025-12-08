from google import genai
import google.genai.errors as genai_errors
import config

# The client gets the API key from the environment variable `GEMINI_API_KEY`.
def responJomok(message):
    client = genai.Client()

    prompt = (
        f"{message}, jawab sebagai @Rusdi dengan gaya jomok sungut lele: 1 kalimat pendek, santai, boleh pakai woilah cik/loh ya/rek/cik/jir sesekali dan jangan keseringan (jangan pernah sebut beberapa text berikut: (sungut lele) dan (@Rusdi))."
    )

    models = [
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite"
    ]

    for m in models:
        try:
            response = client.models.generate_content(
                model=m,
                contents=prompt,
            )
            return response.text
        except genai_errors.ClientError as e:
            if "RESOURCE_EXHAUSTED" in str(e) or "429" in str(e):
                continue
            else:
                return f"Model error: {str(e)}"
            
    return "All models ran out of quota or encountered an error."