import streamlit as st
import subprocess
import tempfile
import os
from datetime import datetime
from streamlit_ace import st_ace
import uuid
import ollama  # Importing ollama package to interact with local Llama model
import ast
import re
import streamlit as st
import subprocess
import tempfile
import os
from datetime import datetime
from streamlit_ace import st_ace
import uuid
import ast
def install_packages(code):
    # Parse the code to extract imported modules
    tree = ast.parse(code)
    imports = set()

    # Find import statements
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            imports.add(node.module)

    # Prepare the install commands using pip
    for package in imports:
        try:
            subprocess.run(["pip", "install", package], check=True)
        except subprocess.CalledProcessError:
            st.error(f"Failed to install package: {package}")


# Function to extract Python code from model response
def extract_code_from_response(response_text):
    """Extract Python code (between triple backticks) from the model response,
    handling multiple triple backticks within the response."""
    start_token = "```"
    end_token = "```"

    try:
        # Use a regular expression to find all code blocks between triple backticks
        # The regex looks for text between sets of triple backticks.
        code_blocks = []
        pattern = r'```(.*?)```'
        
        # We handle cases where multiple code blocks exist
        matches = re.finditer(pattern, response_text, re.DOTALL)
        
        # Loop through all matches and extract the code
        for match in matches:
            code_block = match.group(1).strip()  # Strip any leading/trailing whitespace
            code_blocks.append(code_block)
        
        # If no code blocks found, return a message
        if not code_blocks:
            return "No Python code found in the response."
        
        # Return the list of code blocks as a string with newlines
        return "\n\n".join(code_blocks)  # Join all code blocks with a double newline
        
    except Exception as e:
        return f"Error extracting code: {str(e)}"
    

# Function to get response from the Ollama model
def get_ollama_response(messages):
    response = ollama.chat(model="llama2", messages=messages)
    return response.get('message', {}).get('content', 'No response from the model.')

# Set page layout
st.set_page_config(layout="wide")

# Title of the page
st.title("Python Code Compiler")

# Custom CSS to enhance the theme and layout
st.markdown("""
    <style>
        body {
            background-color: #f4f7fc;
            font-family: 'Arial', sans-serif;
            color: #333;
        }
        .stTextArea>div>div>textarea {
            font-family: 'Courier New', monospace;
        }
        .stButton>button {
            background-color: #007BFF;
            color: white;
            font-size: 16px;
            border-radius: 8px;
            padding: 10px 20px;
        }
        .stButton>button:hover {
            background-color: #0056b3;
        }
        .stSelectbox, .stSlider {
            width: 100%;
        }
        .stTextArea textarea {
            background-color: #f0f0f0;
            border: 1px solid #ccc;
            border-radius: 5px;
            padding: 10px;
        }
        .stTextArea textarea:focus {
            border-color: #007BFF;
            background-color: #fff;
        }
        .stRadio, .stSelectbox, .stSlider {
            margin-top: 20px;
        }
        .stMarkdown, .stSubheader {
            margin-top: 20px;
        }
        .stFileUploader, .stButton {
            margin-top: 20px;
        }
    </style>
""", unsafe_allow_html=True)

# Add a brief description at the top explaining the website functionality
st.markdown("""
    **Welcome to the Python Compiler!**
    - **Write Python Code** - **Upload Files** - **Run Code** - **Interact with Ollama**
""")

# Create 3 columns (Right for Chat, Left for Code Editor, Rest for Output and File Upload)
col1, col2, col3 = st.columns([2, 5, 2])  # Right for chat, left for code editor, rest for output and file upload

# Initialize session states
if "messages" not in st.session_state:
    st.session_state.messages = []

if "llama_response" not in st.session_state:
    st.session_state.llama_response = ""

if "extracted_code" not in st.session_state:
    st.session_state.extracted_code = ""

if "model_code" not in st.session_state:
    st.session_state.model_code = ""

