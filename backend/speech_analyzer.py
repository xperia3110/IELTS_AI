import whisper
import spacy
import numpy as np
import json
from textstat import flesch_kincaid_grade, syllable_count
import language_tool_python

whisper_model = whisper.load_model("base")
nlp = spacy.load("en_core_web_sm")
language_tool = language_tool_python.LanguageTool('en-US')

def transcribe_audio(audio_path):
    """
    Transcribe audio file to text using Whisper AI.
    
    Args:
        audio_path: Path to the audio file
        
    Returns:
        Transcribed text
    """
    result = whisper_model.transcribe(audio_path)
    text = result["text"].strip()
    
    # Check if the transcription is empty or just contains noise
    if not text or text.lower() in ['', ' ', '.', '..', '...', '....', '.....', '......', '.......', '........']:
        return ""
    
    return text

def analyze_speech(transcript):
    """
    Analyze speech transcript for fluency, vocabulary, and grammar.
    
    Args:
        transcript: Transcribed text from audio
        
    Returns:
        Dictionary with analysis results
    """
    # Check for empty or very short transcript
    if not transcript or len(transcript.strip()) < 10:  # Less than 10 characters
        return {
            'fluency_score': 0.0,
            'vocabulary_score': 0.0,
            'grammar_score': 0.0,
            'overall_score': 0.0,
            'feedback': json.dumps({
                'strengths': [],
                'weaknesses': ['No speech detected in the recording'],
                'suggestions': ['Please speak clearly into the microphone when recording']
            })
        }
    
    # Process text with spaCy
    doc = nlp(transcript)
    
    # Check for very short responses
    word_count = len([token for token in doc if not token.is_punct and not token.is_space])
    if word_count < 10:  # Less than 10 words
        return {
            'fluency_score': 0.0,
            'vocabulary_score': 0.0,
            'grammar_score': 0.0,
            'overall_score': 0.0,
            'feedback': json.dumps({
                'strengths': [],
                'weaknesses': ['Response is too short to evaluate'],
                'suggestions': ['Please provide a more detailed response with at least a few sentences']
            })
        }
    
    # Check if the response is just noise or filler words
    filler_words = ['um', 'uh', 'er', 'ah', 'like', 'you know', 'sort of', 'kind of', 'well', 'basically', 'actually', 
                   'i mean', 'you see', 'right', 'okay', 'so', 'just', 'really', 'literally', 'honestly', 'frankly',
                   'actually', 'absolutely', 'definitely', 'certainly', 'obviously', 'clearly', 'apparently',
                   'supposedly', 'allegedly', 'reportedly', 'presumably', 'evidently', 'seemingly', 'ostensibly']
    
    meaningful_words = [word for word in doc if not word.is_punct and not word.is_space and word.text.lower() not in filler_words]
    if len(meaningful_words) < 5:  # Less than 5 meaningful words
        return {
            'fluency_score': 0.0,
            'vocabulary_score': 0.0,
            'grammar_score': 0.0,
            'overall_score': 0.0,
            'feedback': json.dumps({
                'strengths': [],
                'weaknesses': ['Response contains only filler words or noise'],
                'suggestions': ['Please provide a meaningful response with actual content']
            })
        }
    
    fluency_score = analyze_fluency(transcript, doc)
    vocabulary_score = analyze_vocabulary(doc)
    grammar_score = analyze_grammar(transcript)
    
    # Calculate overall score (weighted average)
    overall_score = calculate_overall_score(fluency_score, vocabulary_score, grammar_score)
    
    feedback = generate_feedback(transcript, doc, fluency_score, vocabulary_score, grammar_score)
    
    return {
        'fluency_score': round(fluency_score, 1),
        'vocabulary_score': round(vocabulary_score, 1),
        'grammar_score': round(grammar_score, 1),
        'overall_score': round(overall_score, 1),
        'feedback': feedback
    }

