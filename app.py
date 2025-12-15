import os
import time
import sqlite3
import smtplib
from email.message import EmailMessage
from functools import wraps
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from flask import (
    Flask, render_template, request, redirect, session, url_for, flash, jsonify
)
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

from db import Database

# ============================================================
# CONFIG
# ============================================================
app = Flask(__name__)
app.secret_key = "supersecretkey"  # cámbialo en producción

# Uploads
UPLOAD_FOLDER = os.path.join(app.root_path, "static", "uploads")
COURSE_IMG_FOLDER = os.path.join(app.root_path, "static", "img")
PROFILE_IMG_FOLDER = os.path.join(app.root_path, "static", "profiles")

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["COURSE_IMG_FOLDER"] = COURSE_IMG_FOLDER
app.config["PROFILE_IMG_FOLDER"] = PROFILE_IMG_FOLDER

# Email config (ajusta si quieres SMTP real)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587

app.config['MAIL_USERNAME'] = 'brawlc370@gmail.com'
app.config['MAIL_PASSWORD'] = 'dwgm kpqf eqpf djli'  # contraseña de aplicación

app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False

# 👇 Esta línea hace que NO aparezca “brawlc370”
app.config['MAIL_DEFAULT_SENDER'] = ('mljAcademy', 'brawlc370@gmail.com')



# ============================================================
# DB
# ============================================================
db = Database()

# ============================================================
# UTIL: serializer para tokens
# ============================================================
def get_serializer():
    return URLSafeTimedSerializer(app.secret_key)

def generar_token(email):
    s = get_serializer()
    return s.dumps(email, salt='recuperar-contrasena-salt')

def verificar_token(token, max_age_seconds=3600):
    s = get_serializer()
    try:
        email = s.loads(token, salt='recuperar-contrasena-salt', max_age=max_age_seconds)
        return email
    except (SignatureExpired, BadSignature):
        return None

