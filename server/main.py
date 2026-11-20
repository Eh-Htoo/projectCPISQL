from flask import Flask, jsonify
from flask_cors import CORS

app = Flask (__name__)
cors = CORS(app, origins="http://localhost:5173", supports_credentials=True)

@app.route("/api/users", methods = ['GET'])
def users():
    return jsonify(
        {
            "users": [
                'poe',
                'Joe',
                'jessie'
            ]
        }

    )


if __name__ == "__main__":
    app.run(debug = True, port = 8080)


