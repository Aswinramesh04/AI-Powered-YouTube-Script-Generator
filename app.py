import os
import json
import streamlit as st
import boto3
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)
from dotenv import load_dotenv

# Load environment variables from a .env file if present
load_dotenv()


# Constants for configuration
MODEL_ID = 'anthropic.claude-v2'  # Replace with the correct model ID if different
REGION_NAME = 'us-east-1'  # Replace with your AWS region
MAX_RETRIES = 6
MIN_WAIT = 1
MAX_WAIT = 60


def main():
    # Set page configuration
    st.set_page_config(
        page_title="Alwrity - AI-Powered YouTube Script Generator Using Claude v2 (Beta)",
        layout="wide",
    )

    # Custom CSS for styling
    st.markdown("""
        <style>
            /* Scrollbar Styling */
            ::-webkit-scrollbar-track {
                background: #e1ebf9;
            }

            ::-webkit-scrollbar-thumb {
                background-color: #90CAF9;
                border-radius: 10px;
                border: 3px solid #e1ebf9;
            }

            ::-webkit-scrollbar-thumb:hover {
                background: #64B5F6;
            }

            ::-webkit-scrollbar {
                width: 16px;
            }

            /* Button Styling */
            div.stButton > button:first-child {
                background: #1565C0;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                text-align: center;
                text-decoration: none;
                display: inline-block;
                font-size: 16px;
                margin: 10px 2px;
                cursor: pointer;
                transition: background-color 0.3s ease;
                box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.2);
                font-weight: bold;
            }

            div.stButton > button:first-child:hover {
                background-color: #0D47A1;
            }

            /* Hide Header and Footer */
            header {visibility: hidden;}
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
        </style>
    """, unsafe_allow_html=True)

    # Application Title and Description
    st.title("Alwrity - AI-Powered YouTube Script Generator Using Claude v2")
    st.markdown("Create engaging, high-converting YouTube scripts effortlessly with our AI-powered script generator. 🎬✨")

    # Input Fields within an Expander for Better UI
    with st.expander("**PRO-TIP** - Better input yield, better results. 📌", expanded=True):
        col1, space, col2 = st.columns([5, 0.1, 5])

        with col1:
            main_points = st.text_area(
                '**What is your video about? 🎥**',
                placeholder='Write a few lines on your video idea (e.g., "New trek, Latest in news, Finance, Tech...")',
                help="Describe the idea of the whole content in a single sentence. Keep it between 1-3 sentences."
            )
            tone_style = st.selectbox(
                '**Select Tone & Style 🎭**',
                ['Casual', 'Professional', 'Humorous', 'Formal', 'Informal', 'Inspirational'],
                help="Choose the tone and style that best fits your video."
            )
            target_audience = st.multiselect(
                '**Select Video Target Audience 🎯 (One or Multiple)**',
                [
                    'Beginners', 'Marketers', 'Gamers', 'Foodies', 'Entrepreneurs', 'Students',
                    'Parents', 'Tech Enthusiasts', 'General Audience', 'News article', 'Finance Article'
                ],
                help="Select one or more target audiences for your video."
            )

        with col2:
            video_length = st.selectbox(
                '**Select Video Length ⏰**',
                [
                    'Short (1-3 minutes)', 'Medium (3-5 minutes)',
                    'Long (5-10 minutes)', 'Very Long (10+ minutes)'
                ],
                help="Choose the desired length of your video."
            )
            language = st.selectbox(
                '**Select Language 🌐**',
                [
                    'English', 'Spanish', 'French', 'German', 'Chinese', 'Japanese', 'Other'
                ],
                help="Select the language for your video script."
            )
            if language == 'Other':
                custom_language = st.text_input(
                    '**Enter your preferred language**',
                    placeholder='e.g., Italian, Portuguese...',
                    help="Specify your preferred language if not listed above."
                )
                language = custom_language.strip() if custom_language.strip() else 'English'

            use_case = st.selectbox(
                '**YouTube Script Use Case 📚**',
                [
                    'Tutorials', 'Product Reviews', 'Explainer Videos', 'Vlogs', 'Motivational Speeches',
                    'Comedy Skits', 'Educational Content'
                ],
                help="Select the use case that best describes your video."
            )

    # Button to Generate Script
    if st.button('**Write YT Script 📝**'):
        with st.spinner("Assigning AI professional to write your YT script... ⏳"):
            # Input Validation
            if not main_points.strip():
                st.error("🚫 Please provide the main points about your video.")
            elif not target_audience:
                st.error("🚫 Please select at least one target audience.")
            else:
                response = generate_youtube_script(
                    target_audience,
                    main_points,
                    tone_style,
                    video_length,
                    use_case,
                    language
                )
                if response:
                    st.subheader('**🧕👩 Your Final YouTube Script! 📜**')
                    st.markdown(f"```\n{response}\n```")  # Using code block for better formatting
                    st.success("🎉 Script generated successfully!")
                else:
                    st.error("💥 Failed to write the script. Please try again!")


