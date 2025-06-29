import os
import time
import logging
import threading
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import dotenv_values
import platform

class SpeechRecognitionSystem:
    def __init__(self):
        self.driver = None
        self.html_path = None
        self.input_language = "en-US"
        self.lock = threading.Lock()
        self.shutdown_flag = threading.Event()
        self.recognition_active = False
        self.setup_logging()
        self.load_config()
        self.setup_working_directory()
        self.setup_html_file()
        self.setup_driver()

    def setup_logging(self):
        """Configure logging system"""
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join("Data", "speech_recognition.log")),
                logging.StreamHandler()
            ]
        )
        logging.getLogger('selenium').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('webdriver_manager').setLevel(logging.WARNING)
        logging.info("System initialized")

    def load_config(self):
        """Load configuration from .env file"""
        try:
            env_vars = dotenv_values(".env")
            if isinstance(env_vars, dict):
                self.input_language = env_vars.get("InputLanguage", "en-US")
                logging.info(f"Loaded InputLanguage: {self.input_language}")
            else:
                logging.warning("Invalid .env file format. Using defaults.")
        except Exception as e:
            logging.warning(f"Failed to load .env file: {e}. Using defaults.")

    def setup_working_directory(self):
        """Ensure all required directories exist"""
        try:
            os.makedirs("Data", exist_ok=True)
            os.makedirs("Frontend/Files", exist_ok=True)
            logging.info("Working directories set up")
        except Exception as e:
            logging.error(f"Failed to create directories: {e}")
            raise

    def setup_html_file(self):
        """Create HTML interface for voice recognition"""
        html_content = f"""<!DOCTYPE html>
        <html lang="en">
        <head>
            <title>Voice Control</title>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; text-align: center; margin-top: 50px; }}
                button {{ padding: 12px 24px; margin: 10px; cursor: pointer; font-size: 16px; }}
                #status {{ color: #666; margin: 20px; }}
                #output {{ 
                    min-height: 60px; 
                    border: 1px solid #ddd; 
                    padding: 15px; 
                    margin: 20px auto; 
                    max-width: 500px;
                    border-radius: 5px;
                }}
                #error {{ color: #d9534f; }}
                .container {{ max-width: 800px; margin: 0 auto; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Voice Recognition System</h2>
                <button id="start" class="btn-start">Start Listening</button>
                <button id="end" class="btn-stop">Stop</button>
                <p id="status">Status: Ready</p>
                <div id="output"></div>
                <p id="error"></p>
            </div>
            <script>
                const output = document.getElementById('output');
                const errorDisplay = document.getElementById('error');
                const statusDisplay = document.getElementById('status');
                let recognition;
                let isRunning = false;
                let audioContext;

                async function initAudio() {{
                    try {{
                        audioContext = new (window.AudioContext || window.webkitAudioContext)();
                        await audioContext.resume();
                        return true;
                    }} catch (error) {{
                        errorDisplay.textContent = 'Audio initialization failed: ' + error.message;
                        return false;
                    }}
                }}

                document.getElementById('start').addEventListener('click', async () => {{
                    if (isRunning) return;
                    
                    if (!await initAudio()) return;
                    
                    try {{
                        statusDisplay.textContent = "Status: Requesting microphone...";
                        const stream = await navigator.mediaDevices.getUserMedia({{ audio: true }});
                        
                        statusDisplay.textContent = "Status: Initializing...";
                        recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
                        recognition.lang = '{self.input_language}';
                        recognition.continuous = true;
                        recognition.interimResults = true;
                        isRunning = true;
                        errorDisplay.textContent = '';

                        recognition.onstart = () => {{
                            statusDisplay.textContent = "Status: Listening...";
                            document.getElementById('start').disabled = true;
                            document.getElementById('end').disabled = false;
                        }};

                        recognition.onresult = (event) => {{
                            let final = '';
                            let interim = '';
                            for (let i = event.resultIndex; i < event.results.length; i++) {{
                                const transcript = event.results[i][0].transcript;
                                if (event.results[i].isFinal) {{
                                    final += transcript;
                                }} else {{
                                    interim += transcript;
                                }}
                            }}
                            output.innerHTML = `<strong>${{final}}</strong><span style="color:#888">${{interim}}</span>`;
                        }};

                        recognition.onerror = (event) => {{
                            const errorsToIgnore = ['no-speech', 'audio-capture'];
                            if (errorsToIgnore.includes(event.error)) {{
                                statusDisplay.textContent = "Status: Waiting for speech...";
                                setTimeout(() => recognition.start(), 1000);
                            }} else {{
                                errorDisplay.textContent = 'Error: ' + event.error;
                                stopRecognition();
                            }}
                        }};

                        recognition.onend = () => {{
                            if (isRunning) recognition.start();
                        }};

                        recognition.start();
                    }} catch (error) {{
                        errorDisplay.textContent = 'Error: ' + error.message;
                        statusDisplay.textContent = "Status: Failed";
                        isRunning = false;
                    }}
                }});

                function stopRecognition() {{
                    if (recognition && isRunning) {{
                        isRunning = false;
                        recognition.onend = null;
                        recognition.stop();
                        output.textContent = '';
                        statusDisplay.textContent = "Status: Ready";
                        document.getElementById('start').disabled = false;
                        document.getElementById('end').disabled = true;
                        
                        if (audioContext) {{
                            audioContext.close().catch(e => console.log(e));
                        }}
                    }}
                }}

                document.getElementById('end').addEventListener('click', stopRecognition);
            </script>
        </body>
        </html>"""

        self.html_path = os.path.abspath(os.path.join("Data", "Voice.html"))
        try:
            with open(self.html_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            logging.info(f"HTML interface created at {self.html_path}")
        except Exception as e:
            logging.error(f"Failed to create HTML file: {e}")
            raise

    def setup_driver(self):
        """Configure Chrome WebDriver with optimal settings"""
        if self.driver:
            self.cleanup_driver()

        chrome_options = Options()
        chrome_options.add_argument("--use-fake-ui-for-media-stream")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_argument("--disable-renderer-backgrounding")
        chrome_options.add_argument("--disable-background-timer-throttling")
        chrome_options.add_argument("--disable-extensions")
        
        try:
            service = Service(
                ChromeDriverManager().install(),
                service_args=["--verbose", "--log-path=" + os.path.devnull]
            )
            self.driver = webdriver.Chrome(
                service=service,
                options=chrome_options
            )
            self.driver.set_page_load_timeout(20)
            self.driver.set_script_timeout(20)
            logging.info("WebDriver initialized successfully")
        except Exception as e:
            logging.error(f"WebDriver init failed: {e}")
            self.cleanup()
            raise

    def cleanup_driver(self):
        """Properly cleanup WebDriver resources"""
        try:
            if self.driver:
                if self.recognition_active:
                    try:
                        self.driver.find_element(By.ID, "end").click()
                        time.sleep(1)
                    except:
                        pass
                self.driver.quit()
                self.driver = None
                self.recognition_active = False
                logging.info("WebDriver successfully terminated")
        except Exception as e:
            logging.error(f"Driver cleanup error: {e}")

    def process_text(self, text):
        """Clean and format recognized text"""
        if not text or not text.strip():
            return ""
            
        text = text.strip()
        
        error_phrases = ["error:", "aborted", "not allowed", "could not"]
        if any(phrase in text.lower() for phrase in error_phrases):
            return ""
            
        if len(text.split()) < 2:
            return ""
            
        if text[-1] not in ['.', '?', '!']:
            question_words = ["how", "what", "when", "why", "who", "where", "can you"]
            if any(text.lower().startswith(word) for word in question_words):
                text += "?"
            else:
                text += "."
                
        return text.capitalize()

    def speech_recognition(self, timeout=30):
        """Perform voice recognition with stable WebDriver session"""
        try:
            if not self.driver or not self.is_driver_alive():
                self.setup_driver()

            file_url = f"file://{self.html_path}"
            
            with self.lock:
                if self.shutdown_flag.is_set():
                    return ""
                    
                self.driver.get(file_url)
                WebDriverWait(self.driver, 10).until(
                    lambda d: d.execute_script('return document.readyState') == 'complete'
                )
                
                start_button = WebDriverWait(self.driver, 15).until(
                    EC.element_to_be_clickable((By.ID, "start"))
                )
                start_button.click()
                self.recognition_active = True

            start_time = time.time()
            last_text = ""
            valid_text_detected = False

            while not self.shutdown_flag.is_set() and time.time() - start_time < timeout:
                try:
                    with self.lock:
                        if not self.driver:
                            break
                            
                        status = self.driver.find_element(By.ID, "status").text
                        if "Listening" not in status:
                            break
                            
                        current_text = self.process_text(
                            self.driver.find_element(By.ID, "output").text
                        )
                        
                        if current_text and current_text != last_text:
                            logging.info(f"Detected: {current_text}")
                            last_text = current_text
                            
                            if len(current_text.split()) >= 2:
                                valid_text_detected = True
                                break

                    time.sleep(1)

                except Exception as e:
                    logging.warning(f"Polling error: {e}")
                    break

            with self.lock:
                if self.driver and self.recognition_active:
                    try:
                        self.driver.find_element(By.ID, "end").click()
                        time.sleep(0.5)
                    except:
                        pass
                    finally:
                        self.recognition_active = False

            return last_text if valid_text_detected else ""

        except Exception as e:
            logging.error(f"Recognition session failed: {e}")
            return ""

    def is_driver_alive(self):
        """Check if WebDriver is still responsive"""
        try:
            if self.driver:
                self.driver.title
                return True
        except:
            return False
        return False

    def run(self):
        """Main execution loop"""
        try:
            while not self.shutdown_flag.is_set():
                print("\nReady for voice input (Ctrl+C to exit)...")
                result = self.speech_recognition()
                
                if result:
                    print(f"\nRecognized command: {result}")
                    
                time.sleep(0.5)
                
        except KeyboardInterrupt:
            print("\nShutting down voice service")
            self.shutdown_flag.set()