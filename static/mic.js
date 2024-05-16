// Function to initialize SpeechRecognition
function initSpeechRecognition() {
    // Check if SpeechRecognition is supported by the browser
    if ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window) {
        // Create a new SpeechRecognition instance
        const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();

        // Set properties for recognition
        recognition.lang = 'en-US'; // Set language to English
        recognition.interimResults = false; // Disable interim results

        // When speech recognition starts
        recognition.onstart = function() {
            console.log('Speech recognition started...');
        };

        // When speech recognition ends
        recognition.onend = function() {
            console.log('Speech recognition ended.');
        };

        // When speech is recognized
        recognition.onresult = function(event) {
            const query = event.results[0][0].transcript.trim(); // Get recognized speech
            console.log('Recognized query:', query);
            sendMessage(query); // Send the query as a message
        };

        // Add event listener to the microphone button
        const micButton = document.getElementById('micButton');
        micButton.addEventListener('click', function() {
            // Start speech recognition
            recognition.start();
        });
    } else {
        console.error('Speech recognition is not supported by this browser.');
    }
}

// Initialize speech recognition when the DOM content is loaded
document.addEventListener('DOMContentLoaded', function() {
    initSpeechRecognition();
});
