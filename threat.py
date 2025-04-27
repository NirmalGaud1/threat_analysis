import streamlit as st
import google.generativeai as genai
import requests
import json
from PIL import Image
import io

# Configuration
GENAI_API_KEY = "AIzaSyA-9-lTQTWdNM43YdOXMQwGKDy0SrMwo6c"  # Replace with yours
GOOGLE_API_KEY = "AIzaSyAClKl7by7FZqBLjlwNiVpuOY1oWw9ZoCA"  # Replace with yours

genai.configure(api_key=GENAI_API_KEY)
gemini_model = genai.GenerativeModel('gemini-2.5-flash')

def google_search(query, search_type="text", num=5):
    """Performs a Google Search."""
    base_url = "https://www.googleapis.com/customsearch/v1" # Using the same endpoint but without CSE ID
    params = {
        "q": query,
        "key": GOOGLE_API_KEY,
        "num": num,
    }
    if search_type == "image":
        params["searchType"] = "image"
        params["imgSize"] = "medium"
    response = requests.get(base_url, params=params)
    response.raise_for_status()  # Raise an exception for HTTP errors
    return response.json()

def analyze_person(query, is_image=False):
    """Search for person information using Google Search API."""
    try:
        if is_image:
            # Reverse image search
            search_results = google_search(query, search_type="image")
        else:
            # Text search focusing on social media
            search_results = google_search(f"{query} site:linkedin.com OR site:facebook.com OR site:twitter.com", num=5)

        if 'items' in search_results:
            return {
                "summary": gemini_model.generate_content(f"Summarize these search results about {query}: {json.dumps(search_results['items'][:3])}").text,
                "links": [item['link'] for item in search_results['items'][:5]]
            }
        return {"error": "No results found"}
    except requests.exceptions.RequestException as e:
        return {"error": f"Google Search API request failed: {e}"}
    except json.JSONDecodeError:
        return {"error": "Failed to decode Google Search API response."}
    except Exception as e:
        return {"error": str(e)}

def main():
    st.set_page_config(page_title="Person Threat Analyzer", layout="wide")

    st.title("🔍 Person Threat Analysis System")
    st.markdown("Analyze social media profiles and public information")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Input")
        input_type = st.radio("Search Type", ["Name", "Image", "Profile URL"])

        query = None
        if input_type == "Name":
            query = st.text_input("Enter Full Name", placeholder="John Doe")
        elif input_type == "Image":
            uploaded_file = st.file_uploader("Upload Profile Picture", type=["jpg", "png"])
            if uploaded_file:
                query = Image.open(uploaded_file)
                st.image(query, width=200)
        elif input_type == "Profile URL":
            query = st.text_input("Enter Social Media Profile URL")

    with col2:
        st.subheader("Analysis")

        if st.button("Search"):
            if not query:
                st.warning("Please provide input")
                return

            with st.spinner("Searching databases..."):
                # Person search
                is_image = isinstance(query, Image.Image)
                results = analyze_person(query, is_image=is_image)

                if "error" in results:
                    st.error(f"Search error: {results['error']}")
                else:
                    st.success("✅ Profile Information Found")

                    with st.expander("📄 Summary"):
                        st.write(results['summary'])

                    with st.expander("🌐 Related Links"):
                        for link in results['links']:
                            st.markdown(f"- [{link}]({link})")

                    # Threat analysis
                    with st.expander("⚠️ Threat Assessment"):
                        threat_report = gemini_model.generate_content(
                            f"Analyze this person's digital footprint for potential threats: {results['summary']}"
                            "Consider these factors:\n"
                            "- Criminal history\n"
                            "- Violent rhetoric\n"
                            "- Weapon ownership signs\n"
                            "- Mental health indicators\n"
                            "- Group affiliations\n\n"
                            "Respond in this format:\n"
                            "Risk Level: Low/Medium/High\n"
                            "Key Concerns: bullet points\n"
                            "Recommendations: bullet points"
                        ).text
                        st.write(threat_report)

    st.markdown("""
    ---
    **Disclaimer:** This system uses public data only. Results may be inaccurate.
    Never make real decisions based on this analysis. Always verify through official channels.
    """)

if __name__ == "__main__":
    main()
