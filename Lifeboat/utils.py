"""

global-land-mask is a python module for checking whether a lat/lon point is
on land or on sea. In order to do this, we use the globe dataset,
which samples the entire earth at 1 km resolution.

The global mask is of shape (21600, 43200), coming to about 980 mB when
saved without compression. This data can be compressed to 2.5 mb using numpy
savez_compressed, making for a very compact package.


"""

import numpy as np
import os
import cv2
from heapq import heappop, heappush
from math import sin, cos, sqrt, atan2, asin, acos

def degree2rad(x): return x*0.017453292519943295
def rad2Degree(x): return x*57.29577951308232

def getAngularDistance(lat0, lon0, lat1, lon1):
    sDLat = sin((lat1-lat0)/2.0)
    sdLon = sin((lon1-lon0)/2.0)
    a = sDLat*sDLat+cos(lat0)*cos(lat1)*sdLon*sdLon
    return 2 * atan2(sqrt(a), sqrt(1-a))

def getGreatCircleDistance(lat0, lon0, lat1, lon1):
    return 6371e3*getAngularDistance(lat0, lon0, lat1, lon1) # R*angular distance

def getBearing(lat0, lon0, lat1, lon1):
    dLon = lon1-lon0
    cLat1 = cos(lat1)
    return atan2(sin(dLon)*cLat1, cos(lat0)*sin(lat1)-sin(lat0)*cLat1*cos(dLon))

class PIDControl:
    def __init__(self, p, i, d, cutoff):
        self.p = p
        self.i = i
        self.d = d
        self.cutoff = cutoff
        self.reset()
    
    def control(self, error):
        self.sumError += error
        out = self.p*error + self.i*self.sumError + self.d*(error-self.prevError)
        self.prevError = error
        if self.sumError < self.cutoff: self.sumError = -self.cutoff
        elif self.sumError > self.cutoff: self.sumError = self.cutoff
        return out
    
    def reset(self):
        self.sumError = 0
        self.prevError = 0

class Control:
    def __init__(self, PIDCutoffDistance, PIDCutoffHeading, distanceThreshold):
        self.distanceController = PIDControl(PIDCutoffDistance[0], PIDCutoffDistance[1], PIDCutoffDistance[2], PIDCutoffDistance[3])
        self.headingController = PIDControl(PIDCutoffHeading[0], PIDCutoffHeading[1], PIDCutoffHeading[2], PIDCutoffHeading[3])
        self.distanceThreshold = distanceThreshold
        self.isSet = False
    
    def setControlPoint(self, initLat, initLon, destLat, destLon):
        self.lat0 = degree2rad(initLat)
        self.lon0 = degree2rad(initLon)
        self.lat1 = degree2rad(destLat)
        self.lon1 = degree2rad(destLon)
        self.initBearing = getBearing(self.lat0, self.lon0, self.lat1, self.lon1)
        self.sInitBearing = sin(self.initBearing)
        self.cInitBearing = cos(self.initBearing)
        self.sLat0 = sin(self.lat0)
        self.cLat0 = cos(self.lat0)
        self.arrived = False
        self.isSet = True
    
    def __normalizeHeading(self, angle):
        return (angle+360)%360
    
    def __getHeadingError(self, desiredHeading, currentHeading):
        angle = self.__normalizeHeading(desiredHeading-currentHeading)
        if angle > 180: return angle-360
        return angle
    
    def control(self, lat, lon, heading):
        if not self.isSet: return 0
        lat = degree2rad(lat)
        lon = degree2rad(lon)
        if getGreatCircleDistance(lat, lon, self.lat1, self.lon1) < self.distanceThreshold:
            self.isSet = False
            self.arrived = True
            return 0
        ad = getAngularDistance(self.lat0, self.lon0, lat, lon)
        actDistance = asin(sin(ad)*sin(getBearing(self.lat0, self.lon0, lat, lon)-self.initBearing))
        aAtDistance = acos(cos(ad)/cos(actDistance))
        saAtDistance = sin(aAtDistance)
        caAtDistance = cos(aAtDistance)
        nearestLatAt = asin(self.sLat0*caAtDistance+self.cLat0*saAtDistance*self.cInitBearing)
        nearestLonAt = self.lon0+atan2(self.sInitBearing*saAtDistance*self.cLat0, caAtDistance-self.sLat0*sin(nearestLatAt))
        trueBearing = self.__normalizeHeading(rad2Degree(getBearing(nearestLatAt, nearestLonAt, self.lat1, self.lon1)))
        headingError = self.__getHeadingError(trueBearing, heading)
        headingControlOutput = self.headingController.control(headingError)
        distanceControlOutput = self.distanceController.control(actDistance*6371e5)

        controlOutput  = distanceControlOutput

        if distanceControlOutput < 0:
            maxHeadingError = self.__getHeadingError(self.__normalizeHeading(trueBearing-90), heading)
            maxHeadingControlOutput = self.headingController.control(maxHeadingError)
            controlOutput = max(controlOutput, maxHeadingControlOutput)
        else:
            maxHeadingError = self.__getHeadingError(self.__normalizeHeading(trueBearing+90), heading)
            maxHeadingControlOutput = self.headingController.control(maxHeadingError)
            controlOutput = min(controlOutput, maxHeadingControlOutput)
        # print("headingControl: {}, distanceControl: {}, maxHeadingControl: {}, maxHeadingError: {}".format(headingControlOutput, distanceControlOutput, maxHeadingControlOutput, maxHeadingError))
        # print("true bearing: {}, heading error: {}, dist error: {}".format(trueBearing, headingError, actDistance*6371e5))
        return distanceControlOutput
    
    def isArrived(self):
        return self.arrived

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

# from time import sleep
# if __name__ == "__main__":
#     c = Control([1.5,0,1,4], [1.5,0,1,4])
#     c.setControlPoint(-7.286276, 112.795992, -7.286410, 112.796010)
#     c.control(-7.286345, 112.796017, 180) # -7.286352, 112.795988
#     # 33.1234789, 123.1234567 // laut
#     # -6.533850, 106.800901 // darat
#     print("gukguk")
#     latIdx0 = lat_to_index(-6.533850)
#     latIdx1 = latToIndex(-6.533850)
#     lonIdx0 = lon_to_index(106.800901)
#     lonIdx1 = lonToIndex(106.800901)
#     # print("converting")
#     _mask = np.array(_mask, dtype=np.uint8)
#     # print("saving")
#     # cv2.imwrite("mapmask.png", _mask)
#     print("reading")
#     imagemask = cv2.imread("mapmask.png", cv2.IMREAD_UNCHANGED)
#     sleep(3)
#     print("checking")
#     print(np.array_equal(imagemask, _mask))
    
#     # print(latIndextoLat(latIdx0), lonIndextoLon(lonIdx1))

#     # print("lat min: {}, lon min: {}".format(self.lat.min(), self.lon.min()))
#     # print("self.latMax: {}, lon max: {}".format(self.lat.max(), self.lon.max()))
#     # print("lat0: {}, lon0: {}".format(self.lat[0], self.lon[0]))
#     # print("lat1: {}, lon1: {}".format(self.lat[1], self.lon[1]))
#     # print("lat max - lat min:", self.lat.max()-self.lat.min())
#     # print("lon max - lon min:", self.lon.max()-self.lon.min())
#     # print("lat 1 - lat 0:", self.lat[1]-self.lat[0])
#     # print("lon 1 - lon 0:", self.lon[1]-self.lon[0])