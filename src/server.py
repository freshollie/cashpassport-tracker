import uuid

from flask import Flask, request, jsonify
from api import CashpassportApi

token_to_api = {}

app = Flask(__name__)

DEV = True

@app.route("/login", methods=["POST"])
def login():
    data = request.form

    error = ""
    if "user" not in data:
        error = "Must specify username"
    elif "pass" not in data:
        error = "Must specify password"
    elif "message" not in data:
        error = "Must specify secret message"
    elif "answer" not in data:
        error = "Must specify secret answer"
    elif "zone" not in data:
        error = "Must specify timezone"

    if error:
        return jsonify({"error": error})

    user_id = data["user"]
    password = data["pass"]
    message = data["message"]
    answer = data["answer"]
    time_zone = data["zone"]

    user_api = CashpassportApi(user_id, password, message, answer, time_zone)

    response = user_api.login()

    error = ""

    if response == CashpassportApi.ERROR_BAD_USER_ID:
        error = "Invalid user"
    elif response == CashpassportApi.ERROR_BAD_PASSWORD:
        error = "Invalid password"
    elif response == CashpassportApi.ERROR_BAD_SECURITY_MESSAGE:
        error = "Bad security message found for user"
    elif response == CashpassportApi.ERROR_BAD_SECURITY_ANSWER:
        error = "Invalid security answer"
    elif response == CashpassportApi.CONNECTION_ERROR:
        error = "Connection error"

    if error:
        return jsonify({"success": False, "error": error, "code": response})

    token = uuid.uuid4().hex

    if DEV:
        token = "1"

    token_to_api[token] = user_api

    return jsonify({"success": True, "token": token})

@app.route("/get-balance")
def get_balance():
    token = request.args.get("token")

    if not token or token not in token_to_api:
        return jsonify({"error": "invalid token", "code": 20})

    user_api = token_to_api[token]

    if not user_api.is_logged_in():
        user_api.login()

    balance = user_api.get_balance()

    if balance == CashpassportApi.ERROR_LOGGED_OUT:
        del token_to_api[token]
        return jsonify({"error": "invalid token", "code": 20})

    return jsonify({"balance": balance})

@app.route("/get-transactions")
def get_transactions():
    token = request.args.get("token")
    from_ts = request.args.get("from")

    if not token or token not in token_to_api:
        return jsonify({"error": "invalid token", "code": 20})

    user_api = token_to_api[token]

    if not user_api.is_logged_in():
        user_api.login()

    if not from_ts:
        from_ts = 0

    transactions = user_api.get_transactions(from_ts=from_ts)

    if transactions == CashpassportApi.ERROR_LOGGED_OUT:
        del token_to_api[token]
        return jsonify({"error": "invalid token", "code": 20})

    return jsonify({"transactions": transactions.as_simple()})

if __name__ == "__main__":
    app.run(debug=True, threaded=True)