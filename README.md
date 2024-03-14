# Mortgage Eligibility Detector

This Flask application leverages mortgage data to assess an individual's eligibility for home purchase approval based on key financial indicators: Front-End Debt-to-Income Ratio (FEDTI), Debt-to-Income Ratio (DTI), Loan-to-Value Ratio (LTV), and credit rating. Additionally, it incorporates a chatbot powered by OpenAI GPT-3.5, designed to provide insights and answers to queries related to the Fannie Mae Eligibility Matrix, making it an invaluable tool for both potential homebuyers and financial advisors.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

Before you begin, ensure you have the following installed:
- Python 3.8 or higher
- pip (Python package installer)

### Installation

Follow these steps to set up your development environment:

1. Clone the repository to your local machine:
    ```
    git clone https://github.com/Pistonamey/team_eda.git
    ```
2. Navigate to the project directory:
    ```
    cd team_eda
    ```
3. Install the required Python packages:
    ```
    pip install -r requirements.txt
    ```
4. Set up the environment variables:
    - Duplicate the `.env.example` file and rename it to `.env`.
    - Fill in the variables in `.env` with your OpenAI API key and any other necessary configurations.

5. Run the Flask application:
    ```
    flask run
    ```

## Usage

After starting the application, navigate to `http://localhost:5000` in your web browser. You'll be greeted with a simple interface where you can:

- Input your mortgage data (FEDTI, DTI, LTV, and credit rating) to check your eligibility for a home purchase.
- Use the chatbot feature to ask questions related to the Fannie Mae Eligibility Matrix. The chatbot, powered by OpenAI GPT-3.5, is trained to provide informative responses to a wide range of queries.

