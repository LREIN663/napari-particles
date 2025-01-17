import h5py
import numpy as np
import yaml as _yaml
import os.path as _ospath
from tkinter import filedialog as fd
from tkinter import Tk
import napari
import matplotlib.pyplot as plt
from napari_particles.particles import Particles
import easygui
from ._dock_widget import dataset,create_new_layer


def load_info(path):
    path_base, path_extension = _ospath.splitext(path)
    filename = path_base + ".yaml"
    try:
        with open(filename, "r") as info_file:
            info = list(_yaml.load_all(info_file, Loader=_yaml.FullLoader))
    except FileNotFoundError as e:
        print(
            "\nAn error occured. Could not find metadata file:\n{}".format(
                filename
            )
        )
    return info


def load_locs(path):
    with h5py.File(path, "r") as locs_file:
        locs = locs_file["locs"][...]
    locs = np.rec.array(
        locs, dtype=locs.dtype
    )  # Convert to rec array with fields as attributes
    info = load_info(path)
    return locs, info


def load_hdf5(self, file_path):
    filename = file_path.split('/')[-1]
    locs, info = load_locs(file_path)
    try:
        pixelsize = locs.pixelsize
    except:
        pixelsize = int(easygui.enterbox("Pixelsize?"))
    self.pixelsize = pixelsize
    try:
        locs.z
        zdim = True
        self.C3d.setChecked(True)
    except:
        zdim=False
    self.list_of_datasets.append(dataset(locs=locs, parent=self, zdim=zdim, pixelsize=pixelsize, name=filename))

    create_new_layer(self=self, aas=0.1,  layer_name=filename, idx=-1)


def load_h5(self, file_path):
    filename = file_path.split('/')[-1]
    LOCS_DTYPE_2D = [("frame", "f4"), ("x", "f4"), ("y", "f4"), ("photons", "f4")]
    LOCS_DTYPE_3D = [("frame", "f4"), ("x", "f4"), ("y", "f4"), ("z", "f4"), ("photons", "f4")]
    with h5py.File(file_path, "r") as locs_file:
        data = locs_file['molecule_set_data']['datatable'][...]
        pixelsize = locs_file['molecule_set_data']['xy_pixel_size_um'][...] * 1E3  # to µm to nm
    try:
        locs = np.rec.array((data['FRAME_NUMBER'], data['X_POS_PIXELS'], data['Y_POS_PIXELS'], data['Z_POS_PIXELS'],
                             data['PHOTONS']), dtype=LOCS_DTYPE_3D)
        zdim = True
        self.C3d.setChecked(True)
    except:
        locs = np.rec.array((data['FRAME_NUMBER'], data['X_POS_PIXELS'], data['Y_POS_PIXELS'],
                             data['PHOTONS']), dtype=LOCS_DTYPE_2D)
        zdim = False
    num_channel = max(data['CHANNEL']) + 1
    for i in range(num_channel):
        locs_in_ch=locs[data['CHANNEL']==i]
        self.list_of_datasets.append(dataset(locs=locs_in_ch, zdim=zdim, parent=self, pixelsize=pixelsize, name=filename+f" Channel {i+1}"))
        create_new_layer(self=self, aas=0.1,  layer_name=filename+f" Channel {i+1}", idx=-1)

def load_mfx_json(self,file_path): # 3D not implemented yet
    LOCS_DTYPE_2D = [("frame", "f4"), ("x", "f4"), ("y", "f4"), ("photons", "f4")]
    LOCS_DTYPE_3D = [("frame", "f4"), ("x", "f4"), ("y", "f4"), ("z", "f4"), ("photons", "f4")]
    filename = file_path.split('/')[-1]
    with open(file_path) as f:
        raw_data=json.load(f)
    f.close()
    locsx=[]
    locsy=[]
    try:
        zdim = True
        self.C3d.setChecked(True)
    except:
        zdim = False
    if zdim:
        locsz = []
        for i in range(len(raw_data)):
            if raw_data['vld'][i]:
                locsx.append((raw_data[i]['itr'][-1]['loc'][0]) * 1E9)
                locsy.append((raw_data[i]['itr'][-1]['loc'][1]) * 1E9)
                locsz.append((raw_data[i]['itr'][-1]['loc'][2]) * 1E9)
        frames = np.ones(len(locsx))
        photons = 1000 * np.ones(len(locsx))
        pixelsize = 1
        locs = np.rec.array(
            (frames, locsx, locsy, locsz, photons),
            dtype=LOCS_DTYPE_3D, )
    else:
        for i in range(len(raw_data)):
            if raw_data['vld'][i]:
                locsx.append((raw_data[i]['itr'][-1]['loc'][0]) * 1E9)
                locsy.append((raw_data[i]['itr'][-1]['loc'][1]) * 1E9)
        frames = np.ones(len(locsx))
        photons = 1000 * np.ones(len(locsx))
        pixelsize = 1
        locs = np.rec.array(
            (frames, locsx, locsy, photons),
            dtype=LOCS_DTYPE_2D, )
    self.list_of_datasets.append(dataset(locs=locs, zdim=zdim, parent=self, pixelsize=pixelsize, name=filename))
    create_new_layer(self=self, aas=0.1, layer_name=filename, idx=-1)



