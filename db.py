import sqlite3, os
from werkzeug.security import generate_password_hash, check_password_hash


class Database:

    # ============================================================
    #   CONSTRUCTOR
    # ============================================================
    def __init__(self):
       base_dir = os.path.abspath(os.path.dirname(__file__))
       instance_dir = os.path.join(base_dir, "instance")

       os.makedirs(instance_dir, exist_ok=True)
       self.db_usuarios = os.path.join(instance_dir, "usuarios.db")
       self.db_cursos = os.path.join(instance_dir, "cursos.db")
       self.crear_tablas_usuarios()
       self.crear_tablas_cursos()
       self.crear_admin_por_defecto()

    # ============================================================
    #   CONEXIONES
    # ============================================================
    def connect_usuarios(self):
        conn = sqlite3.connect(self.db_usuarios)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def connect_cursos(self):
        conn = sqlite3.connect(self.db_cursos)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    # ============================================================
    #   TABLAS USUARIOS
    # ============================================================
    def crear_tablas_usuarios(self):
        conn = self.connect_usuarios()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                correo TEXT UNIQUE NOT NULL,
                contrasena TEXT NOT NULL,
                rol TEXT DEFAULT 'alumno',
                profile_img TEXT DEFAULT 'perfil.png'
            )
        """)
        conn.commit()
        conn.close()

    # ============================================================
    #   TABLAS CURSOS
    # ============================================================
    def crear_tablas_cursos(self):
        conn = self.connect_cursos()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cursos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT NOT NULL,
                descripcion TEXT,
                imagen TEXT,
                categoria TEXT,
                duracion TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS niveles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                curso_id INTEGER,
                titulo TEXT,
                descripcion TEXT,
                FOREIGN KEY (curso_id) REFERENCES cursos(id) ON DELETE CASCADE
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lecciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nivel_id INTEGER,
                titulo TEXT,
                contenido TEXT,
                video_url TEXT,
                pdf_file TEXT,
                FOREIGN KEY (nivel_id) REFERENCES niveles(id) ON DELETE CASCADE
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS examenes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nivel_id INTEGER,
                titulo TEXT,
                descripcion TEXT,
                FOREIGN KEY (nivel_id) REFERENCES niveles(id) ON DELETE CASCADE
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS preguntas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                examen_id INTEGER,
                texto TEXT,
                correcta TEXT,
                FOREIGN KEY (examen_id) REFERENCES examenes(id) ON DELETE CASCADE
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS respuestas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER,
                examen_id INTEGER,
                pregunta_id INTEGER,
                respuesta_dada TEXT,
                es_correcta INTEGER,
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE CASCADE,
                FOREIGN KEY (examen_id) REFERENCES examenes(id) ON DELETE CASCADE,
                FOREIGN KEY (pregunta_id) REFERENCES preguntas(id) ON DELETE CASCADE
            )
        """)
        conn.commit()
        conn.close()

    # ============================================================
    #   ADMIN POR DEFECTO
    # ============================================================
    def crear_admin_por_defecto(self):
        conn = self.connect_usuarios()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE correo = 'admin@admin.com'")
        if not cursor.fetchone():
            contrasena_hash = generate_password_hash("admin123")
            cursor.execute("""
                INSERT INTO usuarios (nombre, correo, contrasena, rol, profile_img)
                VALUES (?, ?, ?, ?, ?)
            """, ("Administrador", "admin@admin.com", contrasena_hash, "admin", "perfil.png"))
            conn.commit()
        conn.close()

    # ============================================================
    #   REGISTRO Y LOGIN
    # ============================================================
    def registrar_usuario(self, nombre, correo, contrasena):
        conn = self.connect_usuarios()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM usuarios WHERE correo = ?", (correo,))
        if cursor.fetchone():
            conn.close()
            return False
        contrasena_hash = generate_password_hash(contrasena)
        try:
            cursor.execute("""
                INSERT INTO usuarios (nombre, correo, contrasena, rol)
                VALUES (?, ?, ?, ?)
            """, (nombre, correo, contrasena_hash, "alumno"))
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error al registrar usuario: {e}")
            return False
        finally:
            conn.close()

    def verificar_login(self, correo, contrasena):
        conn = self.connect_usuarios()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre, correo, contrasena, rol, profile_img FROM usuarios WHERE correo = ?", (correo,))
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            return None
        
        try:
            hash_guardado = user['contrasena']
        except (IndexError, KeyError):
            hash_guardado = user[3]
        
        if check_password_hash(hash_guardado, contrasena):
            return user
        return None
    def obtener_usuario_por_correo(self, correo):
        conn = self.connect_usuarios()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre, correo, contrasena, rol, profile_img FROM usuarios WHERE correo = ?", (correo,))
        user = cursor.fetchone()
        conn.close()
        return user

    def actualizar_contrasena(self, usuario_id, nueva_contrasena_hash):
        conn = self.connect_usuarios()
        cursor = conn.cursor()
        cursor.execute("UPDATE usuarios SET contrasena = ? WHERE id = ?", (nueva_contrasena_hash, usuario_id))
        conn.commit()
        conn.close()


    # ============================================================
    #   CRUD USUARIOS
    # ============================================================
    def obtener_todos_usuarios(self):
        conn = self.connect_usuarios()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre, correo, rol, profile_img FROM usuarios ORDER BY rol, nombre")
        usuarios = cursor.fetchall()
        conn.close()
        return usuarios

    def actualizar_rol(self, id, rol):
        conn = self.connect_usuarios()
        cursor = conn.cursor()
        cursor.execute("UPDATE usuarios SET rol = ? WHERE id = ?", (rol, id))
        conn.commit()
        conn.close()

    # ============================================================
    #   CRUD CURSOS
    # ============================================================
    def agregar_curso(self, titulo, descripcion, categoria, duracion, imagen):
        conn = self.connect_cursos()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO cursos (titulo, descripcion, categoria, duracion, imagen)
                VALUES (?, ?, ?, ?, ?)
            """, (titulo, descripcion, categoria, duracion, imagen))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"ERROR SQLite al crear curso: {e}")
            return None
        finally:
            conn.close()

    def editar_curso(self, id, titulo, descripcion, categoria, duracion, imagen):
        conn = self.connect_cursos()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE cursos SET titulo=?, descripcion=?, categoria=?, duracion=?, imagen=? WHERE id=?
        """, (titulo, descripcion, categoria, duracion, imagen, id))
        conn.commit()
        conn.close()

    def borrar_curso(self, id):
        conn = self.connect_cursos()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM cursos WHERE id = ?", (id,))
        conn.commit()
        conn.close()

    def obtener_cursos(self):
        conn = self.connect_cursos()
        cursor = conn.cursor()
        cursor.execute("SELECT id, titulo, descripcion, imagen, categoria, duracion FROM cursos")
        data = cursor.fetchall()
        conn.close()
        return data

    def obtener_curso(self, curso_id):
        """
        Devuelve el curso con columnas en orden fijo:
        0: id, 1: titulo, 2: descripcion, 3: imagen, 4: categoria, 5: duracion
        """
        conn = self.connect_cursos()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, titulo, descripcion, imagen, categoria, duracion
            FROM cursos
            WHERE id = ?
        """, (curso_id,))
        data = cursor.fetchone()
        conn.close()
        return data

    # ============================================================
    #   NIVELES
    # ============================================================
    def agregar_nivel(self, curso_id, titulo, descripcion):
        conn = self.connect_cursos()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO niveles (curso_id, titulo, descripcion)
                VALUES (?, ?, ?)
            """, (curso_id, titulo, descripcion))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"ERROR SQLite al agregar nivel: {e}")
            return None
        finally:
            conn.close()

    def obtener_nivel(self, nivel_id):
        conn = self.connect_cursos()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM niveles WHERE id = ?", (nivel_id,))
        data = cursor.fetchone()
        conn.close()
        return data

    def obtener_niveles(self, curso_id):
        conn = self.connect_cursos()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM niveles WHERE curso_id = ?", (curso_id,))
        data = cursor.fetchall()
        conn.close()
        return data

    def obtener_curso_de_nivel(self, nivel_id):
        conn = self.connect_cursos()
        cursor = conn.cursor()
        cursor.execute("SELECT curso_id FROM niveles WHERE id = ?", (nivel_id,))
        curso_id = cursor.fetchone()
        conn.close()
        return curso_id['curso_id'] if curso_id else None

    # ============================================================
    #   WIZARD / CURSOS RÁPIDOS
    # ============================================================
    def wizard_crear_curso(self, titulo, descripcion, ruta_img=None):
        """
        Método usado por el endpoint /api/cursos/crear
        para crear un curso con valores predeterminados si no se envían.
        ruta_img: nombre del archivo subido (opcional)
        """
        categoria = "General"
        duracion = "1h"
        return self.agregar_curso(titulo, descripcion, categoria, duracion, ruta_img)

    def wizard_agregar_niveles(self, curso_id, niveles):
        """
        Agrega múltiples niveles a un curso.
        
        Args:
            curso_id: ID del curso al que pertenecen los niveles
            niveles: Lista que puede contener:
                     - Strings: ["Nivel 1", "Nivel 2"]
                     - Diccionarios: [{"titulo": "Nivel 1", "descripcion": "..."}, ...]
        
        Returns:
            Lista de IDs de los niveles creados, o None si hay error
        """
        if not isinstance(niveles, list):
            print("ERROR: 'niveles' debe ser una lista")
            return None
        
        nivel_ids = []
        conn = self.connect_cursos()
        cursor = conn.cursor()
        
        try:
            for nivel in niveles:
                if isinstance(nivel, str):
                    titulo = nivel
                    descripcion = ""
                elif isinstance(nivel, dict):
                    titulo = nivel.get("titulo", "Sin titulo")
                    descripcion = nivel.get("descripcion", "")
                else:
                    print(f"ADVERTENCIA: Tipo de nivel no esperado: {type(nivel)}")
                    continue
                
                cursor.execute("""
                    INSERT INTO niveles (curso_id, titulo, descripcion)
                    VALUES (?, ?, ?)
                """, (curso_id, titulo, descripcion))
                
                nivel_ids.append(cursor.lastrowid)
            
            conn.commit()
            print(f"Niveles creados exitosamente: {nivel_ids}")
            return nivel_ids
            
        except sqlite3.Error as e:
            print(f"ERROR SQLite al agregar niveles: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()

    # ============================================================
    #   FUNCIÓN INTERNA: FORMATEAR URL DE YOUTUBE
    # ============================================================
    def _format_youtube_url(self, url):
        """
        Convierte una URL de YouTube normal a formato embebible.
        Soporta:
          - https://www.youtube.com/watch?v=VIDEO_ID
          - https://youtu.be/VIDEO_ID
          - Si ya es /embed/ o no es YouTube, la devuelve tal cual.
        """
        if not url:
            return None

        url = url.strip()

        # Ya está en formato embed
        if "youtube.com/embed/" in url:
            return url

        # Formato estándar: watch?v=
        if "youtube.com/watch" in url and "v=" in url:
            video_id = url.split("v=")[1].split("&")[0]
            return f"https://www.youtube.com/embed/{video_id}"

        # Formato corto: youtu.be
        if "youtu.be/" in url:
            video_id = url.split("youtu.be/")[1].split("?")[0]
            return f"https://www.youtube.com/embed/{video_id}"

        # Cualquier otra cosa (otra plataforma, mp4, etc.)
        return url

    # ============================================================
    #   LECCIONES
    # ============================================================
    def wizard_agregar_leccion(self, nivel_id, titulo, contenido, video_url, pdf_filename):
        # Ajustar la URL de YouTube antes de guardar
        video_url = self._format_youtube_url(video_url)

        conn = self.connect_cursos()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO lecciones (nivel_id, titulo, contenido, video_url, pdf_file)
                VALUES (?, ?, ?, ?, ?)
            """, (nivel_id, titulo, contenido, video_url, pdf_filename))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"ERROR SQLite al agregar leccion: {e}")
            return None
        finally:
            conn.close()

    def obtener_lecciones(self, nivel_id):
        conn = self.connect_cursos()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM lecciones WHERE nivel_id = ?", (nivel_id,))
        data = cursor.fetchall()
        conn.close()
        return data

    def obtener_leccion(self, leccion_id):
        conn = self.connect_cursos()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM lecciones WHERE id = ?", (leccion_id,))
        data = cursor.fetchone()
        conn.close()
        return data

    # ============================================================
    #   EXÁMENES Y PREGUNTAS
    # ============================================================
    def agregar_examen(self, nivel_id, titulo, descripcion):
        conn = self.connect_cursos()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO examenes (nivel_id, titulo, descripcion)
                VALUES (?, ?, ?)
            """, (nivel_id, titulo, descripcion))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"ERROR SQLite al agregar examen: {e}")
            return None
        finally:
            conn.close()

    def eliminar_examen(self, examen_id):
        conn = self.connect_cursos()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM examenes WHERE id = ?", (examen_id,))
        conn.commit()
        conn.close()

    def obtener_examenes_por_nivel(self, nivel_id):
        conn = self.connect_cursos()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM examenes WHERE nivel_id = ?", (nivel_id,))
        data = cursor.fetchall()
        conn.close()
        return data

    def obtener_examen(self, examen_id):
        conn = self.connect_cursos()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM examenes WHERE id = ?", (examen_id,))
        data = cursor.fetchone()
        conn.close()
        return data

    def agregar_pregunta(self, examen_id, texto, correcta):
        conn = self.connect_cursos()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO preguntas (examen_id, texto, correcta)
                VALUES (?, ?, ?)
            """, (examen_id, texto, correcta))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"ERROR SQLite al agregar pregunta: {e}")
            return None
        finally:
            conn.close()

    def obtener_preguntas(self, examen_id):
        conn = self.connect_cursos()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM preguntas WHERE examen_id = ?", (examen_id,))
        data = cursor.fetchall()
        conn.close()
        return data

    # ============================================================
    #   RESPUESTAS
    # ============================================================
    def guardar_respuesta(self, usuario_id, examen_id, pregunta_id, respuesta, es_correcta):
        conn = self.connect_cursos()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO respuestas (usuario_id, examen_id, pregunta_id, respuesta_dada, es_correcta)
                VALUES (?, ?, ?, ?, ?)
            """, (usuario_id, examen_id, pregunta_id, respuesta, es_correcta))
            conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"ERROR SQLite al guardar respuesta: {e}")
            return False
        finally:
            conn.close()