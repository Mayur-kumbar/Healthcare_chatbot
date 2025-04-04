import google.generativeai as genai
genai.configure(api_key="AIzaSyB6EAGAEsxwqL1Du_55Ony9xDIQadKv1G8")
print([model.name for model in genai.list_models()])
