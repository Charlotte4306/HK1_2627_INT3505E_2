from pathlib import Path

import connexion

app = connexion.FlaskApp(__name__, specification_dir=str(Path(__file__).parent))
app.add_api("openapi.yaml", validate_responses=True, strict_validation=True)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5002)
