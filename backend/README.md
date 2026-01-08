# BYTE Backend

## Setup

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Environment Variables**:
    Ensure `.env` contains:
    ```
    GOOGLE_API_KEY=...
    # other keys if needed
    ```

3.  **Run Server**:
    ```bash
    python backend/server.py
    ```
    The server will start at `http://0.0.0.0:8000`.

## API Endpoints

-   `POST /auth/signup`: Create account.
-   `POST /auth/login`: Get Access Token.
-   `POST /chat`: Chat with the agent (Requires Bearer Token).
