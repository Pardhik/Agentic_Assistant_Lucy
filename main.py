import os
import gradio as gr
from speech_to_text import record_audio, transcribe_with_groq
from ai_agent import ask_agent
from text_to_speech import text_to_speech_with_elevenlabs, text_to_speech_with_gtts
import cv2
import time
import threading

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
audio_filepath = "audio_question.mp3"

# Global variables
camera = None
is_running = False
last_frame = None
chat_active = False
chat_thread = None

def toggle_chat_and_stream():
    global chat_active
    if not chat_active:
        chat_active = True
        status_html = """<div class="status-indicator status-active"> Voice Chat: Active</div>"""
        return "Stop Voice Chat", status_html, process_audio_and_chat()
    else:
        chat_active = False
        status_html = """<div class="status-indicator status-inactive"> Voice Chat: Offline</div>"""
        return "🎤 Start Voice Chat", status_html, []

def process_audio_and_chat():
    """Enhanced audio processing with better error handling"""
    global chat_active
    chat_history = []
    
    while chat_active:
        try:
            print("Recording audio...")
            record_audio(file_path=audio_filepath)
            
            print("Transcribing audio...")
            user_input = transcribe_with_groq(audio_filepath)
            print(f"User said: {user_input}")

            if not user_input.strip():
                continue

            if "goodbye" in user_input.lower():
                chat_history.append({"role": "user", "content": user_input})
                chat_history.append({"role": "assistant", "content": "👋 Goodbye! It was nice talking with you."})
                break

            
            chat_history.append({"role": "user", "content": user_input})
            
            print("Getting AI response...")
            response = ask_agent(user_query=user_input)
            print(f"AI response: {response}")
            
            chat_history.append({"role": "assistant", "content": response})
            
            # Generate voice response
            print("🔊 Generating voice response...")
            text_to_speech_with_gtts(input_text=response, output_filepath="final.mp3")
            
            yield chat_history

        except Exception as e:
            error_msg = f"Error: {str(e)}"
            chat_history.append({"role": "assistant", "content": error_msg})
            yield chat_history
            print(f"Error in continuous recording: {e}")

def start_chat():
    """Start the chat process"""
    global chat_active, chat_thread
    
    if not chat_active:
        chat_active = True
        print("Starting voice chat...")
        return "Stop Voice Chat", "secondary"
    else:
        chat_active = False
        print("Stopping voice chat...")
        return "Start Voice Chat", "primary"


def initialize_camera():
    global camera
    if camera is None:
        try:
           
            for i in range(3):
                camera = cv2.VideoCapture(i)
                if camera.isOpened():
                    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 480)
                    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 280)  
                    camera.set(cv2.CAP_PROP_FPS, 30)
                    camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    print(f"Camera initialized on index {i}")
                    return True
                camera.release()
            
            print("No camera found")
            camera = None
            return False
        except Exception as e:
            print(f"Camera initialization error: {e}")
            camera = None
            return False
    return True

def start_webcam():
    global is_running, last_frame
    is_running = True
    if not initialize_camera():
        return None, "No Camera Found", "secondary"
    
    try:
        ret, frame = camera.read()
        if ret and frame is not None:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            last_frame = frame
            return frame, "Camera Active", "success"
        else:
            return None, "Camera Error", "secondary"
    except Exception as e:
        print(f"Webcam start error: {e}")
        return None, "Camera Error", "secondary"

def stop_webcam():
    global is_running, camera
    is_running = False
    if camera is not None:
        camera.release()
        camera = None
    print("Camera stopped")
    return None, "Start Camera", "primary"

def get_webcam_frame():
    global camera, is_running, last_frame
    
    if not is_running or camera is None:
        return last_frame
    
    try:
        ret, frame = camera.read()
        if ret and frame is not None:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            last_frame = frame
            return frame
    except Exception as e:
        print(f"Frame capture error: {e}")
    
    return last_frame


