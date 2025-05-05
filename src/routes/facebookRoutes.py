import requests
from flask import Blueprint, request, jsonify, session
from datetime import timedelta

facebook_bp = Blueprint("facebook_bp", __name__)

# Configuración inicial vacía (pero realmente vendrá de session)
PAGE_ID = ""
ACCESS_TOKEN = ""

# Ruta para guardar configuración de Facebook
@facebook_bp.route('/guardar-configuracion', methods=['POST'])
def guardar_configuracion():
    data = request.get_json()
    session['page_id'] = data.get('page_id')
    session['access_token'] = data.get('access_token')
    session.permanent = True  # Hace que la sesión persista
    return jsonify({"msg": "Configuración guardada correctamente."}), 200

# Ruta para publicar en Facebook
@facebook_bp.route("/publicar-facebook", methods=["POST"])
def publicar_facebook():
    page_id = session.get('page_id')
    access_token = session.get('access_token')

    if not page_id or not access_token:
        return jsonify({"error": "No se ha configurado el PAGE_ID o ACCESS_TOKEN."}), 400

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
                "access_token": access_token,
                "published": "true"
            }
            url = f"https://graph.facebook.com/{page_id}/photos"
            response = requests.post(url, data=data, files=files)
        else:
            url = f"https://graph.facebook.com/{page_id}/feed"
            data = {
                "message": mensaje,
                "access_token": access_token
            }
            response = requests.post(url, data=data)

        response.raise_for_status()
        return jsonify({"msg": "Publicación enviada correctamente"}), 200

    except Exception as e:
        print("Error al publicar:", e)
        return jsonify({"error": str(e)}), 500

# Ruta para obtener métricas de Facebook
@facebook_bp.route("/get-facebook-metrics", methods=["GET"])
def get_facebook_metrics():
    page_id = session.get('page_id')
    access_token = session.get('access_token')

    if not page_id or not access_token:
        return jsonify({"error": "No se ha configurado el PAGE_ID o ACCESS_TOKEN."}), 400

    posts_url = f"https://graph.facebook.com/v19.0/{page_id}/posts"
    posts_params = {
        "fields": "id,message,created_time,full_picture",
        "access_token": access_token
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

            print(f"\nConsultando métricas de: {post_id}")

            metrics_url = f"https://graph.facebook.com/v19.0/{post_id}"
            metrics_params = {
                "fields": "reactions.summary(true),comments.summary(true),shares",
                "access_token": access_token
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
                    "imagen": post.get("full_picture", ""),
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

    
@facebook_bp.route("/get-post-details/<post_id>", methods=["GET"])
def get_post_details(post_id):
    page_id = session.get('page_id')
    access_token = session.get('access_token')

    if not page_id or not access_token:
        return jsonify({"error": "No se ha configurado el PAGE_ID o ACCESS_TOKEN."}), 400

    try:
        # Primero obtenemos todas las reacciones de la publicación
        reactions_url = f"https://graph.facebook.com/v19.0/{post_id}/reactions"
        reactions_params = {
            "summary": "true",
            "limit": 1000,
            "access_token": access_token
        }
        reactions_res = requests.get(reactions_url, params=reactions_params)
        reactions_res.raise_for_status()
        reactions_data = reactions_res.json().get("data", [])

        # Contadores individuales
        like = love = haha = wow = sad = angry = 0

        for reaction in reactions_data:
            tipo = reaction.get("type")
            if tipo == "LIKE":
                like += 1
            elif tipo == "LOVE":
                love += 1
            elif tipo == "HAHA":
                haha += 1
            elif tipo == "WOW":
                wow += 1
            elif tipo == "SAD":
                sad += 1
            elif tipo == "ANGRY":
                angry += 1

        # Ahora obtenemos comentarios y compartidos
        extra_url = f"https://graph.facebook.com/v19.0/{post_id}"
        extra_params = {
            "fields": "comments.summary(true),shares",
            "access_token": access_token
        }
        extra_res = requests.get(extra_url, params=extra_params)
        extra_res.raise_for_status()
        extra_data = extra_res.json()

        comentarios = extra_data.get("comments", {}).get("summary", {}).get("total_count", 0)
        compartidos = extra_data.get("shares", {}).get("count", 0)

        return jsonify({
            "like": like,
            "love": love,
            "haha": haha,
            "wow": wow,
            "sad": sad,
            "angry": angry,
            "comentarios": comentarios,
            "compartidos": compartidos
        }), 200

    except Exception as e:
        print(f"Error obteniendo detalles para {post_id}: {e}")
        return jsonify({"error": str(e)}), 500