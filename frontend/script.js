// API Configuration
const API_BASE_URL = 'http://127.0.0.1:4000/api';  // Make sure this matches your Flask server port

// Audio Recording Variables
let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;
let timerInterval = null;
let startTime = null;
let currentQuestionData = null;

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    console.log('Application initialized');
    
    // Initialize DOM elements
    const getQuestionsBtn = document.getElementById('get-questions');
    const recordButton = document.getElementById('record-button');
    const timerDisplay = document.getElementById('timer');
    const recordingStatus = document.getElementById('recording-status');
    const currentQuestion = document.getElementById('current-question');
    const questionPart = document.getElementById('question-part');
    const questionTopic = document.getElementById('question-topic');
    const resultsSection = document.getElementById('results-section');
    const strengthsList = document.getElementById('strengths-list');
    const weaknessesList = document.getElementById('weaknesses-list');
    const suggestionsList = document.getElementById('suggestions-list');
    const transcriptElement = document.getElementById('transcript');

    // Request microphone permission
    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
            console.log('Microphone access granted');
            if (recordButton) recordButton.disabled = false;
        })
        .catch(err => {
            console.error('Error accessing microphone:', err);
            if (recordingStatus) recordingStatus.textContent = 'Error: Microphone access denied';
        });

    // Test API connection with recordingStatus element
    testApiConnection(recordingStatus);

    // Add event listeners
    if (getQuestionsBtn) {
        getQuestionsBtn.addEventListener('click', async () => {
            try {
                console.log('Fetching questions...');
                if (recordingStatus) recordingStatus.textContent = 'Fetching questions...';
                
                const response = await fetch(`${API_BASE_URL}/questions`);
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                
                const questions = await response.json();
                console.log('Received questions:', questions);
                
                if (questions.length > 0) {
                    // Get the first question
                    currentQuestionData = questions[0];
                    if (currentQuestion) currentQuestion.textContent = currentQuestionData.text;
                    if (questionPart) questionPart.textContent = currentQuestionData.part;
                    if (questionTopic) questionTopic.textContent = currentQuestionData.topic;
                    
                    // Reset recording state
                    resetRecordingState();
                    
                    // Enable recording button
                    if (recordButton) {
                        recordButton.disabled = false;
                        recordingStatus.textContent = 'Ready to record';
                    }
                } else {
                    if (recordingStatus) recordingStatus.textContent = 'No questions available';
                }
            } catch (error) {
                console.error('Error fetching questions:', error);
                if (recordingStatus) recordingStatus.textContent = `Error: ${error.message}`;
            }
        });
    }

    if (recordButton) {
        recordButton.addEventListener('click', () => {
            if (!isRecording) {
                startRecording(recordButton, recordingStatus, timerDisplay);
            } else {
                stopRecording(recordButton, recordingStatus, timerDisplay);
            }
        });
    }
});

// Test API connection
async function testApiConnection(recordingStatusElement) {
    try {
        const response = await fetch(`${API_BASE_URL}/test`);
        const data = await response.json();
        console.log('API connection successful:', data);
        if (recordingStatusElement) {
            recordingStatusElement.textContent = 'API connected successfully';
        }
    } catch (error) {
        console.error('API connection failed:', error);
        if (recordingStatusElement) {
            recordingStatusElement.textContent = 'Error: Failed to connect to API';
        }
    }
}

// Start recording
async function startRecording(recordButton, recordingStatus, timerDisplay) {
    try {
        // Check if mediaDevices API is supported
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            throw new Error('Your browser does not support audio recording. Please use a modern browser.');
        }

        // Request audio access with specific constraints
        const stream = await navigator.mediaDevices.getUserMedia({
            audio: {
                channelCount: 1,
                sampleRate: 44100,
                sampleSize: 16
            }
        });
        
        // Create MediaRecorder instance with specific MIME type
        mediaRecorder = new MediaRecorder(stream, {
            mimeType: 'audio/webm;codecs=opus'
        });
        audioChunks = [];

        // Handle data available event
        mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                audioChunks.push(event.data);
            }
        };

        // Handle recording stop
        mediaRecorder.onstop = async () => {
            try {
                const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                const recordingStatusElement = document.getElementById('recording-status');
                await submitRecording(audioBlob, recordingStatusElement);
            } catch (error) {
                console.error('Error processing recording:', error);
                const recordingStatusElement = document.getElementById('recording-status');
                if (recordingStatusElement) {
                    recordingStatusElement.textContent = 'Error: Failed to process recording';
                }
            }
        };

        // Start recording
        mediaRecorder.start(1000); // Collect data every second
        isRecording = true;
        if (recordButton) {
            recordButton.classList.add('recording');
            recordButton.innerHTML = '<svg class="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z"></path></svg>Stop';
        }
        if (recordingStatus) recordingStatus.textContent = 'Recording...';
        
        // Start timer
        startTime = Date.now();
        timerInterval = setInterval(() => updateTimer(timerDisplay), 1000);
    } catch (error) {
        console.error('Error starting recording:', error);
        alert('Failed to start recording. Please make sure you have granted microphone permissions and are using a supported browser.');
    }
}

