
## Installation and Setup

1. **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2. **Create a virtual environment:**
    ```bash
    python -m venv venv
    ```

3. **Activate the virtual environment:**
    - On Windows:
      ```bash
      venv\Scripts\activate
      ```
    - On macOS/Linux:
      ```bash
      source venv/bin/activate
      ```

4. **Install the required packages:**
    ```bash
    pip install -r requirements.txt
    ```

5. **Set up your environment variables:**
    - Create a `.env` file in the project root and add the following:
      ```properties
      DB_HOST=localhost
      DB_USER=root
      DB_PASSWORD=
      DB_NAME=cv_ats
      ```

6. **Run the application:**
    ```bash
    flet run
    ```
