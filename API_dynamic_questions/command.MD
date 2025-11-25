This folder focus on **Dynamic Question Generation API**

It will:
- Generates follow-up questions tailored to a user's initial responses (persona).
- Implemented as a Flask API leveraging a Large Language Model (LLM) for question creativity.

It follows a sequential flow:
1. **Initial Survey Input**: User provides answers to a set of base questions (interest, background).
2. **Dynamic Question API**: The base questions answers are fed to the Flask API (`API_dynamic_questions/app.py`), which uses an LLM to generate dynamic questions to capture nuanced skills and expectations. #

## Set up & Installation
### Prerequisites

You will need an **OpenAI API Key** to run the Dynamic Questions API.

Visit https://platform.openai.com/api-keys to get your key.

Create a file named `.env` in the root directory and securely store your key (e.g., OPENAI_API_KEY=YOUR_KEY_HERE).

### Running the Project **Dynamic Questions Generation API**
This Flask application uses the OpenAI API to generate dynamic questions based on the user's initial responses, capturing their persona, skills, and expectations.

- Run the API Server
```bash
python API_dynamic_questions/app.py
```
The server will start on http://localhost:7070

- Test the API (Recommended Method): Use the provided test script
```bash
python API_dynamic_questions/test_request.py
```

> Note: Change `sample_1.json` to any file in the `base_questions` folder to test different initial inputs. Don't forget to also change the `OUTPUT_FILENAME` accordingly.
