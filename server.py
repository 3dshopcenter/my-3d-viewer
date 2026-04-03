from flask import Flask, request, send_file, send_from_directory, abort
from OCC.Core.STEPControl import STEPControl_Reader
from OCC.Core.IGESControl import IGESControl_Reader
from OCC.Extend.DataExchange import write_gltf_file
import os, tempfile, shutil

app = Flask(__name__)

# Максимальный размер файла — 50 МБ
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

# Разрешённые форматы
ALLOWED_EXTENSIONS = {'stp', 'step', 'igs', 'iges', 'stl'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[-1].lower() in ALLOWED_EXTENSIONS

@app.errorhandler(413)
def too_large(e):
    return {'error': 'Файл слишком большой. Максимум 50 МБ'}, 413

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/convert', methods=['POST'])
def convert():
    if 'model' not in request.files:
        return {'error': 'Файл не найден'}, 400

    file = request.files['model']

    if not file.filename:
        return {'error': 'Имя файла пустое'}, 400

    if not allowed_file(file.filename):
        return {'error': 'Формат не поддерживается'}, 400

    ext = file.filename.rsplit('.', 1)[-1].lower()

    tmp = tempfile.mkdtemp()
    try:
        input_path = os.path.join(tmp, 'input.' + ext)
        output_path = os.path.join(tmp, 'output.glb')
        file.save(input_path)

        if ext in ('stp', 'step'):
            reader = STEPControl_Reader()
            reader.ReadFile(input_path)
            reader.TransferRoots()
            shape = reader.OneShape()
        elif ext in ('igs', 'iges'):
            reader = IGESControl_Reader()
            reader.ReadFile(input_path)
            reader.TransferRoots()
            shape = reader.OneShape()
        elif ext == 'stl':
            from OCC.Core.StlAPI import StlAPI_Reader
            from OCC.Core.TopoDS import TopoDS_Shape
            from OCC.Core.BRep import BRep_Builder
            stl_reader = StlAPI_Reader()
            shape = TopoDS_Shape()
            BRep_Builder()
            stl_reader.Read(shape, input_path)
        else:
            return {'error': 'Формат не поддерживается'}, 400

        write_gltf_file(shape, output_path)
        return send_file(output_path, mimetype='model/gltf-binary')

    except Exception as e:
        return {'error': 'Ошибка конвертации: ' + str(e)}, 500

    finally:
        shutil.rmtree(tmp, ignore_errors=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)