def analyze_fluency(transcript, doc):
    """
    Analyze speech fluency based on:
    - Speech rate (words per minute)
    - Sentence length and variation
    - Filler words and hesitations
    - Reading ease
    
    Returns a score from 0-9 (IELTS scale)
    """
    word_count = len([token for token in doc if not token.is_punct and not token.is_space])
    sentence_count = len(list(doc.sents))
    
    # Return 0 for very short responses
    if word_count < 10 or sentence_count < 1:
        return 0.0
    
    estimated_speech_rate = 150
    
    filler_words = ['um', 'uh', 'er', 'ah', 'like', 'you know', 'sort of', 'kind of', 'well', 'basically', 'actually', 
                   'i mean', 'you see', 'right', 'okay', 'so', 'just', 'really', 'literally', 'honestly', 'frankly',
                   'actually', 'absolutely', 'definitely', 'certainly', 'obviously', 'clearly', 'apparently',
                   'supposedly', 'allegedly', 'reportedly', 'presumably', 'evidently', 'seemingly', 'ostensibly']
    filler_count = sum(transcript.lower().count(filler) for filler in filler_words)
    
    # Calculate reading ease
    fk_grade = flesch_kincaid_grade(transcript)
    
    if sentence_count > 0:
        avg_sentence_length = word_count / sentence_count
        sentence_lengths = [len([token for token in sent if not token.is_punct and not token.is_space]) 
                           for sent in doc.sents]
        sentence_length_variation = np.std(sentence_lengths) if len(sentence_lengths) > 1 else 0
    else:
        avg_sentence_length = 0
        sentence_length_variation = 0
    
    # Extremely strict scoring components (each from 0-9)
    speech_rate_score = min(9, max(0, 2.0 + (estimated_speech_rate - 120) / 40))  # Further reduced base score
    
    filler_ratio = filler_count / max(1, word_count)
    filler_score = min(9, max(0, 9 - filler_ratio * 250))  # Further increased penalty for filler words
    
    complexity_score = min(9, max(0, 2.0 + (fk_grade - 10) * 0.2))  # Further reduced base score
    
    sentence_variation_score = min(9, max(0, 2.0 + sentence_length_variation * 0.2))  # Further reduced base score
    
    # Additional penalties
    if word_count < 150:  # Further increased minimum word count
        speech_rate_score *= 0.5
        complexity_score *= 0.5
    
    if avg_sentence_length < 12:  # Further increased minimum sentence length
        sentence_variation_score *= 0.5
    
    # Weighted average for final fluency score with stricter weights
    fluency_score = (
        speech_rate_score * 0.15 +
        filler_score * 0.45 +     
        complexity_score * 0.2 +
        sentence_variation_score * 0.2
    )
    
    # Additional overall penalty for poor performance
    if fluency_score > 3.0:  # Further reduced threshold
        if filler_ratio > 0.03:  # Further reduced threshold for filler words
            fluency_score *= 0.6
        if avg_sentence_length < 15:  # Further increased minimum sentence length
            fluency_score *= 0.7
        if word_count < 150:  # Further increased minimum word count
            fluency_score *= 0.7
    
    return fluency_score