def generate_youtube_script(target_audience, main_points, tone_style, video_length, use_case, language):
    """
    Generate a YouTube script using Claude v2 via Amazon Bedrock.

    Args:
        target_audience (list): List of target audiences.
        main_points (str): Description of the video content.
        tone_style (str): Selected tone and style.
        video_length (str): Selected video length.
        use_case (str): Selected use case.
        language (str): Selected language.

    Returns:
        str: Generated YouTube script or None if failed.
    """
    # Construct the prompt for Claude v2
    prompt = f"""
    You are an expert scriptwriter. Please create a YouTube script in {language} for a video with the following details:

    **Video Topic:**
    {main_points}

    **Target Audience:**
    {', '.join(target_audience)}

    **Tone & Style:**
    {tone_style}

    **Video Length:**
    {video_length}

    **Use Case:**
    {use_case}

    **Instructions:**
    - Start with a strong hook to grab attention.
    - Structure the script with clear sections and headings.
    - Provide engaging introductions and conclusions for each section.
    - Use clear and concise language, avoiding jargon or overly technical terms.
    - Tailor the language and tone to the target audience.
    - Include relevant examples, anecdotes, and stories to make the video more engaging.
    - Add questions to encourage viewer interaction and participation.
    - End the script with a strong call to action, encouraging viewers to subscribe, like the video, or visit your website.

    **Output Format:**
    Please provide the script in a clear and easy-to-read format.
    Include clear headings for each section and ensure that all instructions are followed.
    """

    try:
        response = generate_text_with_claude(prompt)
        return response
    except Exception as err:
        st.error(f"🚫 An error occurred while generating the script: {err}")
        return None


@retry(wait=wait_random_exponential(min=MIN_WAIT, max=MAX_WAIT), stop=stop_after_attempt(MAX_RETRIES))
def generate_text_with_claude(prompt):
    """
    Generates text using Claude v2 via Amazon Bedrock with exception handling and retries.

    Args:
        prompt (str): The prompt for text generation.

    Returns:
        str: The generated text.
    """
    try:
        # Retrieve AWS credentials from environment variables
        aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
        aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        aws_session_token = os.getenv('AWS_SESSION_TOKEN')  # Optional, for temporary credentials

        if not aws_access_key_id or not aws_secret_access_key:
            raise ValueError("AWS credentials are not set in environment variables.")

        # Initialize the Bedrock client
        client = boto3.client(
            service_name='bedrock',
            region_name=REGION_NAME,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            aws_session_token=aws_session_token  # Optional
        )

        # Prepare the payload for the Claude model
        payload = {
            "prompt": prompt,
            "max_tokens": 3000,  # Adjust based on desired output length and model limits
            "temperature": 0.7,
            "top_p": 0.9,
            "stop_sequences": ["\n\n"],
        }

        # Invoke the Claude v2 model
        response = client.invoke_model(
            modelId=MODEL_ID,
            body=json.dumps(payload),
            contentType='application/json'
        )

        # Parse the response
        response_body = response['body'].read().decode('utf-8')
        response_json = json.loads(response_body)

        # Extract the generated text
        generated_text = response_json.get('generated_text', '').strip()

        if not generated_text:
            raise ValueError("No text was generated by the model.")

        return generated_text

    except Exception as e:
        st.error(f"⚠️ Error during text generation: {e}")
        raise e  # Re-raise exception to trigger retry


if __name__ == "__main__":
    main()
