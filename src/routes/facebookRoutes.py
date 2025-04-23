import requests
from flask import Blueprint, request, jsonify

facebook_bp = Blueprint("facebook_bp", __name__)

PAGE_ID = "610526602144458"
ACCESS_TOKEN = "EAAeViquVBsUBOwItaoRUzqW1g3BoVxutk1XZAA8ArIOa3kWakYf8uEBgpVKfm5251KlaZAJNuOHyD1VAlJfZBCByyDDOfBy9g1Kxo60cpqhlsm339cceFBvyTyjYNSxlFbvT4VxBCAANJYoGQttKqhXcOreKgDSMvT5k40xUdGP0xBvwHiWk2wESCyUkZCkNcd4dgFe2SMcQJX8ZAY0au50npa2M6tE5skZBn3GzhmnK8ZD"

@facebook_bp.route("/publicar-facebook", methods=["POST"])
def publicar_facebook():
    titulo = request.form.get("titulo")
    contenido = request.form.get("contenido")
    file = request.files.get("rutimg")
    mensaje = f"{titulo}\n\n{contenido}"

    try:
        if file and file.filename != "":
            files = {
                "source": (file.filename, file.stream, file.mimetype)
            }
            data = {
                "caption": mensaje,
                "access_token": ACCESS_TOKEN,
                "published": "true"
            }
            url = f"https://graph.facebook.com/{PAGE_ID}/photos"
            response = requests.post(url, data=data, files=files)
        else:
            url = f"https://graph.facebook.com/{PAGE_ID}/feed"
            data = {
                "message": mensaje,
                "access_token": ACCESS_TOKEN
            }
            response = requests.post(url, data=data)

        response.raise_for_status()
        return jsonify({"msg": "Publicación enviada correctamente"}), 200

    except Exception as e:
        print("Error al publicar:", e)
        return jsonify({"error": str(e)}), 500


@facebook_bp.route("/get-facebook-metrics", methods=["GET"])
def get_facebook_metrics():
    posts_url = f"https://graph.facebook.com/v19.0/{PAGE_ID}/posts"
    posts_params = {
        "fields": "id,message,created_time",
        "access_token": ACCESS_TOKEN
    }

    try:
        response = requests.get(posts_url, params=posts_params)
        response.raise_for_status()
        posts = response.json().get("data", [])

        resultados = []

        for post in posts:
            post_id = post.get("id")

            if "message" not in post:
                print(f"Saltando publicación sin mensaje: {post_id}")
                continue

            print(f"\n🔍 Consultando métricas de: {post_id}")

            metrics_url = f"https://graph.facebook.com/v19.0/{post_id}"
            metrics_params = {
                "fields": "reactions.summary(true),comments.summary(true),shares",
                "access_token": ACCESS_TOKEN
            }

            try:
                metrics_res = requests.get(metrics_url, params=metrics_params)
                metrics_res.raise_for_status()
                metrics_data = metrics_res.json()

                reacciones = metrics_data.get("reactions", {}).get("summary", {}).get("total_count", 0)
                comentarios = metrics_data.get("comments", {}).get("summary", {}).get("total_count", 0)
                compartidos = metrics_data.get("shares", {}).get("count", 0)

                resultados.append({
                    "id": post_id,
                    "fecha": post.get("created_time"),
                    "mensaje": post.get("message"),
                    "reacciones": reacciones,
                    "comentarios": comentarios,
                    "compartidos": compartidos
                })

            except Exception as e:
                print(f"Error obteniendo métricas para {post_id}: {e}")
                continue

        return jsonify(resultados), 200

    except Exception as e:
        print("Error al consultar Facebook:", e)
        return jsonify({"error": str(e)}), 500