// Stop recording
function stopRecording(recordButton, recordingStatus, timerDisplay) {
    if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
        isRecording = false;
        if (recordButton) {
            recordButton.classList.remove('recording');
            recordButton.innerHTML = '<svg class="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"></path></svg>Record';
        }
        if (recordingStatus) recordingStatus.textContent = 'Processing...';
        
        // Stop timer
        clearInterval(timerInterval);
    }
}

// Update timer display
function updateTimer(timerDisplay) {
    if (!timerDisplay) return;
    const elapsed = Math.floor((Date.now() - startTime) / 1000);
    const minutes = Math.floor(elapsed / 60);
    const seconds = elapsed % 60;
    timerDisplay.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
}

// Submit recording to backend
async function submitRecording(audioBlob, recordingStatusElement) {
    try {
        if (!currentQuestionData) {
            throw new Error('No question selected');
        }

        const formData = new FormData();
        formData.append('audio', audioBlob, 'recording.webm');
        formData.append('question_id', currentQuestionData.id);
        formData.append('question_text', currentQuestionData.text);

        if (recordingStatusElement) {
            recordingStatusElement.textContent = 'Uploading recording...';
        }

        const response = await fetch(`${API_BASE_URL}/analyze`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to submit recording');
        }

        const result = await response.json();
        displayResults(result);
    } catch (error) {
        console.error('Error submitting recording:', error);
        if (recordingStatusElement) {
            recordingStatusElement.textContent = `Error: ${error.message}`;
        }
    }
}

// Display results
function displayResults(data) {
    try {
        if (!data) {
            throw new Error('No data received from server');
        }

        // Get the analysis data
        const analysis = data.analysis || data;
        
        // Get DOM elements
        const resultsSection = document.getElementById('results-section');
        const recordingStatus = document.getElementById('recording-status');
        const transcriptElement = document.getElementById('transcript');
        const strengthsList = document.getElementById('strengths-list');
        const weaknessesList = document.getElementById('weaknesses-list');
        const suggestionsList = document.getElementById('suggestions-list');
        
        // Display scores
        const scoreElements = {
            'overall-score': analysis.overall_score,
            'fluency-score': analysis.fluency_score,
            'vocabulary-score': analysis.vocabulary_score,
            'grammar-score': analysis.grammar_score,
            'coherence-score': analysis.coherence_score
        };

        // Update each score element
        Object.entries(scoreElements).forEach(([elementId, score]) => {
            const element = document.getElementById(elementId);
            if (element) {
                element.textContent = score.toFixed(1);
            }
        });

        // Parse feedback JSON
        const feedback = typeof analysis.feedback === 'string' 
            ? JSON.parse(analysis.feedback) 
            : analysis.feedback;

        // Update feedback lists
        if (strengthsList) {
            strengthsList.innerHTML = '';
            (feedback.strengths || []).forEach(item => {
                const li = document.createElement('li');
                li.textContent = item;
                strengthsList.appendChild(li);
            });
        }

        if (weaknessesList) {
            weaknessesList.innerHTML = '';
            (feedback.weaknesses || []).forEach(item => {
                const li = document.createElement('li');
                li.textContent = item;
                weaknessesList.appendChild(li);
            });
        }

        if (suggestionsList) {
            suggestionsList.innerHTML = '';
            (feedback.suggestions || []).forEach(item => {
                const li = document.createElement('li');
                li.textContent = item;
                suggestionsList.appendChild(li);
            });
        }

        // Update transcript
        if (transcriptElement) {
            transcriptElement.textContent = data.transcript || '';
        }

        // Show results section
        if (resultsSection) {
            resultsSection.classList.remove('hidden');
        }

        // Update recording status
        if (recordingStatus) {
            recordingStatus.textContent = 'Analysis complete!';
        }
    } catch (error) {
        console.error('Error displaying results:', error);
        const recordingStatus = document.getElementById('recording-status');
        if (recordingStatus) {
            recordingStatus.textContent = 'Error displaying results. Please try again.';
        }
    }
}

// Reset recording state
function resetRecordingState() {
    const timerDisplay = document.getElementById('timer');
    const recordingStatus = document.getElementById('recording-status');
    const resultsSection = document.getElementById('results-section');
    const recordButton = document.getElementById('record-button');

    // Reset timer
    clearInterval(timerInterval);
    if (timerDisplay) timerDisplay.textContent = '00:00';
    
    // Reset recording status
    if (recordingStatus) recordingStatus.textContent = '';
    
    // Reset results section
    if (resultsSection) resultsSection.classList.add('hidden');
    
    // Reset record button
    if (recordButton) {
        recordButton.innerHTML = '<svg class="w-6 h-6 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"></path></svg>Record';
        recordButton.classList.remove('recording');
    }
    isRecording = false;
} 