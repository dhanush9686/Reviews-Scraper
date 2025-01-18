from selenium import webdriver
from flask import Flask, request, render_template, jsonify
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import openai
from flask_cors import CORS
import os
import json
import re

app = Flask(__name__)
CORS(app)

def scrape_all_pages_and_count_reviews(url):
    all_html_pages = []
    total_reviews = 0

    options = webdriver.ChromeOptions()
    options.add_argument("--headless") 
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(options=options)
    driver.get(url)

    try:
        while True:
            # Get the HTML content of the current page
            html = driver.page_source
            all_html_pages.append(html)

            if total_reviews == 0:
                soup = BeautifulSoup(html, "html.parser")
                total_reviews_element = soup.find(string=lambda text: "Reviews" in text if text else False)
                if total_reviews_element:
                    matches = re.findall(r'\d+', total_reviews_element)
                    if matches:
                        total_reviews = int(matches[0])
            try:
                next_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//a[contains(text(),'Next') or contains(text(),'›')]"))
                )
                next_button.click()
                WebDriverWait(driver, 5).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
            except Exception:
                print("No more pages to navigate.")
                break

    except Exception as e:
        print(f"An error occurred during scraping: {e}")
    finally:
        driver.quit()

    return all_html_pages, total_reviews


def extract_review_sections(html_pages):
    """Extracts only review-related sections from all HTML pages."""
    review_sections = []

    for html in html_pages:
        soup = BeautifulSoup(html, "html.parser")
        reviews = soup.find_all(class_=lambda c: c and "review" in c.lower())
        for review in reviews:
            review_sections.append(str(review))

    if not review_sections:
        raise ValueError("No review sections found in the HTML pages.")

    return review_sections


def format_reviews_with_openai(review_sections):
    """Formats extracted review sections using OpenAI API."""
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OpenAI API key not found in environment variables.")

    openai.api_key = api_key
    formatted_reviews = []

    for section in review_sections:
        system_message = (
            "You are a text extraction assistant. Extract the following structured information from the review HTML: "
            "Reviewer Name, Review Title, Review Content, Review Date, Review Rating. "
            "Respond with the result as a JSON array. Example: "
            '[{"Reviewer Name": "John", "Review Title": "Great!", "Review Content": "I loved it", "Review Date": "2025-01-01", "Review Rating": 5}]'
        )
        user_message = f"Extract data from the following review HTML:\n\n{section}"

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "system", "content": system_message},
                          {"role": "user", "content": user_message}],
            )
            raw_response = response.choices[0].message["content"].strip()
            parsed_response = json.loads(raw_response)

            if isinstance(parsed_response, list):
                formatted_reviews.extend(parsed_response)
            else:
                print(f"Unexpected response format: {parsed_response}")

        except Exception as e:
            print(f"Error extracting review: {e}")

    return formatted_reviews


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/api/reviews', methods=['POST'])
def get_reviews():
    url = request.form.get('url')
    if not url:
        return jsonify({"error": "URL parameter is required"}), 400

    try:
        all_pages_html, total_reviews = scrape_all_pages_and_count_reviews(url)
        review_html_sections = extract_review_sections(all_pages_html)
        formatted_reviews = format_reviews_with_openai(review_html_sections)
        
        response_data = {
            "reviews_count": total_reviews,
            "reviews": [
                {
                    "title": review.get("Review Title", ""),
                    "body": review.get("Review Content", ""),
                    "rating": review.get("Review Rating", ""),
                    "reviewer": review.get("Reviewer Name", "")
                }
                for review in formatted_reviews if isinstance(review, dict)
            ]
        }

        return jsonify(response_data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