custom_css = """
/* Main container styling - Compact version */
.gradio-container {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

/* Compact header styling */
.main-header {
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(10px);
    border-radius: 15px;
    padding: 15px;
    margin: 10px 0;
    border: 1px solid rgba(255, 255, 255, 0.2);
    text-align: center;
}

.main-header h1 {
    background: linear-gradient(45deg, #ff6b6b, #ffa500, #4ecdc4);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2.5em !important;  /* Reduced from 3.5em */
    margin: 0;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
}

/* Compact card styling */
.card {
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(15px);
    border-radius: 15px;
    padding: 15px;  /* Reduced from 25px */
    margin: 10px;   /* Reduced from 15px */
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);  /* Reduced shadow */
    border: 1px solid rgba(255, 255, 255, 0.3);
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}

/* Compact button styling */
button.primary {
    background: linear-gradient(45deg, #667eea, #764ba2) !important;
    border: none !important;
    border-radius: 20px !important;  /* Reduced from 25px */
    color: white !important;
    padding: 8px 16px !important;    /* Reduced from 12px 24px */
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 2px 10px rgba(102, 126, 234, 0.4) !important;  /* Reduced shadow */
    font-size: 0.9em !important;     /* Slightly smaller font */
}

button.secondary {
    background: linear-gradient(45deg, #ff6b6b, #ffa500) !important;
    border: none !important;
    border-radius: 20px !important;
    color: white !important;
    padding: 8px 16px !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 2px 10px rgba(255, 107, 107, 0.4) !important;
    font-size: 0.9em !important;
}

button.success {
    background: linear-gradient(45deg, #4ecdc4, #44a08d) !important;
    border: none !important;
    border-radius: 20px !important;
    color: white !important;
    padding: 8px 16px !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 2px 10px rgba(78, 205, 196, 0.4) !important;
    font-size: 0.9em !important;
}

/* Compact status indicators */
.status-indicator {
    display: inline-flex;
    align-items: center;
    gap: 6px;      /* Reduced from 8px */
    padding: 6px 12px;  /* Reduced from 8px 16px */
    border-radius: 15px;  /* Reduced from 20px */
    font-weight: 500;
    margin: 5px 0;  /* Reduced from 10px 0 */
    font-size: 0.9em;
}

.status-active {
    background: rgba(78, 205, 196, 0.2);
    color: #2d5a5a;
    border: 1px solid rgba(78, 205, 196, 0.5);
}

.status-inactive {
    background: rgba(255, 107, 107, 0.2);
    color: #8b3a3a;
    border: 1px solid rgba(255, 107, 107, 0.5);
}

/* Compact chat styling */
.chatbot {
    border-radius: 12px !important;  /* Reduced from 15px */
    border: none !important;
    box-shadow: inset 0 2px 8px rgba(0,0,0,0.1) !important;  /* Reduced shadow */
}

/* Compact image container */
.image-container img {
    border-radius: 12px !important;  /* Reduced from 15px */
    border: 2px solid rgba(255, 255, 255, 0.3) !important;  /* Reduced from 3px */
    box-shadow: 0 4px 15px rgba(0,0,0,0.2) !important;  /* Reduced shadow */
}

/* Compact features section */
.features-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    margin-top: 10px;
}

.feature-item {
    background: white;
    padding: 6px 10px;
    border-radius: 15px;
    font-size: 0.85em;
    text-align: center;
    box-shadow: 0 2px 6px rgba(0,0,0,0.1);
}
"""

