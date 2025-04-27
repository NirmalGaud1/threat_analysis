import streamlit as st
import google.generativeai as genai
import requests
import json
from PIL import Image

# Configuration (Remember to replace with your actual API key)
GENAI_API_KEY = "AIzaSyA-9-lTQTWdNM43YdOXMQwGKDy0SrMwo6c"
GOOGLE_API_KEY = "AIzaSyAClKl7by7FZqBLjlwNiVpuOY1oWw9ZoCA"
# You might consider using a Custom Search Engine ID for more targeted results
# GOOGLE_CSE_ID = "YOUR_CUSTOM_SEARCH_ENGINE_ID"

genai.configure(api_key=GENAI_API_KEY)
gemini_model = genai.GenerativeModel('gemini-1.5-flash')

def google_search(query, search_type="text", num=5):
    """Performs a Google Search."""
    base_url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "q": query,
        "key": GOOGLE_API_KEY,
        "num": num,
    }
    if search_type == "image":
        params["searchType"] = "image"
        params["imgSize"] = "medium"
        # If using CSE: params["cx"] = GOOGLE_CSE_ID
    else:
        params["q"] = f"{query} site:linkedin.com OR site:facebook.com OR site:twitter.com"
        # If using CSE: params["cx"] = GOOGLE_CSE_ID
    response = requests.get(base_url, params=params)
    response.raise_for_status()
    return response.json()

def analyze_input(query, input_type):
    """Analyze input using Google Search and Gemini."""
    try:
        if input_type == "Image":
            search_results = google_search(query, search_type="image")
        elif input_type == "URL":
            search_results = google_search(query, num=3) # Search the URL itself
        else: # input_type == "Name"
            search_results = google_search(query)

        if 'items' in search_results:
            search_summary = gemini_model.generate_content(
                f"Summarize these search results about '{query}': {json.dumps(search_results['items'][:3])}"
            ).text

            links = [item['link'] for item in search_results['items'][:5]]

            threat_analysis_prompt = f"""Based on this information: {search_summary} and these links: {links}
            Perform a risk assessment considering potential public information. Provide:
            1. Potential person identification.
            2. Background information.
            3. Public records summary (if any can be inferred).
            4. Risk assessment (Low/Medium/High and reasoning).
            5. Relevant fictional links (as bullet points for demonstration)."""

            analysis_response = gemini_model.generate_content(threat_analysis_prompt).text
            return f"{analysis_response}\n\n**Source Links:**\n" + "\n".join(links)
        else:
            return "No relevant search results found."

    except requests.exceptions.RequestException as e:
        return f"Search error: {e}"
    except json.JSONDecodeError:
        return "Error decoding search results."
    except Exception as e:
        return f"Analysis error: {str(e)}"

def main():
    st.set_page_config(page_title="Person Analyzer", layout="wide")

    st.title("🔍 Person Analysis System")
    st.markdown("Demonstration system using Gemini AI and Google Search API")
    st.markdown("**Warning:** This system attempts to retrieve real-time public data. Be mindful of ethical and legal implications.")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Input")
        input_type = st.radio("Input Type", ["Name", "Image", "URL"])

        query = None
        if input_type == "Name":
            query = st.text_input("Enter Name", placeholder="John Doe")
        elif input_type == "Image":
            uploaded_file = st.file_uploader("Upload Image", type=["jpg", "png"])
            if uploaded_file:
                query = Image.open(uploaded_file)
                st.image(query, width=200)
        elif input_type == "URL":
            query = st.text_input("Enter Profile URL")

    with col2:
        st.subheader("Analysis")

        if st.button("Analyze") and query:
            with st.spinner("Searching and Analyzing..."):
                results = analyze_input(query, input_type)
                st.subheader("Full Report")
                st.markdown(results)

    st.markdown("""
    ---
    **Disclaimer:** This system uses public data. Accuracy may vary.
    Be aware of ethical and legal implications when analyzing personal information.
    Never use for purposes that could infringe on privacy or cause harm.
    """)

if __name__ == "__main__":
    main()