def enviar_email_reset(destino_email, link_reset):
    server = app.config.get('MAIL_SERVER')
    # Fallback a consola si no configurado
    if not server or server == 'smtp.example.com':
        print("=== Enlace de recuperación (DEBUG - no SMTP configurado) ===")
        print(link_reset)
        print("===========================================================")
        return True

    try:
        msg = EmailMessage()
        msg['Subject'] = 'Recuperar contraseña - mljAcademy'
        msg['From'] = app.config['MAIL_USERNAME']
        msg['To'] = destino_email
        msg.set_content(
            f"Hola,\n\nRecibimos una solicitud para restablecer tu contraseña. "
            f"Usa este enlace (válido 1 hora):\n\n{link_reset}\n\n"
            "Si no lo pediste, ignora este correo.\n\nSaludos,\nmljAcademy"
        )

        smtp = smtplib.SMTP(app.config['MAIL_SERVER'], app.config['MAIL_PORT'])
        if app.config.get('MAIL_USE_TLS'):
            smtp.starttls()
        smtp.login(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
        smtp.send_message(msg)
        smtp.quit()
        return True
    except Exception as e:
        print("Error enviando correo:", e)
        return False

# ============================================================
# PROTECCIONES
# ============================================================
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
      
            return redirect("/login")
        return f(*args, **kwargs)
    return wrapper

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        # Ahora revisa "usuario_id" en lugar de "user_id"
        if "usuario_id" not in session or session.get("rol") != "admin":
            if request.method == 'GET':
                flash("Acceso denegado. Se requiere ser administrador.")
                return redirect(url_for('home'))  # Redirige al inicio
            return jsonify({"error": "Acceso denegado. Se requiere ser administrador."}), 403
        return f(*args, **kwargs)
    return wrapper

# ============================================================
# FORMAT YOUTUBE (helper)
# ============================================================
def format_youtube_url(url: str | None) -> str | None:
    if not url:
        return None
    url = url.strip()
    if "youtube.com/embed/" in url:
        return url
    if "youtube.com/watch" in url and "v=" in url:
        video_id = url.split("v=")[1].split("&")[0]
        return f"https://www.youtube.com/embed/{video_id}"
    if "youtu.be/" in url:
        video_id = url.split("youtu.be/")[1].split("?")[0]
        return f"https://www.youtube.com/embed/{video_id}"
    return url

# ============================================================
# CONTEXT PROCESSOR
# ============================================================
@app.context_processor
def inject_db():
    return dict(db=db)

# ============================================================
# RUTAS PÚBLICAS
# ============================================================
@app.route("/")
def home():
    return render_template("home.html")

@app.route('/sobre')
def sobre_nosotros():
    return render_template('sobre_nosotros.html')

@app.route('/ubicacion')
def ubicacion():
    return render_template('ubicacion.html')

@app.route("/perfil", methods=["GET", "POST"])
def perfil():
    # SOLO usuarios logueados
    if "user_id" not in session:
        return redirect("/login")

    # Conexión DB
    conn = db.connect_usuarios()
    cur = conn.cursor()

    # Cargar datos actuales
    cur.execute("SELECT id, nombre, correo, profile_img FROM usuarios WHERE id = ?", (session["user_id"],))
    usuario = cur.fetchone()

    if request.method == "POST":

        # FOTO
        if "foto" in request.files:
            foto = request.files["foto"]
            if foto.filename != "":
                filename = secure_filename(foto.filename)
                ruta = os.path.join("static/img/perfiles", filename)
                foto.save(ruta)

                cur.execute("UPDATE usuarios SET profile_img = ? WHERE id = ?", (filename, session["user_id"]))
                conn.commit()

                session["foto_perfil"] = filename
                session["profile_img"] = filename

        # NOMBRE
        nuevo_nombre = request.form.get("nombre")
        if nuevo_nombre:
            cur.execute("UPDATE usuarios SET nombre = ? WHERE id = ?", (nuevo_nombre, session["user_id"]))
            conn.commit()
            session["nombre"] = nuevo_nombre

        # CORREO
        nuevo_email = request.form.get("email")
        if nuevo_email:
            cur.execute("UPDATE usuarios SET correo = ? WHERE id = ?", (nuevo_email, session["user_id"]))
            conn.commit()
            session["correo"] = nuevo_email

    conn.close()
    return render_template("perfil.html", usuario=usuario)





# ============================================================
# LOGIN / REGISTRO / LOGOUT
# ============================================================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        correo = request.form.get("correo")
        contraseña = request.form.get("contraseña")
        user = db.verificar_login(correo, contraseña)
        if user:
            # soporta sqlite3.Row y tuplas
            uid = user["id"] if hasattr(user, "keys") else user[0]
            uname = user["nombre"] if hasattr(user, "keys") else user[1]
            ucorreo = user["correo"] if hasattr(user, "keys") else user[2]
            urol = user["rol"] if hasattr(user, "keys") else user[4]
            # perfil en DB: intentamos detectar campo profile_img o profile
            uprofile = None
            if hasattr(user, "keys"):
                if "profile_img" in user.keys():
                    uprofile = user["profile_img"]
                elif "foto" in user.keys():
                    uprofile = user["foto"]
            else:
                # si es tupla y está en la posición 5 (como antes)
                if user and len(user) > 5:
                    uprofile = user[5]

            # guardar en session (nombres compatibles con templates que usas)
        session["usuario_id"] = uid          # ID del usuario
        session["nombre"] = uname            # Nombre completo
        session["nombre_usuario"] = uname    # Nombre de usuario para mostrar
        session["correo"] = ucorreo          # Email
        session["rol"] = urol                # Debe ser "admin" o "usuario"
        session["foto_perfil"] = uprofile if uprofile else "perfil.png"

        return redirect("/")
    else:
            flash("Correo o contraseña incorrectos")
    return render_template("login.html")

@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        nombre = request.form.get("nombre")
        correo = request.form.get("correo")
        contraseña = request.form.get("contraseña")
        creado = db.registrar_usuario(nombre, correo, contraseña)
        if creado:
            flash("Cuenta creada correctamente. Inicia sesión.")
            return redirect("/login")
        else:
            flash("El correo ya está registrado")
    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ============================================================
# RECUPERAR / RESET PASSWORD
# ============================================================
@app.route("/recuperar", methods=["GET", "POST"])
def recuperar():
    if request.method == "POST":
        correo = request.form.get("correo")
        if not correo:
            flash("Introduce un correo válido")
            return redirect(url_for("recuperar"))

        user = db.obtener_usuario_por_correo(correo)
        # Mensaje genérico para no filtrar usuarios
        flash("Si el correo existe, recibirás un email con instrucciones.")
        if not user:
            return redirect(url_for("login"))

        token = generar_token(correo)
        link = url_for("reset_password", token=token, _external=True)
        enviado = enviar_email_reset(correo, link)
        if not enviado:
            flash("Error al enviar el email. Intenta más tarde.")
            return redirect(url_for("recuperar"))
        return redirect(url_for("login"))

    return render_template("recuperar_contrasena.html")


@app.route("/reset/<token>", methods=["GET", "POST"])
def reset_password(token):
    correo = verificar_token(token, max_age_seconds=3600)
    if not correo:
        flash("Token inválido o expirado. Solicita otro enlace.")
        return redirect(url_for("recuperar"))

    user = db.obtener_usuario_por_correo(correo)
    if not user:
        flash("Usuario no encontrado.")
        return redirect(url_for("recuperar"))

    if request.method == "POST":
        nueva = request.form.get("contraseña")
        nueva2 = request.form.get("contraseña2")
        if not nueva or nueva != nueva2:
            flash("Las contraseñas no coinciden o están vacías.")
            return redirect(url_for("reset_password", token=token))

        nueva_hash = generate_password_hash(nueva)
        db.actualizar_contrasena(user["id"] if hasattr(user, "keys") else user[0], nueva_hash)
        flash("Contraseña actualizada. Ya puedes iniciar sesión.")
        return redirect(url_for("login"))

    return render_template("reset_password.html", correo=correo)

# ============================================================
# ADMIN: CRUD CURSOS
# ============================================================
@app.route("/admin/cursos")
@admin_required
def gestion_cursos():
    # Aquí va la lógica para listar o gestionar cursos
    return render_template("admin_cursos.html")




@app.route("/admin/cursos/agregar", methods=["GET", "POST"])
@admin_required
def admin_cursos_agregar():
    if request.method == "POST":
        titulo = request.form["titulo"]
        descripcion = request.form["descripcion"]
        categoria = request.form.get("categoria", "")
        duracion = request.form.get("duracion", "")

        imagen = request.files.get("imagen")
        ruta_img = "curso.png"

        if imagen and imagen.filename != "":
            timestamp = int(time.time())
            filename = f"{timestamp}_{secure_filename(imagen.filename)}"
            ruta_img = filename 
            # GUARDAR IMAGEN DE CURSO EN static/img
            imagen.save(os.path.join(app.config["COURSE_IMG_FOLDER"], filename))

        db.agregar_curso(titulo, descripcion, categoria, duracion, ruta_img)

        flash("Curso agregado correctamente")
        return redirect("/admin/cursos")

    return render_template("admin_cursos_agregar.html")


@app.route("/admin/cursos/editar/<int:id>", methods=["GET", "POST"])
@admin_required
def admin_cursos_editar(id):
    curso = db.obtener_curso(id)

    if request.method == "POST":
        titulo = request.form["titulo"]
        descripcion = request.form["descripcion"]
        categoria = request.form.get("categoria", "")
        duracion = request.form.get("duracion", "")

        imagen = request.files.get("imagen")
        
        ruta_img = curso["imagen"] if hasattr(curso, 'keys') and "imagen" in curso.keys() else (curso[5] if curso and len(curso) > 5 else "curso.png")

        if imagen and imagen.filename != "":
            timestamp = int(time.time())
            filename = f"{timestamp}_{secure_filename(imagen.filename)}"
            ruta_img = filename
            # GUARDAR IMAGEN DE CURSO EN static/img
            imagen.save(os.path.join(app.config["COURSE_IMG_FOLDER"], filename))

        db.editar_curso(id, titulo, descripcion, categoria, duracion, ruta_img)
        flash("Curso actualizado")
        return redirect("/admin/cursos")

    return render_template("admin_cursos_editar.html", curso=curso)


@app.route("/admin/cursos/borrar/<int:id>")
@admin_required
def admin_cursos_borrar(id):
    db.borrar_curso(id)
    flash("Curso eliminado")
    return redirect("/admin/cursos")

# ============================================================
# PUBLIC VIEWS: cursos/lecciones/examenes
# ============================================================
@app.route("/cursos")
def lista_cursos_publica():
    cursos = db.obtener_cursos()
    return render_template("cursos.html", cursos=cursos)

@app.route("/cursos/<int:curso_id>")
def ver_curso_publico(curso_id):
    curso = db.obtener_curso(curso_id)
    niveles = db.obtener_niveles(curso_id)
    if not curso:
        return "Curso no encontrado"
    lecciones_por_nivel = {}
    for nivel in niveles:
        nivel_id = nivel["id"] if hasattr(nivel, "keys") else nivel[0]
        lecciones_por_nivel[nivel_id] = db.obtener_lecciones(nivel_id)
    return render_template("curso_detalle.html", curso=curso, niveles=niveles, lecciones_por_nivel=lecciones_por_nivel)

@app.route("/leccion/<int:leccion_id>")
def ver_leccion(leccion_id):
    leccion = db.obtener_leccion(leccion_id)
    if not leccion:
        return "Lección no encontrada"
    nivel_id = leccion["nivel_id"] if hasattr(leccion, "keys") else leccion[1]
    curso_id = db.obtener_curso_de_nivel(nivel_id)
    curso = db.obtener_curso(curso_id)
    lecciones = db.obtener_lecciones(nivel_id)
    ids = [l["id"] if hasattr(l, "keys") else l[0] for l in lecciones]
    try:
        idx = ids.index(leccion_id)
        leccion_anterior = ids[idx - 1] if idx > 0 else None
        leccion_siguiente = ids[idx + 1] if idx < len(ids) - 1 else None
    except ValueError:
        leccion_anterior = None
        leccion_siguiente = None
    return render_template("leccion.html", leccion=leccion, curso=curso, curso_id=curso_id, leccion_anterior=leccion_anterior, leccion_siguiente=leccion_siguiente)

@app.route("/admin/examenes/agregar/<int:nivel_id>", methods=["GET", "POST"])
@admin_required
def admin_agregar_examen(nivel_id):
    if request.method == "POST":
        titulo = request.form.get("titulo")
        descripcion = request.form.get("descripcion", "")
        db.agregar_examen(nivel_id, titulo, descripcion)
        flash("Examen agregado correctamente")
        return redirect(f"/admin/niveles/{nivel_id}")
    return render_template("admin_examen_presentar.html", nivel_id=nivel_id)

@app.route("/admin/examenes/<int:examen_id>/preguntas", methods=["GET", "POST"])
@admin_required
def admin_examen_preguntas(examen_id):
    if request.method == "POST":
        texto = request.form.get("texto")
        respuesta = request.form.get("respuesta_correcta")
        db.agregar_pregunta(examen_id, texto, respuesta)
    preguntas = db.obtener_preguntas(examen_id)
    examen = db.obtener_examen(examen_id)
    return render_template("admin_examen_preguntas.html", examen=examen, preguntas=preguntas)

@app.route("/admin/examenes/eliminar/<int:examen_id>")
@admin_required
def admin_eliminar_examen(examen_id):
    examen = db.obtener_examen(examen_id)
    if examen:
        db.eliminar_examen(examen_id)
        flash("Examen eliminado")
        nivel_id = examen["nivel_id"] if hasattr(examen, "keys") and "nivel_id" in examen.keys() else examen[1]
        return redirect(f"/admin/niveles/{nivel_id}")
    return "Examen no encontrado"

@app.route("/examen/<int:examen_id>", methods=["GET"])
@login_required
def presentar_examen(examen_id):
    examen = db.obtener_examen(examen_id)
    preguntas = db.obtener_preguntas(examen_id)
    if not examen:
        return "Examen no encontrado"
    return render_template("examen_presentar.html", examen=examen, preguntas=preguntas)

@app.route("/examen/<int:examen_id>/resolver", methods=["POST"])
@login_required
def resolver_examen(examen_id):
    preguntas = db.obtener_preguntas(examen_id)
    total = len(preguntas)
    correctas = 0
    for p in preguntas:
        pregunta_id = p["id"] if hasattr(p, "keys") else p[0]
        correcta = p["correcta"] if hasattr(p, "keys") else p[3]
        respuesta = request.form.get(str(pregunta_id))
        es_correcta = 1 if respuesta == correcta else 0
        if es_correcta:
            correctas += 1
        db.guardar_respuesta(session["user_id"], examen_id, pregunta_id, respuesta, es_correcta)
    nota = round((correctas / total) * 10, 2) if total > 0 else 0.0
    aprobado = nota >= 7
    return render_template("examen_resultado.html", nota=nota, correcto=correctas, total=total, aprobado=aprobado)

# ============================================================
# ADMIN USERS
# ============================================================
@app.route("/admin/usuarios")
@admin_required
def admin_usuarios():
    usuarios = db.obtener_todos_usuarios()
    return render_template("admin_usuarios.html", usuarios=usuarios)

@app.route("/admin/usuarios/rol/<int:id>/<rol>")
@admin_required
def cambiar_rol(id, rol):
    db.actualizar_rol(id, rol)
    return redirect("/admin/usuarios")

@app.route("/admin/usuarios/borrar/<int:id>")
@admin_required
def borrar_usuario(id):
    conn = db.connect_usuarios()
    c = conn.cursor()
    c.execute("DELETE FROM usuarios WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect("/admin/usuarios")

# ============================================================
# WIZARD / API ENDPOINTS
# ============================================================
@app.route("/api/cursos/crear", methods=["POST"])
@admin_required
def api_crear_curso():
    titulo = request.form.get('titulo')
    descripcion = request.form.get('descripcion', '')
    ruta_img = None
    if 'imagen' in request.files:
        file = request.files['imagen']
        if file and file.filename != "":
            timestamp = int(time.time())
            filename = f"{timestamp}_{secure_filename(file.filename)}"
            ruta_absoluta = os.path.join(app.config['COURSE_IMG_FOLDER'], filename)
            if not os.path.exists(app.config['COURSE_IMG_FOLDER']):
                os.makedirs(app.config['COURSE_IMG_FOLDER'])
            file.save(ruta_absoluta)
            ruta_img = filename
    try:
        curso_id = db.wizard_crear_curso(titulo, descripcion, ruta_img)
        if curso_id:
            return jsonify({'success': True, 'curso_id': curso_id}), 200
        else:
            return jsonify({'success': False, 'message': 'Error al crear curso en la DB.'}), 500
    except Exception as e:
        print(f"ERROR en api_crear_curso: {e}")
        return jsonify({'success': False, 'message': f'Error interno del servidor: {e}'}), 500

@app.route("/api/cursos/agregar_niveles", methods=["POST"])
@admin_required
def api_agregar_niveles():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No se recibió JSON válido"}), 400
        curso_id = int(data.get("curso_id", 0))
        niveles = data.get("niveles")
        if not isinstance(niveles, list):
            return jsonify({"error": "niveles debe ser una lista"}), 400
        curso = db.obtener_curso(curso_id)
        if not curso:
            return jsonify({"error": f"El curso {curso_id} no existe"}), 400
        nivel_ids = db.wizard_agregar_niveles(curso_id, niveles)
        if nivel_ids is None:
            return jsonify({"error": "Error al guardar niveles"}), 500
        return jsonify({"nivel_ids": nivel_ids, "status": "ok"})
    except Exception as e:
        import traceback as tb
        tb.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route("/api/cursos/agregar_leccion", methods=["POST"])
@admin_required
def api_agregar_leccion():
    nivel_id = request.form.get("nivel_id")
    titulo = request.form.get("titulo")
    contenido = request.form.get("contenido")
    video_url = request.form.get("video_url")
    pdf = request.files.get("pdf")
    video_url = format_youtube_url(video_url)
    pdf_filename = None
    if pdf and pdf.filename != "":
        timestamp = int(time.time())
        filename = f"{timestamp}_{secure_filename(pdf.filename)}"
        pdf_filename = filename
        if not os.path.exists(app.config["UPLOAD_FOLDER"]):
            os.makedirs(app.config["UPLOAD_FOLDER"])
        pdf.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
    leccion_id = db.wizard_agregar_leccion(nivel_id, titulo, contenido, video_url, pdf_filename)
    if leccion_id:
        return jsonify({"status": "ok", "leccion_id": leccion_id})
    else:
        return jsonify({"status": "error", "message": "No se pudo guardar la lección"}), 500

# ============================================================
# EJECUTAR APP
# ============================================================
if __name__ == "__main__":
    # asegurar carpetas
    for p in (app.config["UPLOAD_FOLDER"], app.config["COURSE_IMG_FOLDER"], app.config["PROFILE_IMG_FOLDER"]):
        if not os.path.exists(p):
            os.makedirs(p)
    app.run(debug=True)
