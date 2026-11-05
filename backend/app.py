import os
from flask import Flask, jsonify, request
from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions
from supabase_auth.errors import AuthApiError
from postgrest import APIError
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_PUBLISHABLE_KEY = os.environ.get("SUPABASE_PUBLISHABLE_KEY")

if not SUPABASE_URL or not SUPABASE_PUBLISHABLE_KEY:
    raise RuntimeError("SUPABASE_URL and SUPABASE_PUBLISHABLE_KEY must be configured")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY)


@app.errorhandler(APIError)
def handle_database_error(_error):
    return jsonify({"error": "Database request failed"}), 500


def authenticated_context():
    authorization = request.headers.get("Authorization", "")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None, None, (jsonify({"error": "Authentication required"}), 401)

    try:
        client = create_client(
            SUPABASE_URL,
            SUPABASE_PUBLISHABLE_KEY,
            options=ClientOptions(
                headers={"Authorization": f"Bearer {token}"},
                auto_refresh_token=False,
                persist_session=False,
            ),
        )
        user = client.auth.get_user(token).user
    except AuthApiError:
        return None, None, (jsonify({"error": "Invalid or expired access token"}), 401)
    except Exception:
        return None, None, (jsonify({"error": "Authentication service unavailable"}), 503)

    return client, user, None


@app.get("/")
def index():
    return jsonify({"service": "events-api"})


@app.get("/api/events")
def list_events():
    limit = min(max(request.args.get("limit", default=50, type=int), 1), 100)
    response = supabase.table("events").select("*").limit(limit).execute()
    return jsonify({"events": response.data})


@app.get("/api/events/<event_id>")
def get_event(event_id):
    response = (
        supabase.table("events")
        .select("*")
        .eq("id", event_id)
        .limit(1)
        .execute()
    )
    if not response.data:
        return jsonify({"error": "Event not found"}), 404
    return jsonify(response.data[0])


@app.post("/api/registrations")
def create_registration():
    client, user, error_response = authenticated_context()
    if error_response:
        return error_response

    payload = request.get_json(silent=True)
    event_id = payload.get("event_id") if isinstance(payload, dict) else None
    if not event_id:
        return jsonify({"error": "event_id is required"}), 400

    event_response = (
        client.table("events")
        .select("id")
        .eq("id", event_id)
        .limit(1)
        .execute()
    )
    if not event_response.data:
        return jsonify({"error": "Event not found"}), 404

    try:
        response = (
            client.table("registrations")
            .insert({"event_id": event_id, "user_id": user.id})
            .execute()
        )
    except APIError as error:
        if getattr(error, "code", None) == "23505":
            return jsonify({"error": "Already registered for this event"}), 409
        raise

    registration = response.data[0] if response.data else None
    return jsonify({"registration": registration}), 201


@app.get("/api/me/registrations")
def list_my_registrations():
    client, user, error_response = authenticated_context()
    if error_response:
        return error_response

    response = (
        client.table("registrations")
        .select("*")
        .eq("user_id", user.id)
        .limit(100)
        .execute()
    )
    return jsonify({"registrations": response.data})


@app.get("/api/events/<event_id>/registrations")
def list_event_registrations(event_id):
    client, user, error_response = authenticated_context()
    if error_response:
        return error_response

    event_response = (
        client.table("events")
        .select("organizer_id")
        .eq("id", event_id)
        .limit(1)
        .execute()
    )
    if not event_response.data:
        return jsonify({"error": "Event not found"}), 404
    if event_response.data[0].get("organizer_id") != user.id:
        return jsonify({"error": "Only the event organizer can view registrations"}), 403

    response = (
        client.table("registrations")
        .select("*")
        .eq("event_id", event_id)
        .limit(100)
        .execute()
    )
    return jsonify({"registrations": response.data})

if __name__ == '__main__':
    app.run(debug=True)