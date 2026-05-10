import google.generativeai as genai
from config.settings import settings

genai.configure(api_key=settings.gemini_api_key)

for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print(m.name)
