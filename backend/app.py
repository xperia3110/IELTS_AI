from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import uuid
import tempfile
from models import db, Question, Response, Result
from speech_analyzer import analyze_speech, transcribe_audio
from gemini_analyzer import analyze_with_gemini
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# Configure CORS with more permissive settings
CORS(app, resources={
    r"/*": {
        "origins": "*",  # Allow all origins during development
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

db.init_app(app)

@app.route('/api/questions', methods=['GET'])
def get_questions():
    """
    Get 10 random IELTS speaking questions.
    Returns a JSON array of question objects.
    """
   
    questions = Question.query.order_by(db.func.random()).limit(20).all()
    
    # Convert to JSON
    questions_json = [
        {
            'id': q.id,
            'text': q.text,
            'topic': q.topic,
            'isAudioOnly': False  # Default value, frontend can override
        } for q in questions
    ]
    
    return jsonify(questions_json)

@app.route('/api/analyze', methods=['POST'])
def submit_response():
    """
    Submit a user's audio response for analysis.
    Expects: 
    - audio file in request.files['audio']
    - question_id in request.form
    - question_text in request.form
    Returns analysis results.
    """
    try:
        if 'audio' not in request.files:
            print("Error: No audio file in request")
            return jsonify({'error': 'No audio file provided'}), 400
        
        audio_file = request.files['audio']
        question_id = request.form.get('question_id')
        question_text = request.form.get('question_text')
        
        if not question_id:
            print("Error: Missing question_id")
            return jsonify({'error': 'Missing question_id'}), 400
        
        # Check file extension
        if not audio_file.filename.lower().endswith(tuple(f'.{ext}' for ext in app.config['ALLOWED_EXTENSIONS'])):
            print(f"Error: Invalid file type. File: {audio_file.filename}")
            return jsonify({'error': 'Invalid file type. Allowed types: ' + ', '.join(app.config['ALLOWED_EXTENSIONS'])}), 400
        
        # Create uploads directory if it doesn't exist
        upload_dir = app.config['UPLOAD_FOLDER']
        if not os.path.exists(upload_dir):
            try:
                os.makedirs(upload_dir)
                print(f"Created upload directory: {upload_dir}")
            except Exception as e:
                print(f"Error creating upload directory: {str(e)}")
                return jsonify({'error': 'Failed to create upload directory'}), 500
        
        # Save audio file temporarily
        temp_path = os.path.join(upload_dir, f"{uuid.uuid4()}.wav")
        try:
            audio_file.save(temp_path)
            print(f"Saved audio file to: {temp_path}")
        except Exception as e:
            print(f"Error saving audio file: {str(e)}")
            return jsonify({'error': 'Failed to save audio file'}), 500
        
        try:
            # Transcribe audio
            print("Starting audio transcription...")
            transcript = transcribe_audio(temp_path)
            print("Transcription completed")
            
            # Get question for context
            question = db.session.get(Question, question_id)  # Updated to use session.get()
            if not question:
                # If question not found in DB but text was provided, use that
                if question_text:
                    question_context = question_text
                else:
                    print(f"Error: Question not found with ID: {question_id}")
                    return jsonify({'error': 'Question not found'}), 404
            else:
                question_context = question.text
            
            # Analyze speech with traditional NLP
            print("Starting NLP analysis...")
            nlp_analysis = analyze_speech(transcript)
            print("NLP analysis completed")
            
            # Analyze with Gemini AI for deeper insights
            print("Starting Gemini analysis...")
            try:
                gemini_analysis = analyze_with_gemini(transcript, question_context)
                print("Gemini analysis completed")
            except Exception as e:
                print(f"Warning: Gemini analysis failed: {str(e)}")
                # Provide fallback analysis if Gemini fails
                gemini_analysis = {
                    'fluency_score': nlp_analysis['fluency_score'],
                    'vocabulary_score': nlp_analysis['vocabulary_score'],
                    'grammar_score': nlp_analysis['grammar_score'],
                    'coherence_score': 0.0,  # Default score
                    'feedback': {
                        'strengths': ['The response addresses the question'],
                        'weaknesses': ['Unable to perform detailed analysis'],
                        'suggestions': ['Try to speak more clearly and at a moderate pace']
                    }
                }
            
            # Combine analyses for final result
            combined_analysis = combine_analyses(nlp_analysis, gemini_analysis)
            
            # Create response and result in a single transaction
            response = Response(
                question_id=question_id,
                audio_path=temp_path,
                transcript=transcript
            )
            db.session.add(response)
            db.session.flush()  # Get the response ID without committing
            
            result = Result(
                response_id=response.id,  # Now we have the response ID
                fluency_score=combined_analysis['fluency_score'],
                vocabulary_score=combined_analysis['vocabulary_score'],
                grammar_score=combined_analysis['grammar_score'],
                coherence_score=combined_analysis['coherence_score'],
                overall_score=combined_analysis['overall_score'],
                feedback=combined_analysis['feedback']
            )
            db.session.add(result)
            
            # Commit the transaction
            db.session.commit()
            print("Database records created successfully")
            
            # Return analysis results
            return jsonify({
                'response_id': response.id,
                'transcript': transcript,
                'analysis': combined_analysis
            })
        
        except Exception as e:
            db.session.rollback()
            print(f"Error processing audio: {str(e)}")
            return jsonify({'error': f'Error processing audio: {str(e)}'}), 500
        finally:
            # Clean up temporary file
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    print(f"Cleaned up temporary file: {temp_path}")
            except Exception as e:
                print(f"Error cleaning up temporary file: {str(e)}")
    
    except Exception as e:
        print(f"Unexpected error in submit_response: {str(e)}")
        return jsonify({'error': f'Unexpected error: {str(e)}'}), 500

@app.route('/api/results/<response_id>', methods=['GET'])
def get_result(response_id):
    """
    Get analysis results for a specific response.
    Returns a JSON object with the result data.
    """
    result = Result.query.get_or_404(response_id)
    response = result.response
    question = response.question
    
    return jsonify({
        'id': result.id,
        'date': result.created_at.isoformat(),
        'question': {
            'id': question.id if question else None,
            'text': question.text if question else "Unknown question",
            'topic': question.topic if question else None
        },
        'transcript': response.transcript,
        'fluency_score': result.fluency_score,
        'vocabulary_score': result.vocabulary_score,
        'grammar_score': result.grammar_score,
        'coherence_score': result.coherence_score,
        'overall_score': result.overall_score,
        'feedback': result.feedback
    })

@app.route('/api/test', methods=['GET'])
def test_endpoint():
    """Simple endpoint to test if the API is running."""
    return jsonify({'status': 'API is running'})

@app.before_request
def create_tables():
    """Create database tables before first request."""
    db.create_all()
    
    # Seed the database with sample questions if it's empty
    if Question.query.count() == 0:
        seed_database()

def combine_analyses(nlp_analysis, gemini_analysis):
    """
    Combine traditional NLP analysis with Gemini AI analysis.
    
    Args:
        nlp_analysis: Results from traditional NLP analysis
        gemini_analysis: Results from Gemini AI analysis
        
    Returns:
        Combined analysis results
    """
    # Extract scores from both analyses
    fluency_nlp = nlp_analysis['fluency_score']
    vocabulary_nlp = nlp_analysis['vocabulary_score']
    grammar_nlp = nlp_analysis['grammar_score']
    
    fluency_gemini = gemini_analysis['fluency_score']
    vocabulary_gemini = gemini_analysis['vocabulary_score']
    grammar_gemini = gemini_analysis['grammar_score']
    coherence_gemini = gemini_analysis['coherence_score']
    
    # Weighted combination (giving more weight to Gemini for deeper analysis)
    fluency_combined = (fluency_nlp * 0.3) + (fluency_gemini * 0.7)
    vocabulary_combined = (vocabulary_nlp * 0.2) + (vocabulary_gemini * 0.8)  
    grammar_combined = (grammar_nlp * 0.2) + (grammar_gemini * 0.8)  
    
    # Calculate overall score with adjusted weights
    overall_score = (
        fluency_combined * 0.15 +      
        vocabulary_combined * 0.4 +     
        grammar_combined * 0.4 +        
        coherence_gemini * 0.05        
    )
    
    # Apply stricter minimum thresholds for higher scores
    if overall_score > 7.0:
       
        if (vocabulary_combined < 7.5 or grammar_combined < 7.5 or 
            fluency_combined < 7.0 or coherence_gemini < 7.0):
            overall_score = 6.5
    elif overall_score > 6.0:
       
        if (vocabulary_combined < 6.5 or grammar_combined < 6.5 or 
            fluency_combined < 6.0 or coherence_gemini < 6.0):
            overall_score = 5.5
    elif overall_score > 5.0:
       
        if (vocabulary_combined < 5.5 or grammar_combined < 5.5 or 
            fluency_combined < 5.0 or coherence_gemini < 5.0):
            overall_score = 4.5
    
    # Apply additional penalties for low scores
    if any(score < 3.0 for score in [vocabulary_combined, grammar_combined, fluency_combined, coherence_gemini]):
        overall_score *= 0.5  # 50% penalty if any score is below 3.0
    elif any(score < 4.0 for score in [vocabulary_combined, grammar_combined, fluency_combined, coherence_gemini]):
        overall_score *= 0.7  # 30% penalty if any score is below 4.0
    
   
    fluency_combined = round(fluency_combined * 2) / 2
    vocabulary_combined = round(vocabulary_combined * 2) / 2
    grammar_combined = round(grammar_combined * 2) / 2
    coherence_gemini = round(coherence_gemini * 2) / 2
    overall_score = round(overall_score * 2) / 2
    
    # Combine feedback
    nlp_feedback = nlp_analysis.get('feedback', '{}')
    gemini_feedback = gemini_analysis.get('feedback', '{}')
    
    return {
        'fluency_score': fluency_combined,
        'vocabulary_score': vocabulary_combined,
        'grammar_score': grammar_combined,
        'coherence_score': coherence_gemini,
        'overall_score': overall_score,
        'feedback': gemini_feedback,
        'nlp_analysis': nlp_analysis,
        'gemini_analysis': gemini_analysis
    }

def seed_database():
    """Seed the database with sample IELTS speaking questions."""
    sample_questions = [
        {'text': 'Tell me about your hometown and what you like about it.', 'topic': 'Hometown'},
        {'text': 'What kind of accommodation do you live in?', 'topic': 'Accommodation'},
        {'text': 'Do you work or study? Tell me about it.', 'topic': 'Work/Study'},
        {'text': 'What do you enjoy doing in your free time?', 'topic': 'Hobbies'},
        {'text': 'How often do you use public transportation?', 'topic': 'Transportation'},
        {'text': 'What types of food do you enjoy eating?', 'topic': 'Food'},
        {'text': 'Do you prefer to spend time alone or with friends?', 'topic': 'Social Life'},
        {'text': 'What kind of music do you like to listen to?', 'topic': 'Music'},
        {'text': 'Describe a skill you would like to learn and explain why.', 'topic': 'Skills'},
        {'text': 'Describe a memorable trip you have taken in the past.', 'topic': 'Travel'},
        {'text': 'Describe a person who has had a significant influence on your life.', 'topic': 'People'},
        {'text': 'Describe a book or movie that made a strong impression on you.', 'topic': 'Entertainment'},
        {'text': 'Describe a time when you helped someone.', 'topic': 'Experiences'},
        {'text': 'Describe a place you would like to visit in the future.', 'topic': 'Travel'},
        {'text': 'Describe an important decision you have made in your life.', 'topic': 'Life Choices'},
        {'text': 'Describe a traditional festival or celebration in your country.', 'topic': 'Culture'},
        {'text': 'What changes would you like to see in your country in the next ten years?', 'topic': 'Society'},
        {'text': 'Do you think social media has a positive or negative impact on society?', 'topic': 'Technology'},
        {'text': 'How do you think education will change in the future?', 'topic': 'Education'},
        {'text': 'What are the advantages and disadvantages of living in a big city?', 'topic': 'Urban Life'},
        {'text': 'How important is it to preserve traditional cultures in a globalized world?', 'topic': 'Culture'},
        {'text': 'What role should governments play in protecting the environment?', 'topic': 'Environment'},
        {'text': 'Do you think technology makes people more or less creative?', 'topic': 'Technology'},
        {'text': 'How might climate change affect future generations?', 'topic': 'Environment'}
    ]
    
    for q in sample_questions:
        question = Question(text=q['text'], topic=q['topic'])
        db.session.add(question)
    
    db.session.commit()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 4000)), debug=True)

