import os
import boto3
from flask import Flask, jsonify, request
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.ext.flask.middleware import XRayMiddleware

app = Flask(__name__)

# ------------------ X-RAY ------------------
xray_recorder.configure(service="course-service")
XRayMiddleware(app, xray_recorder)

# ------------------ CONFIG ------------------
REGION = os.environ.get("AWS_REGION", "ap-south-2")

# DynamoDB (IRSA handles authentication)
dynamodb = boto3.resource("dynamodb", region_name=REGION)
courses_table = dynamodb.Table("noorcourse")


# ------------------ HEALTH ------------------
@app.route("/noor student/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": "course-service"
    }), 200


# ------------------ CREATE COURSE ------------------
@app.route("/noor student/courses", methods=["POST"])
def create_course():
    try:
        data = request.get_json()

        code = data.get("code")
        title = data.get("title")
        description = data.get("description")

        if not code or not title:
            return jsonify({
                "error": "code and title are required"
            }), 400

        courses_table.put_item(
            Item={
                "code": code,
                "title": title,
                "description": description
            }
        )

        return jsonify({
            "message": "Course created successfully",
            "course": {
                "code": code,
                "title": title,
                "description": description
            }
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ------------------ GET ONE COURSE ------------------
@app.route("/noor student/courses/<course_code>", methods=["GET"])
def get_course(course_code):
    try:
        resp = courses_table.get_item(Key={"code": course_code})
        item = resp.get("Item")

        if not item:
            return jsonify({"error": "Course not found"}), 404

        return jsonify(item), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ------------------ GET ALL COURSES ------------------
@app.route("/courses", methods=["GET"])
def list_courses():
    try:
        resp = courses_table.scan(Limit=50)
        return jsonify(resp.get("Items", [])), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ------------------ UPDATE COURSE ------------------
@app.route("/courses/<course_code>", methods=["PUT"])
def update_course(course_code):
    try:
        data = request.get_json()

        title = data.get("title")
        description = data.get("description")

        if not title:
            return jsonify({
                "error": "title is required"
            }), 400

        courses_table.update_item(
            Key={"code": course_code},
            UpdateExpression="SET title = :t, description = :d",
            ExpressionAttributeValues={
                ":t": title,
                ":d": description
            },
            ReturnValues="UPDATED_NEW"
        )

        return jsonify({
            "message": "Course updated successfully",
            "code": course_code,
            "title": title,
            "description": description
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ------------------ DELETE COURSE ------------------
@app.route("/courses/<course_code>", methods=["DELETE"])
def delete_course(course_code):
    try:
        courses_table.delete_item(Key={"code": course_code})

        return jsonify({
            "message": "Course deleted successfully",
            "code": course_code
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ------------------ MAIN ------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3001, debug=False)
    x