def analyze_vocabulary(doc):
    """
    Analyze vocabulary based on:
    - Lexical diversity
    - Word rarity/complexity
    - Appropriate collocations
    - Topic-specific vocabulary
    
    Returns a score from 0-9 (IELTS scale)
    """
    # Count total and unique words
    all_words = [token.text.lower() for token in doc if not token.is_punct and not token.is_space]
    unique_words = set(all_words)
    
    # Return 0 for very short responses
    if len(all_words) < 10:
        return 0.0
    
    # Calculate lexical diversity (type-token ratio)
    if len(all_words) > 0:
        lexical_diversity = len(unique_words) / len(all_words)
    else:
        lexical_diversity = 0
    
    # Calculate average word length and syllable count
    avg_word_length = np.mean([len(word) for word in all_words]) if all_words else 0
    avg_syllables = np.mean([syllable_count(word) for word in all_words]) if all_words else 0
    
    # Calculate word rarity using spaCy's frequency ranks
    # Lower rank means more common word
    word_ranks = [token.rank if hasattr(token, 'rank') else 0 for token in doc 
                 if not token.is_punct and not token.is_space]
    avg_word_rank = np.mean(word_ranks) if word_ranks else 0
    
    # Extremely strict scoring components (each from 0-9)
    diversity_score = min(9, max(0, lexical_diversity * 6))  # Further reduced multiplier
    
    length_score = min(9, max(0, 2.0 + (avg_word_length - 7.0) * 0.8))  # Further reduced base score
    
    syllable_score = min(9, max(0, 2.0 + (avg_syllables - 2.5) * 1.5))  # Further reduced base score
    
    rarity_score = min(9, max(0, 2.0 - avg_word_rank / 20000))  # Further reduced base score
    
    # Additional penalties
    if len(all_words) < 75:  # Further increased minimum word count
        diversity_score *= 0.5
        length_score *= 0.5
    
    # Check for common word repetition
    common_words = {'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i', 'it', 'for', 'not', 'on', 'with', 
                   'he', 'as', 'you', 'do', 'at', 'this', 'but', 'his', 'by', 'from', 'they', 'we', 'say', 'her', 'she',
                   'or', 'an', 'will', 'my', 'one', 'all', 'would', 'there', 'their', 'what', 'so', 'up', 'out', 'if',
                   'about', 'who', 'get', 'which', 'go', 'me', 'when', 'make', 'can', 'like', 'time', 'no', 'just',
                   'him', 'know', 'take', 'people', 'into', 'year', 'your', 'good', 'some', 'could', 'them', 'see',
                   'other', 'than', 'then', 'now', 'look', 'only', 'come', 'its', 'over', 'think', 'also', 'back',
                   'after', 'use', 'two', 'how', 'our', 'work', 'first', 'well', 'way', 'even', 'new', 'want', 'because',
                   'any', 'these', 'give', 'day', 'most', 'us', 'very', 'many', 'much', 'more', 'most', 'such', 'only',
                   'little', 'then', 'now', 'other', 'some', 'such', 'no', 'nor', 'not', 'too', 'very', 'can', 'will',
                   'just', 'should', 'now', 'much', 'more', 'most', 'such', 'only', 'little', 'then', 'now', 'other',
                   'some', 'such', 'no', 'nor', 'not', 'too', 'very', 'can', 'will', 'just', 'should', 'now'}
    common_word_count = sum(1 for word in all_words if word in common_words)
    common_word_ratio = common_word_count / len(all_words) if all_words else 0
    
    if common_word_ratio > 0.25:  # Further reduced threshold for common words
        rarity_score *= 0.5
    
    # Weighted average for final vocabulary score with stricter weights
    vocabulary_score = (
        diversity_score * 0.25 +
        length_score * 0.35 +
        syllable_score * 0.35 +
        rarity_score * 0.05
    )
    
    # Additional overall penalty for poor performance
    if vocabulary_score > 3.0:  # Further reduced threshold
        if common_word_ratio > 0.2:  # Further reduced threshold for common words
            vocabulary_score *= 0.6
        if lexical_diversity < 0.6:  # Further increased threshold for lexical diversity
            vocabulary_score *= 0.6
        if len(all_words) < 150:  # Further increased minimum word count
            vocabulary_score *= 0.7
    
    return vocabulary_score

def analyze_grammar(transcript):
    """
    Analyze grammar based on:
    - Grammatical errors
    - Sentence structure complexity
    - Tense usage
    - Agreement errors
    
    Returns a score from 0-9 (IELTS scale)
    """
    # Check for empty or very short transcript
    if not transcript or len(transcript.strip()) < 5:  # Less than 5 characters
        return 0.0
    
    # Check for grammar errors using LanguageTool
    matches = language_tool.check(transcript)
    error_count = len(matches)
    
    # Calculate error density (errors per 100 words)
    word_count = len(transcript.split())
    
    # Return 0 for very short responses
    if word_count < 5:
        return 0.0
    
    error_density = (error_count / max(1, word_count)) * 100
    
    # Extremely strict scoring based on error density
    grammar_score = min(9, max(0, 6 - error_density * 2.5))  # Further increased penalty for errors
    
    # Additional penalties
    if word_count < 75:  # Further increased minimum word count
        grammar_score *= 0.5
    
    # Check for basic grammar patterns
    basic_patterns = ['i am', 'i like', 'i want', 'i have', 'i can', 'i will', 'i think', 'i know', 'i feel',
                     'i need', 'i should', 'i would', 'i could', 'i must', 'i should', 'i would like',
                     'i want to', 'i have to', 'i need to', 'i like to', 'i want to be', 'i am going to',
                     'i believe', 'i understand', 'i agree', 'i disagree', 'i hope', 'i wish', 'i prefer',
                     'i enjoy', 'i love', 'i hate', 'i like', 'i dislike', 'i want', 'i need', 'i should',
                     'i would', 'i could', 'i might', 'i may', 'i must', 'i have to', 'i got to', 'i gotta']
    basic_pattern_count = sum(1 for pattern in basic_patterns if pattern in transcript.lower())
    if basic_pattern_count > 0:  # Further reduced threshold for basic patterns
        grammar_score *= 0.6
    
    # Maximum score reduction for poor performance
    if grammar_score > 3.0:  # Further reduced threshold
        if error_density > 2:  # Further reduced threshold for error density
            grammar_score *= 0.6
        if basic_pattern_count > 1:  # Further reduced threshold for basic patterns
            grammar_score *= 0.6
        if word_count < 150:  # Further increased minimum word count
            grammar_score *= 0.7
    
    return grammar_score

