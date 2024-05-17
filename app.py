from flask import Flask, render_template, jsonify, request
import shopify
import os
import re
from llama_index.core import Settings
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.callbacks import CallbackManager
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core import PromptTemplate

app = Flask(__name__)

os.environ['GOOGLE_API_KEY'] = "AIzaSyD8MuvEtPT6C7SwRjMxDJK8wEhfAj6zTk0"



safety_settings = [
  {
    "category": "HARM_CATEGORY_HARASSMENT",
    "threshold": "BLOCK_NONE"
  },
  {
    "category": "HARM_CATEGORY_HATE_SPEECH",
    "threshold": "BLOCK_NONE"
  },
  {
    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
    "threshold": "BLOCK_NONE"
  },
  {
    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
    "threshold": "BLOCK_NONE"
  },
]
generation_config = {
  "temperature": 0.4,
  "top_p": 0.7,
  "top_k": 50,
  "max_output_tokens": 8192,
}

llm = Gemini(model_types="gemini-1.5-Pro", generation_config = generation_config,
                  safety_settings=safety_settings, device = 'cuda', device_map='cuda')
Settings.llm=llm

model_name = "nomic-ai/nomic-embed-text-v1"
embed_model = HuggingFaceEmbedding(model_name=model_name, trust_remote_code=True, device='cuda')
Settings.embed_model = embed_model

template = (
    "I have provided context information below.\n"
    "---------------------\n"
    "{context_str}"
    "\n---------------------\n"
    "**You are conversational AI.**\n"
    "*Response Format*: Bullet points with key-value pairs and product name as `Title`.\n"
    '''**Sample Response Format*: 
        - Title: The Institutes
        - Author: CALVIN JOHN
        - Category: Religious Studies.\n'''
    "Use only the provided context, no external knowledge allowed. {query_str}\n"
)

llm_prompt = PromptTemplate(template)

# Load documents and build index
documents = SimpleDirectoryReader("data").load_data()
index = VectorStoreIndex.from_documents(documents)

query_engine = index.as_query_engine(text_qa_template=llm_prompt, similarity_top_k=15)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_bot_response', methods=['POST'])
def get_bot_response():
    # Get the user query from the request
    user_query = request.json.get('query')

    if user_query is None:
        return jsonify({'bot_response': 'No query provided.'}), 400

    # Use the user query to get product information
    try:
        product_info = query_product_info(user_query)
        # Generate a bot response based on the product information
        bot_response = generate_bot_response(product_info)
        # Return the bot response
        return jsonify({'bot_response': bot_response})
    except Exception as e:
        return jsonify({'bot_response': f'Error: {str(e)}'}), 500

def query_product_info(prompt):

    # shop_url = 'https://shopingai.myshopify.com/'
    # admin_api_key = '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'
    # api_version = "2023-10"  # Specify a valid API version
    shop_url = 'https://boatai.myshopify.com/'
    admin_api_key = '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'
    api_version= "2023-10"

    # Create and activate a new session
    session = shopify.Session(shop_url, api_version, admin_api_key)
    shopify.ShopifyResource.activate_session(session)
    response = query_engine.query(prompt)
    response = response.response
    print("Resonse:\n", response)

    # Regular expression pattern to match titles
    pattern = r'Title: (.*)'
    # Find all matches of the pattern
    product_titles = re.findall(pattern, response)

    # Dictionary to store images with titles
    product_images = {}

    # Fetch images for each title
    for title in product_titles:
        print("Title", title)
        # Find products with the given title
        products = shopify.Product.find(title=title)

        # If products are found, store their images
        if products:
            for product in products:
                # Accessing the first image's src for each product
                image_src = product.images[0].src if product.images else None
                product_url = f"{shop_url}/products/{product.handle}"
                if image_src:
                    # Store the image URL with the title
                    product_images[title] = {"product_url": product_url, "image_src": image_src}
                    break  # Only store the first image for each title
                else:
                    print("No image found for product:", product.title)
        else:
            print("No products found with the title:", title)

    return product_images


def generate_bot_response(product_info):
    # Generate a response based on the product information
    response = ""

    # Check if product information is available
    if product_info:
        response += "<div class = 'message-final'>"
        response += "<h3>Here are some products I found:</h3>"
        response += "<ul style='list-style-type: none; padding: 0;'>"

        # Iterate through the product information and format the response
        for product, info in product_info.items():
            product_url = info.get('product_url', 'Not available')
            image_src = info.get('image_src', 'Not available')

            response += "<li style='margin-bottom: 20px;'>"
            response += f"<h4>{product}</h4>"
            response += f"<a href='{product_url}' target='_blank'><img src='{image_src}' alt='{product}' style='max-width: 200px;'></a>"
            response += f"<p><strong>Product URL:</strong> <a href='{product_url}' target='_blank'>{product_url}</a></p>"
            response += "</li>"
        
        response += "</ul>"
        response += "</div>"
    else:
        response += "I couldn't find any products related to your query."

    return response


if __name__ == "__main__":
    app.run(debug=True)
