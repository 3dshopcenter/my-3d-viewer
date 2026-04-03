from flask import Flask, request, send_file, send_from_directory
from OCC.Core.STEPControl import STEPControl_Reader
from OCC.Core.IGESControl import IGESControl_Reader
from OCC.Extend.DataExchange import write_gltf_file
import os, tempfile, shutil

app = Flask(__name__)

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/convert', methods=['POST'])
def convert():
    file = request.files['model']
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
            from OCC.Core.BRep import BRep_Builder
            from OCC.Core.TopoDS import TopoDS_Shape
            stl_reader = StlAPI_Reader()
            shape = TopoDS_Shape()
            builder = BRep_Builder()
            stl_reader.Read(shape, input_path)
        else:
            return {'error': 'Формат не поддерживается'}, 400

        write_gltf_file(shape, output_path)
        return send_file(output_path, mimetype='model/gltf-binary')

    finally:
        shutil.rmtree(tmp, ignore_errors=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)