def load_mfx_npy(self,file_path):
    LOCS_DTYPE_2D = [("frame", "f4"), ("x", "f4"), ("y", "f4"), ("photons", "f4")]
    LOCS_DTYPE_3D = [("frame", "f4"), ("x", "f4"), ("y", "f4"), ("z", "f4"), ("photons", "f4")]
    filename = file_path.split('/')[-1]
    raw_data=np.load(file_path)
    locsx=[]
    locsy=[]
    minx= min(raw_data['itr']['loc'][:,-1,0])
    miny=min(raw_data['itr']['loc'][:,-1,1])
    try:
        minz=min(raw_data['itr']['loc'][:,-1,2])
        zdim=True
        self.C3d.setChecked(True)
    except:
        zdim=False
    if zdim:
        locsz=[]
        for i in range(len(raw_data)):
            if raw_data['vld'][i]:
                locsx.append((raw_data['itr']['loc'][i, -1, 0]) * 1E9)
                locsy.append((raw_data['itr']['loc'][i, -1, 1]) * 1E9)
                locsz.append((raw_data['itr']['loc'][i, -1, 2]) * 1E9)
        frames = np.ones(len(locsx))
        photons = 1000 * np.ones(len(locsx))
        pixelsize = 1
        locs = np.rec.array(
            (frames, locsx, locsy, locsz, photons),
            dtype=LOCS_DTYPE_3D, )
    else:
        for i in range(len(raw_data)):
            if raw_data['vld'][i]:
                locsx.append((raw_data['itr']['loc'][i, -1, 0]-minx)*1E9)
                locsy.append((raw_data['itr']['loc'][i, -1, 1]-miny)*1E9)
        frames = np.ones(len(locsx))
        photons = 1000 * np.ones(len(locsx))
        pixelsize = 1
        locs = np.rec.array(
            (frames, locsx, locsy, photons),
            dtype=LOCS_DTYPE_2D, )
    self.list_of_datasets.append(dataset(locs=locs, zdim=zdim, parent=self, pixelsize=pixelsize, name=filename))
    create_new_layer(self=self, aas=0.1, layer_name=filename, idx=-1)


def load_csv(self, file_path):
    filename = file_path.split('/')[-1]
    data = {}
    LOCS_DTYPE_2D = [("frame", "f4"), ("x", "f4"), ("y", "f4"), ("photons", "f4")]
    LOCS_DTYPE_3D = [("frame", "f4"), ("x", "f4"), ("y", "f4"), ("z", "f4"), ("photons", "f4")]
    with open(file_path, mode='r') as infile:
        header = infile.readline()
        header = header.replace('\n', '')
        header = header.split(',')
        data_list = np.loadtxt(file_path, delimiter=',', skiprows=1, dtype=float)
    for i in range(len(header)):
        data[header[i]] = data_list[:, i]
    try:
        pixelsize = data['"pixelsize"']
    except:
        pixelsize = int(easygui.enterbox("Pixelsize?"))
    try:
        locs = np.rec.array(
            (data['"frame"'], data['"x [nm]"'] / pixelsize, data['"y [nm]"'] / pixelsize, data['"z [nm]"'] / pixelsize,
             data['"intensity [photon]"']), dtype=LOCS_DTYPE_3D)
        zdim = True
        self.C3d.setChecked(True)
    except:
        locs = np.rec.array(
            (data['"frame"'], data['"x [nm]"'] / pixelsize, data['"y [nm]"'] / pixelsize, data['"intensity [photon]"']),
            dtype=LOCS_DTYPE_2D, )
        zdim = False
    self.list_of_datasets.append(dataset(locs=locs, zdim=zdim, parent=self, pixelsize=pixelsize, name=filename))
    create_new_layer(self=self, aas=0.1,  layer_name=filename, idx=-1)


## load_SMLM adapted from Marting Weigerts readSmlmFile
import zipfile
import json
import struct
import io
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
dtype2struct = {'uint8': 'B', 'uint32': 'I', 'float64': 'd', 'float32': 'f'}
dtype2length = {'uint8': 1, 'uint32': 4, 'float64': 8, 'float32': 4}


