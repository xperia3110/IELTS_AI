import google.generativeai as genai
import json
import os
from config import Config

# Configure the Gemini API
api_key = os.environ.get('GEMINI_API_KEY') or Config.GEMINI_API_KEY
if not api_key:
    raise ValueError("GEMINI_API_KEY environment variable or Config.GEMINI_API_KEY is not set")

genai.configure(api_key=api_key)

# Set up the model
try:
    model = genai.GenerativeModel('gemini-2.0-flash') #change the model name matching your api key
except Exception as e:
    print(f"Error initializing Gemini model: {e}")
    model = None

def analyze_with_gemini(transcript, question):
    """
    Analyze speech transcript using Gemini AI for deeper insights.
    
    Args:
        transcript: Transcribed text from audio
        question: The IELTS question that was asked
        
    Returns:
        Dictionary with analysis results
    """
    if not model:
        raise Exception("Gemini model not initialized. Please check your API key and model configuration.")

    # Check for empty or very short transcript
    if not transcript or len(transcript.strip()) < 10:  # Less than 10 characters
        return {
            'fluency_score': 0.0,
            'vocabulary_score': 0.0,
            'grammar_score': 0.0,
            'coherence_score': 0.0,
            'overall_score': 0.0,
            'feedback': json.dumps({
                'strengths': [],
                'weaknesses': ['No speech detected in the recording'],
                'suggestions': ['Please speak clearly into the microphone when recording']
            })
        }

    try:
        # Create prompt for Gemini
        prompt = f"""
        You are an expert IELTS speaking examiner. Analyze the following response to an IELTS speaking question.
        
        IELTS Question: {question}
        
        Response: {transcript}
        
        Provide a detailed analysis of the response based on the IELTS speaking assessment criteria:
        1. Fluency and Coherence
        2. Lexical Resource (Vocabulary)
        3. Grammatical Range and Accuracy
        4. Pronunciation (though we can't assess this from text)
        
        For each criterion, provide:
        - A score on the IELTS band scale (0-9, with 0.5 increments)
        - Specific strengths (2-3 points)
        - Specific weaknesses (2-3 points)
        - Concrete suggestions for improvement (2-3 points)
        
        Format your response as a JSON object with the following structure:
        {{
            "fluency_score": float,
            "vocabulary_score": float,
            "grammar_score": float,
            "coherence_score": float,
            "overall_score": float,
            "feedback": {{
                "strengths": [
                    "Specific strength point 1",
                    "Specific strength point 2",
                    "Specific strength point 3"
                ],
                "weaknesses": [
                    "Specific weakness point 1",
                    "Specific weakness point 2",
                    "Specific weakness point 3"
                ],
                "suggestions": [
                    "Specific suggestion point 1",
                    "Specific suggestion point 2",
                    "Specific suggestion point 3"
                ]
            }}
        }}
        
        Guidelines for feedback:
        1. Strengths should highlight specific examples from the response
        2. Weaknesses should be specific and actionable
        3. Suggestions should be practical and implementable
        4. Each point should be concise and clear
        5. Avoid generic statements
        6. Focus on the most important points in each category
        
        Only return the JSON object, nothing else.
        """
        
        # Get response from Gemini
        response = model.generate_content(prompt)
        
        # Parse the JSON response
        try:
            # Extract JSON from the response
            response_text = response.text
            
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            
            analysis = json.loads(response_text)
            
            # Ensure all required fields are present
            required_fields = ['fluency_score', 'vocabulary_score', 'grammar_score', 'coherence_score', 
                              'overall_score', 'feedback']
            for field in required_fields:
                if field not in analysis:
                    if field == 'coherence_score':
                        analysis['coherence_score'] = analysis.get('fluency_score', 0.0)
                    else:
                        # Default values for missing fields
                        analysis[field] = 0.0  # Default to 0.0 for missing fields
            
            if 'feedback' not in analysis or not isinstance(analysis['feedback'], dict):
                analysis['feedback'] = {
                    'strengths': [],
                    'weaknesses': ['Unable to perform detailed analysis'],
                    'suggestions': ['Please provide a more detailed response']
                }
            
            analysis['feedback'] = json.dumps(analysis['feedback'])
            
            return analysis
            
        except Exception as e:
            # If JSON parsing fails, return a default analysis
            print(f"Error parsing Gemini response: {e}")
            return {
                'fluency_score': 0.0,
                'vocabulary_score': 0.0,
                'grammar_score': 0.0,
                'coherence_score': 0.0,
                'overall_score': 0.0,
                'feedback': json.dumps({
                    'strengths': [],
                    'weaknesses': ['Unable to perform detailed analysis'],
                    'suggestions': ['Please provide a more detailed response']
                })
            }
    
    except Exception as e:
        # If Gemini API call fails, return a default analysis
        print(f"Error calling Gemini API: {e}")
        return {
            'fluency_score': 0.0,
            'vocabulary_score': 0.0,
            'grammar_score': 0.0,
            'coherence_score': 0.0,
            'overall_score': 0.0,
            'feedback': json.dumps({
                'strengths': [],
                'weaknesses': ['Unable to perform detailed analysis'],
                'suggestions': ['Please provide a more detailed response']
            })
        }