# Left Column (Input Data and File Uploads)
with col1:
    # Input for stdin
    st.subheader("📥 Input Data for Script (stdin)")
    stdin_data = st.text_area("Provide input data:", height=150, placeholder="Input data for the code...")
   

    # Initialize session state for session_dir if it doesn't exist
    if "session_dir" not in st.session_state:
        st.session_state["session_dir"] = tempfile.mkdtemp()  # Create a temporary directory for session files

    # File upload section
    uploaded_files = st.file_uploader(
        "📂 Upload Files for Your Code (accessible via their paths)",
        accept_multiple_files=True,
    )

    uploaded_files_dict = {}

    # Save uploaded files with unique names in the session directory
    if uploaded_files:
        st.subheader("📁 Uploaded Files")
        for uploaded_file in uploaded_files:
            unique_name = f"{uuid.uuid4()}_{uploaded_file.name}"
            file_path = os.path.join(st.session_state["session_dir"], unique_name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            uploaded_files_dict[uploaded_file.name] = file_path

            # Display file details
            st.markdown(f"**File Name:** `{uploaded_file.name}`")
            st.markdown(f"**Server Path:** `{file_path}`")
    else:
        st.info("No files uploaded yet.")

# Left Column (Code Editor and Output)
with col2:
    st.subheader("✍️ Write Your Python Code")
    
    # Button to extract content from the Ollama model and insert it into the editor
    if st.button("💬 Get Code from Ollama"):
        st.session_state["code"] = st.session_state.extracted_code
        st.session_state.extracted_code = extract_code_from_response(st.session_state.llama_response)

        #st.session_state.extracted_code = extracted_code  # Insert extracted code into the editor
        st.success("📝 Code extracted from Ollama and inserted into the editor.")
        # Code editor widget
    initial_code = st.session_state.get("extracted_code", "")
    
    # Create a row for theme, font size, and editor height in one line
    theme_col, font_col, height_col = st.columns([3, 2, 2])  # Adjusting column width to align properly

    with theme_col:
        theme = st.selectbox(
            "🎨 Select Theme",
            ["monokai", "dracula", "solarized_light", "github", "xcode", "tomorrow_night"]
        )

    with font_col:
        font_size = st.selectbox("🔠 Select Font Size", [10, 12, 14, 16, 18, 20, 24, 28, 36],index=4 )

    with height_col:
        editor_height = st.selectbox("📏 Select Editor Height", [200, 400, 600, 800],index=1)

    print(st.session_state.extracted_code)
    code = st_ace(
        value=st.session_state.extracted_code,  # Show the extracted code
        language="python",  # Set language as Python for syntax highlighting
        theme=theme,  # Theme selected by the user
        font_size=font_size,  # Font size selected by the user
        height=editor_height,  # User-defined height
        auto_update=True,  # Automatically update value when editing
        #key="code",  # Key to store this widget in session state
        placeholder=st.session_state.extracted_code
    )
    # Store the modified code in session state
    st.session_state["code"] = code
            
    # Run Code button
    if st.button("▶️ Run Code"):
        code = st.session_state.get("code", "")
        if not code.strip():
            st.error("❌ No code provided! Please write some Python code.")
        else:
            # Save the code to a temporary file
            with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w") as temp_file:
                temp_file.write(code)
                temp_file_name = temp_file.name
            install_packages(code)
            try:
                # Running the Python code directly
                result = subprocess.run(
                    ["python", temp_file_name],
                    input=stdin_data,
                    capture_output=True,
                    text=True,
                    timeout=10,
                )

                # Display the results
                st.subheader("📊 Execution Output")
                st.text_area("Output", result.stdout, height=200)
                if result.stderr:
                    st.text_area("⚠️ Errors", result.stderr, height=200)

                # Log the execution
                if "execution_log" not in st.session_state:
                    st.session_state.execution_log = []

                st.session_state.execution_log.append({
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "code": code,
                    "output": result.stdout,
                    "error": result.stderr,
                    "stdin": stdin_data,
                })

            except subprocess.TimeoutExpired:
                st.error("❌ Execution timed out. Ensure your code doesn't contain infinite loops.")
            except Exception as e:
                st.error(f"❌ An unexpected error occurred: {e}")
            finally:
                # Cleanup the temporary code file
                if os.path.exists(temp_file_name):
                    os.remove(temp_file_name)


    # Optionally, display the code below the editor
    st.write("## 📝 Model code:")
    st.code(st.session_state.extracted_code, language="python")
    # Optionally, display the code below the editor
    st.write("## 📑 Model Response:")
    st.text_area(st.session_state.llama_response )



# Right Column (Chatbox for user input and Ollama model interaction)
with col3:
    st.subheader("🤖 Chat with Ollama")
    
    # Get input from the user to chat with Ollama model
    user_message = st.text_area("Write a message to Ollama", height=100, placeholder="Ask for code or assistance...")

    if st.button("💬 Send to Ollama"):
        if user_message:
            # Add user message to the session messages list
            st.session_state.messages.append({"role": "user", "content": user_message})

            # Get the response from Ollama model
            response_text = get_ollama_response(st.session_state.messages)
            #response_text = "```\nprint(\"fck\")\n```"
            st.session_state.llama_response = response_text
             
            # Extract any Python code from the response
            extracted_code = extract_code_from_response(response_text)
        
            st.session_state.extracted_code =extracted_code

            # Optionally, store extracted code in the editor
            st.session_state.extracted_code = extracted_code
        else:
            st.warning("❗ Please enter a message for Ollama to process.")

    # Display Ollama's response
    st.subheader("📑 Ollama's Response")
    st.text_area("Llama Model Response", st.session_state.llama_response, height=400)




# Display execution history in a collapsible section
if "execution_log" in st.session_state and st.session_state.execution_log:
    st.subheader("📜 Execution History")
    for log in st.session_state.execution_log[-5:]:  # Display the last 5 executions
        st.markdown(f"**🕒 Time:** {log['time']}")
        st.markdown("**📋 Code:**")
        st.code(log["code"], language="python")
        if log["stdin"]:
            st.markdown("**📥 Input Data (stdin):**")
            st.code(log["stdin"], language="python")
        st.markdown("**📝 Output:**")
        st.code(log["output"], language="python")
        if log["error"]:
            st.markdown("**⚠️ Errors:**")
            st.code(log["error"], language="python")