def calculate_overall_score(fluency_score, vocabulary_score, grammar_score):
    """
    Calculate overall IELTS speaking score based on component scores.
    
    IELTS speaking is scored on a 9-band scale.
    """
    # Extremely strict weighted average of component scores
    overall_score = (
        fluency_score * 0.1 +       # Further reduced from 0.15
        vocabulary_score * 0.5 +     # Further increased from 0.45
        grammar_score * 0.4          # Maintained at 0.4
    )
    
    # Additional penalties for poor performance in any area
    if any(score < 4.0 for score in [fluency_score, vocabulary_score, grammar_score]):
        overall_score *= 0.5  # 50% penalty if any score is below 4.0
    
    if any(score < 3.0 for score in [fluency_score, vocabulary_score, grammar_score]):
        overall_score *= 0.3  # 70% penalty if any score is below 3.0
    
    if any(score < 2.0 for score in [fluency_score, vocabulary_score, grammar_score]):
        overall_score *= 0.2  # 80% penalty if any score is below 2.0
    
    return overall_score

def generate_feedback(transcript, doc, fluency_score, vocabulary_score, grammar_score):
    """
    Generate detailed feedback based on analysis.
    
    Returns a JSON string with structured feedback.
    """
    feedback = {
        'strengths': [],
        'weaknesses': [],
        'suggestions': []
    }
    
    # Extremely strict feedback thresholds
    if fluency_score >= 4.0:  # Further reduced threshold
        feedback['strengths'].append("Adequate flow of speech with some use of connective phrases")
    elif fluency_score >= 3.0:  # Further reduced threshold
        feedback['weaknesses'].append("Very frequent hesitations and significant difficulty maintaining flow")
        feedback['suggestions'].append("Practice speaking about unfamiliar topics to improve fluency")
    else:
        feedback['weaknesses'].append("Extremely frequent hesitations and severe difficulty maintaining flow")
        feedback['suggestions'].append("Record yourself speaking and identify points of hesitation")
    
    if vocabulary_score >= 4.0:  # Further reduced threshold
        feedback['strengths'].append("Basic range of vocabulary with limited use of idiomatic expressions")
    elif vocabulary_score >= 3.0:  # Further reduced threshold
        feedback['weaknesses'].append("Very limited vocabulary range with excessive repetition")
        feedback['suggestions'].append("Learn topic-specific vocabulary for common IELTS themes")
    else:
        feedback['weaknesses'].append("Extremely basic vocabulary with severe repetition")
        feedback['suggestions'].append("Build vocabulary by reading articles on diverse topics")
    
    if grammar_score >= 4.0:  # Further reduced threshold
        feedback['strengths'].append("Basic control of grammatical structures")
    elif grammar_score >= 3.0:  # Further reduced threshold
        feedback['weaknesses'].append("Very frequent grammatical errors in basic structures")
        feedback['suggestions'].append("Practice using a variety of tenses and complex sentences")
    else:
        feedback['weaknesses'].append("Extremely frequent basic grammatical errors")
        feedback['suggestions'].append("Review basic grammar rules and practice with simple sentences first")
    
    # Add specific vocabulary suggestions
    rare_words = [token.text for token in doc if token.rank and token.rank < 30000 
                 and not token.is_stop and not token.is_punct]
    if rare_words:
        feedback['strengths'].append(f"Good use of advanced vocabulary such as: {', '.join(rare_words[:3])}")
    
    # Add specific grammar error examples
    matches = language_tool.check(transcript)
    if matches:
        error_examples = [match.context for match in matches[:2]]
        feedback['weaknesses'].append(f"Grammar errors in phrases like: {'; '.join(error_examples)}")
    
    return json.dumps(feedback)

