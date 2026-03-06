import os
import google.generativeai as genai

# Setup Gemini API key if present, otherwise fallback to mock implementation
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')
else:
    model = None
    print("WARNING: GEMINI_API_KEY not found. Using mock AI responses.")

def validate_requirement_ai(description: str) -> str:
    if model:
        prompt = f"""
        You are an expert technical project manager and Safeworks consultant.
        Please enhance the following job requirement description to make it highly professional, structured, and clear.
        Use bullet points for key responsibilities and required skills. Maintain a professional and concise tone.
        
        Original Requirement:
        {description}
        """
        try:
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Error calling Gemini: {e}")
            return f"[AI Enhanced] {description}"
    else:
        return f"[MOCK AI ENHANCED] A clear, professional summary of: {description}"

def check_worker_compatibility(requirement_details: dict, worker_details: dict) -> dict:
    if model:
        prompt = f"""
        Given the following job requirement:
        {requirement_details}

        And the following worker profile:
        {worker_details}

        Check the worker's certifications and years of experience and match them to the requirement on a scale of 0 to 100%.
        Also, suggest 1-2 short certifications or courses to be assigned to the worker to improve compatibility.
        Return ONLY valid JSON in this exact format, with no markdown block formatting:
        {{
            "match_percentage": 85,
            "suggested_courses": ["Course 1", "Course 2"]
        }}
        """
        try:
            # response = model.generate_content(prompt)
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config={
                    'system_instruction': 'You are a professional document generator. Never speak in the first person. Never provide introductory or concluding remarks. Provide only the requested document.'
                }
            )
            import json
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
            data = json.loads(text.strip())
            return {
                "match_percentage": data.get("match_percentage", 0),
                "suggested_courses": data.get("suggested_courses", [])
            }
        except Exception as e:
            print(f"Error calling Gemini: {e}")
            # Fallback
            pass

    # Mock implementation fallback
    import random
    score = random.randint(50, 100)
    return {
        "match_percentage": score,
        "suggested_courses": ["Advanced Safety Training", "Skill Certification II"]
    }