def load_SMLM(self, file_path):
    filename = file_path.split('.')[-1]
    zf = zipfile.ZipFile(file_path, 'r')
    file_names = zf.namelist()
    if "manifest.json" in file_names:
        manifest = json.loads(zf.read("manifest.json"))
        assert manifest['format_version'] == '0.2'
        for file_info in manifest['files']:
            if file_info['type'] == "table":
                logger.info('loading table...')
                format_key = file_info['format']
                file_format = manifest['formats'][format_key]
                if file_format['mode'] == 'binary':
                    try:
                        table_file = zf.read(file_info['name'])
                        logger.info(file_info['name'])
                    except KeyError:
                        logger.error('ERROR: Did not find %s in zip file', file_info['name'])
                        continue
                    else:
                        logger.info('loading table file: %s bytes', len(table_file))
                        logger.info('headers: %s', file_format['headers'])
                        headers = file_format['headers']
                        dtype = file_format['dtype']
                        shape = file_format['shape']
                        cols = len(headers)
                        rows = file_info['rows']
                        logger.info('rows: %s, columns: %s', rows, cols)
                        assert len(headers) == len(dtype) == len(shape)
                        rowLen = 0
                        for i, h in enumerate(file_format['headers']):
                            rowLen += dtype2length[dtype[i]]

                        tableDict = {}
                        byteOffset = 0
                        try:
                            import numpy as np
                            for i, h in enumerate(file_format['headers']):
                                tableDict[h] = np.ndarray((rows,), buffer=table_file, dtype=dtype[i], offset=byteOffset,
                                                          order='C', strides=(rowLen,))
                                byteOffset += dtype2length[dtype[i]]
                        except ImportError:
                            logger.warning(
                                'Failed to import numpy, performance will drop dramatically. Please install numpy for the best performance.')
                            st = ''
                            for i, h in enumerate(file_format['headers']):
                                st += (str(shape[i]) + dtype2struct[dtype[i]])

                            unpack = struct.Struct(st).unpack
                            tableDict = {h: [] for h in headers}
                            for i in range(0, len(table_file), rowLen):
                                unpacked_data = unpack(table_file[i:i + rowLen])
                                for j, h in enumerate(headers):
                                    tableDict[h].append(unpacked_data[j])
                            tableDict = {h: np.array(tableDict[h]) for i, h in enumerate(headers)}
                        data = {}
                        data['min'] = [tableDict[h].min() for h in headers]
                        data['max'] = [tableDict[h].max() for h in headers]
                        data['avg'] = [tableDict[h].mean() for h in headers]
                        data['tableDict'] = tableDict
                        file_info['data'] = data
                        logger.info('table file loaded: %s', file_info['name'])
                else:
                    raise Exception('format mode {} not supported yet'.format(file_format['mode']))
            elif file_info['type'] == "image":
                if file_format['mode'] == 'binary':
                    try:
                        image_file = zf.read(file_info['name'])
                        logger.info('image file loaded: %s', file_info['name'])
                    except KeyError:
                        logger.error('ERROR: Did not find %s in zip file', file_info['name'])
                        continue
                    else:
                        from PIL import Image
                        image = Image.open(io.BytesIO(image_file))
                        data = {}
                        data['image'] = image
                        file_info['data'] = data
                        logger.info('image file loaded: %s', file_info['name'])

            else:
                logger.info('ignore file with type: %s', file_info['type'])
    else:
        raise Exception('invalid file: no manifest.json found in the smlm file')
    prop = manifest['files'][-1]['data']['tableDict']
    LOCS_DTYPE_2D = [("frame", "f4"), ("x", "f4"), ("y", "f4"), ("photons", "f4")]
    LOCS_DTYPE_3D = [("frame", "f4"), ("x", "f4"), ("y", "f4"), ("z", "f4"), ("photons", "f4")]
    try:
        pixelsize = prop['pixelsize']
    except:
        pixelsize = int(easygui.enterbox("Pixelsize?"))
    if not 'intensity_photon_' in prop.keys():  # If the photons are not given, set them to 1k
        prop['intensity_photon_'] = 1000 * np.ones(len(prop['x']))
    try:
        locs = np.rec.array(
            (prop['frame'], prop['x'] / pixelsize, prop['y'] / pixelsize, prop['z'] / pixelsize,
             prop['intensity_photon_']), dtype=LOCS_DTYPE_3D)
        zdim = True
        self.C3d.setChecked(True)
    except:
        locs = np.rec.array(
            (prop['frame'], prop['x'] / pixelsize, prop['y'] / pixelsize,
             prop['intensity_photon_']), dtype=LOCS_DTYPE_2D)
        zdim = False
    self.list_of_datasets.append(dataset(locs=locs, zdim=zdim, parent=self, pixelsize=pixelsize, name=filename))
    create_new_layer(self=self, aas=0.1,  layer_name=filename, idx=-1)

##### Lowest Order functions