with gr.Blocks(css=custom_css, title="LUCY AI Assistant") as demo:
    # Compact Header
    with gr.Column(elem_classes=["main-header"]):
        gr.HTML("""
            <h1>👧🏼 LUCY – AI Assistant</h1>
            <p style="color: rgba(255,255,255,0.9); font-size: 1em; margin-top: 5px;">
                Intelligent companion for conversations and assistance
            </p>
        """)
    
    with gr.Row():
        with gr.Column(scale=1):
            camera_status = gr.HTML("""
                <div class="status-indicator status-inactive">
                     Camera: Offline
                </div>
            """)
        with gr.Column(scale=1):
            chat_status = gr.HTML("""
                <div class="status-indicator status-inactive">
                     Voice Chat: Offline
                </div>
            """)

    with gr.Row():
        # Left Column - Compact Webcam
        with gr.Column(scale=1, elem_classes=["card"]):
            gr.HTML("<h3 style='color: #333; text-align: center; margin-bottom: 10px;'>📹 Live Video</h3>")
            
            with gr.Row():
                start_btn = gr.Button("Start", variant="primary", size="sm")
                stop_btn = gr.Button("Stop", variant="secondary", size="sm")
            
            webcam_output = gr.Image(
                label="Live Camera Feed",
                streaming=True,
                show_label=False,
                width=480, 
                height=280, 
                elem_classes=["image-container"]
            )
            
            webcam_timer = gr.Timer(0.1)
        
        with gr.Column(scale=1, elem_classes=["card"]):
            gr.HTML("<h3 style='color: #333; text-align: center; margin-bottom: 10px;'> AI Chat</h3>")
            
            chatbot = gr.Chatbot(
                label="AI Conversation",
                height=320, 
                show_label=False,
                type="messages",
                elem_classes=["chatbot"]
            )
            
            with gr.Row():
                chat_toggle_btn = gr.Button("Start Chat", variant="primary", size="sm")
                clear_btn = gr.Button("Clear", variant="secondary", size="sm")
            
            gr.HTML("""
                <div style="background: linear-gradient(45deg, rgba(102,126,234,0.1), rgba(78,205,196,0.1)); 
                            border-radius: 12px; padding: 12px; margin-top: 15px;">
                    <h4 style="color: #333; margin-bottom: 8px; text-align: center; font-size: 1em;">🎯 Features</h4>
                    <div class="features-grid">
                        <div class="feature-item"> Voice Recognition</div>
                        <div class="feature-item"> AI Responses</div>
                        <div class="feature-item"> Voice Synthesis</div>
                        <div class="feature-item"> Live Video</div>
                    </div>
                </div>
            """)

    gr.HTML("""
        <div style="text-align: center; padding: 10px; color: rgba(255, 255, 255, 0.8); font-size: 0.8em;">
            <p>Powered by Advanced AI Technology</p>
        </div>
    """)
    
    def enhanced_start_webcam():
        result = start_webcam()
        if result[0] is not None:
            status_html = """<div class="status-indicator status-active">Camera: Online</div>"""
        else:
            status_html = """<div class="status-indicator status-inactive">Camera: Error</div>"""
        return result[0], result[1], status_html
    
    def enhanced_stop_webcam():
        result = stop_webcam()
        status_html = """<div class="status-indicator status-inactive">📷 Camera: Offline</div>"""
        return result[0], result[1], status_html
    
    def enhanced_chat_toggle():
        global chat_active
        result = start_chat()
        
        if chat_active:
            status_html = """<div class="status-indicator status-active">Voice Chat: Active</div>"""
        else:
            status_html = """<div class="status-indicator status-inactive">Voice Chat: Offline</div>"""
        
        return result[0], status_html
    
    # Bind events
    start_btn.click(
        fn=enhanced_start_webcam,
        outputs=[webcam_output, start_btn, camera_status]
    )
    
    stop_btn.click(
        fn=enhanced_stop_webcam,
        outputs=[webcam_output, start_btn, camera_status]
    )
    
    webcam_timer.tick(
        fn=get_webcam_frame,
        outputs=webcam_output,
        show_progress=False
    )
    
    chat_toggle_btn.click(
        fn=enhanced_chat_toggle,
        outputs=[chat_toggle_btn, chat_status]
    )
    
    chat_toggle_btn.click(
        fn=process_audio_and_chat,
        outputs=chatbot,
        show_progress=True
    )
    
    clear_btn.click(
        fn=lambda: [],
        outputs=chatbot
    )

# Launch configuration
if __name__ == "__main__":
    print("Starting LUCY AI Assistant...")
    print("Laptop-optimized UI with compact design")
    print("Server starting on port 7860")
    print("Make sure your microphone is working")
    print("Camera will try different indices if default fails")
    
    demo.queue(max_size=10)
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=True,
        debug=True,
        show_error=True
    )