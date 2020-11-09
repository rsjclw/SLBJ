from PyQt5.QtGui import QImage, QPixmap
from cv2 import resize, cvtColor, COLOR_BGR2RGB
import numpy as np

def convertToQPixmap(img):
    shape = img.shape
    try:
        img = cvtColor(img, COLOR_BGR2RGB)
        img = QImage(img.data, img.shape[1], img.shape[0], img.strides[0], QImage.Format_RGB888)
    except:
        img = zeros(shape, dtype=uint8)
        img = QImage(img.data, img.shape[1], img.shape[0], img.strides[0], QImage.Format_RGB888)
    return QPixmap.fromImage(img)

class Globe:
    # Load the data from file.
    def __init__(self, map_path):
        # full_path = os.path.realpath(__file__)
        # _path, _ = os.path.split(full_path)
        # _mask_filename = os.path.join(_path,'globe_combined_mask_compressed.npz')
        # _mask_fid = np.load(_mask_filename)
        # self.mask = _mask_fid['mask']
        # self.lat = _mask_fid['lat']
        # self.lon = _mask_fid['lon']

        # np.savez_compressed("worldmap.npz", mask=self.mask, latMax=self.LATMAX, lonMax=179.99166666666667, latMin=-89.99166666666667, lonMin=self.LONMIN, latLen=21600, lonLen=43200)

        _mask_fid = np.load(map_path)
        self.mask = _mask_fid['mask']
        self.LATMAX = _mask_fid['latMax']
        self.LONMIN = _mask_fid['lonMin']
        self.LATMAXIDX = _mask_fid['latLen']
        self.LONMAXIDX = _mask_fid['lonLen']
        self.DLAT = -(_mask_fid['latMax']-_mask_fid['latMin'])/(_mask_fid['latLen']-1)
        self.DLON = (_mask_fid['lonMax']-_mask_fid['lonMin'])/(_mask_fid['lonLen']-1)

    def latToIndex(self, lat):
        return (int)((lat-self.LATMAX)/self.DLAT)

    def lonToIndex(self, lon):
        return (int)((lon-self.LONMIN)/self.DLON)

    def latIndextoLat(self, latIndex):
        return latIndex*self.DLAT+self.LATMAX

    def lonIndextoLon(self, lonIndex):
        return lonIndex*self.DLON+self.LONMIN
    
    def isLand(self, latIdx, lonIdx):
        return not self.mask[latIdx, lonIdx]

    def lat_to_index(self, lat):
        lat = np.array(lat)
        if np.any(lat>90): raise ValueError('latitude must be <= 90')
        if np.any(lat<-90): raise ValueError('latitude must be >= -90')
        lat[lat > self.lat.max()] = self.lat.max()
        lat[lat < self.lat.min()] = self.lat.min()
        return ((lat - self.lat[0])/(self.lat[1]-self.lat[0])).astype('int')

    def lon_to_index(self, lon):
        lon = np.array(lon)
        if np.any(lon > 180): raise ValueError('longitude must be <= 180')
        if np.any(lon < -180): raise ValueError('longitude must be >= -180')
        lon[lon > self.lon.max()] = self.lon.max()
        lon[lon < self.lon.min()] = self.lon.min()
        return ((lon - self.lon[0]) / (self.lon[1] - self.lon[0])).astype('int')

    def is_ocean(self, lat,lon):
        lat_i = lat_to_index(lat)
        lon_i = lon_to_index(lon)
        return self.mask[lat_i,lon_i]

    def is_land(self, lat,lon):
        lat_i = lat_to_index(lat)
        lon_i = lon_to_index(lon)
        return np.logical_not(self.mask[lat_i,lon_i])
    
    def search_land(self, lat, lon, maxRange):
        heap = []
        visited = {}
        a = {}
        latIdx = self.latToIndex(lat)
        lonIdx = self.lonToIndex(lon)
        heappush(heap, (0, latIdx, lonIdx))
        visited[(latIdx, lonIdx)] = True
        print("searching")
        while(len(heap) > 0):
            node = heappop(heap)
            cd = node[0]
            latIdx = node[1]
            lonIdx = node[2]
            lat = degree2rad(self.latIndextoLat(latIdx))
            lon = degree2rad(self.lonIndextoLon(lonIdx))
            if self.isLand(latIdx, lonIdx): return rad2Degree(lat), rad2Degree(lon)
            nextIdx = (latIdx+1)%self.LATMAXIDX # atas
            if not ((nextIdx, lonIdx) in visited):
                d = cd+getGreatCircleDistance(degree2rad(self.latIndextoLat(nextIdx)), lon, lat, lon)
                if d < maxRange:
                    visited[(nextIdx, lonIdx)] = True
                    heappush(heap, (d, nextIdx, lonIdx))
            
            nextIdx = (lonIdx+1)%self.LONMAXIDX # kanan
            if not ((latIdx, nextIdx) in visited):
                d = cd+getGreatCircleDistance(lat, degree2rad(self.lonIndextoLon(nextIdx)), lat, lon)
                if d < maxRange:
                    visited[(latIdx, nextIdx)] = True
                    heappush(heap, (d, latIdx, nextIdx))
            
            nextIdx = (latIdx-1)%self.LATMAXIDX # bawah
            if not ((nextIdx, lonIdx) in visited):
                d = cd+getGreatCircleDistance(degree2rad(self.latIndextoLat(nextIdx)), lon, lat, lon)
                if d < maxRange:
                    visited[(nextIdx, lonIdx)] = True
                    heappush(heap, (d, nextIdx, lonIdx))
            
            nextIdx = (lonIdx-1)%self.LONMAXIDX # kiri
            if not ((latIdx, nextIdx) in visited):
                d = cd+getGreatCircleDistance(lat, degree2rad(self.lonIndextoLon(nextIdx)), lat, lon)
                if d < maxRange:
                    visited[(latIdx, nextIdx)] = True
                    heappush(heap, (d, latIdx, lonIdx))
            
            # print(cd)
        return None
