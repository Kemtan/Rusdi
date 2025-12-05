from google import genai
import config

# The client gets the API key from the environment variable `GEMINI_API_KEY`.
def responJomok(message):
    client = genai.Client()

    response = client.models.generate_content(
        model="gemini-2.5-flash", contents=f"{message}, jawab sebagai @Rusdi dengan gaya jomok sungut lele: 1 kalimat pendek, santai, boleh pakai woilah cik/loh ya/rek/cik/jir sesekali."
    )
    return response.text