a practice project that gives skincare recommendation

# Skincare Suggestion Web App

A Flask-based web application that provides personalized skincare product and diet recommendations based on user input and quiz results. Users can register, log in, take skin quizzes, view suggestions, search ingredients, and manage their profiles.

## Features
- User registration and login
- Skin quiz for personalized recommendations
- Product and diet suggestions
- Ingredient search hub
- Profile management and editing
- Privacy and about us pages

## Technologies Used
- Python 3.12
- Flask
- MySQL (Flask-MySQLdb)
- Jinja2 templates
- HTML/CSS (templates/static)

## Setup Instructions
1. Clone the repository:
	```bash
	git clone <repo-url>
	cd project_skincare
	```
2. Create and activate a Python virtual environment:
	```bash
	python3 -m venv skincare
	source skincare/bin/activate
	```
3. Install dependencies:
	```bash
	pip install -r requirements.txt
	```
4. Configure MySQL database settings in `app.py`:
	- Update `MYSQL_HOST`, `MYSQL_USER`, `MYSQL_PASSWORD`, and `MYSQL_DB` as needed.
5. Run the application:
	```bash
	python app.py
	```
6. Access the app at `http://localhost:5000`

## Project Structure
```
project_skincare/
├── app.py
├── insert_data.py
├── main_skincare.py
├── requirements.txt
├── static/
│   └── images/
├── templates/
│   └── *.html
├── tests/
│   └── testcase.py
├── skincare/
│   └── (virtual environment)
└── README.md
```

## Testing
Run unit tests using pytest:
```bash
pytest -v tests/testcase.py
```

## License
This project is for educational purposes.
