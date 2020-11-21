#include <vector>
#include <unordered_map>
#include <string>
#include <queue>
#include <math.h>
#include <boost/functional/hash.hpp>
#include <sys/time.h>
#include <thread>
#include <opencv2/highgui/highgui.hpp>
#include <opencv2/core.hpp>
#include <opencv2/imgcodecs/imgcodecs.hpp>
#include "TCPServer.hpp"
#define R 6371e3 // meter
#define M_PI 3.14159265358979323846
// total pixel: 933120000

using namespace std;
using namespace cv;

typedef struct{
    double lat, lon;
    int latIdx, lonIdx, fd;
} Ship;

typedef struct{
    double lat, lon, saverLat, saverLon;
    char status;
    int fd;
    bool searching;
    unsigned int maxRange;
    string saver;
    time_t timestamp;
} SBoat;

typedef unordered_map <string, Ship> ShipsMap;
typedef unordered_map <string, SBoat> SBoatsMap;
typedef unordered_map <int, string> fdsMap;
typedef unordered_map <pair <int, int>, string, boost::hash <pair <int, int> > > World;

class GCS{
    public:
    int fd;
    GCS(){
    }
    void init(const string &id_, SBoatsMap *sboats_, TCPServer *tcpServer, mutex *mtxSBoats_){
        this->tcp = tcpServer;
        this->sboats = sboats_;
        this->updating = false;
        this->deleting = false;
        this->t = NULL;
        this->id = id_;
        this->mtxSBoats = mtxSBoats_;
    }
    ~GCS(){
        this->deleting = true;
        while(this->updating){
            usleep(1000);
        }
    }
    void updateData(){
        mtxUpdate.lock();
        if(this->updating){
            mtxUpdate.unlock();
            return;
        }
        this->updating = true;
        mtxUpdate.unlock();
        if(this->t != NULL){
            this->t->join();
            delete this->t;
            this->t = NULL;
        }
        t = new thread(&GCS::__updateData, this);
    }

    private:
    string id;
    thread *t;
    string camBoatID;
    TCPServer *tcp;
    SBoatsMap *sboats;
    bool updating, deleting;
    mutex mtxUpdate;
    mutex *mtxSBoats;
    void __updateData(){
        this->mtxSBoats->lock();
        SBoatsMap sboatsTemp = *sboats;
        this->mtxSBoats->unlock();
        char msg[256];
        for (auto i : sboatsTemp){
            if(this->deleting) break;
            sprintf(msg, "$%s;%.7lf;%.7lf;%.7lf;%.7lf;%c", i.first.c_str(), i.second.lat, i.second.lon, i.second.saverLat, i.second.saverLon, i.second.status);
            this->tcp->sendData(fd, msg);
            usleep(1);
        }
        sprintf(msg, "$!!");
        this->tcp->sendData(fd, msg);
        mtxUpdate.lock();
        this->updating = false;
        mtxUpdate.unlock();
    }
};

struct comparePQ
{
    bool operator()(const pair <double, pair <int, int> >& l, const pair <double, pair <int, int> >& r){
        return l.first > r.first;
    }
};

typedef unordered_map <string, GCS> GCSMap;


typedef priority_queue <pair <double, pair <int, int> >, vector<pair <double, pair <int, int> > >, comparePQ> PQueue;

double degree2rad(double x){
    return x*0.017453292519943295;
}

double getDistance(double lat0, double lon0, double lat1, double lon1){
    lat0 = degree2rad(lat0);
    lat1 = degree2rad(lat1);
    double sDLat = sin((lat1-lat0)/2.0);
    double sdLon = sin(degree2rad(lon1-lon0)/2.0);

    double a = sDLat*sDLat+cos(lat0)*cos(lat1)*sdLon*sdLon;
    return R*(2 * atan2(sqrt(a), sqrt(1-a)));
}

class Globe{
    public:
    Mat mapMask;
    Globe(string path){
        FILE *fp;
        char buff[255];
        fp = fopen(path.c_str(), "r");
        fscanf(fp, "%s%lf%lf%lf%lf%d%d", buff, &this->latMax, &this->lonMax,
        &this->latMin, &this->lonMin, &this->latLen, &this->lonLen);
        fclose(fp);
        this->mapMask = imread(buff, IMREAD_UNCHANGED);
        this->dlat = -(this->latMax-this->latMin)/(double)(this->latLen-1);
        this->dlon = (this->lonMax-this->lonMin)/(double)(this->lonLen-1);
    }

    int latToIndex(double lat){
        return (int)((lat-this->latMax)/this->dlat);
    }

    int lonToIndex(double lon){
        return (int)((lon-this->lonMin)/this->dlon);
    }

    double latIndextoLat(int latIndex){
        return ((double)latIndex)*this->dlat+this->latMax;
    }

    double lonIndextoLon(int lonIndex){
        return ((double)lonIndex)*this->dlon+this->lonMin;
    }

    int getLatLen(){
        return this->latLen;
    }

    int getLonLen(){
        return this->lonLen;
    }
    private:
    double latMax, latMin, lonMax, lonMin, dlat, dlon;
    int latLen, lonLen;
};

const char splitter[2] = ";";
char buff8[9];
char buff4[5];