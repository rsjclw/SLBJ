#include <vector>
#include <unordered_map>
#include <string>
#include <queue>
#include <math.h>
#include <boost/functional/hash.hpp>
#include <sys/time.h>
#include <thread>
#include "TCPServer.hpp"
#define R 6371e3 // meter
#define M_PI 3.14159265358979323846

using namespace std;

typedef struct{
    double lat, lon;
} Jacket;

typedef unordered_map <int, Jacket> JacketsMap;

class Boat{
    public:
    int fd;
    Boat(){
    }
    void init(JacketsMap *jktMap_, TCPServer *tcpServer, mutex *mtxJkt_){
        this->tcp = tcpServer;
        this->jktMap = jktMap_;
        this->updating = false;
        this->deleting = false;
        this->t = NULL;
        this->mtxjkt = mtxJkt_;
    }
    ~Boat(){
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
        t = new thread(&Boat::__updateData, this);
    }

    private:
    thread *t;
    TCPServer *tcp;
    JacketsMap *jktMap;
    bool updating, deleting;
    mutex mtxUpdate;
    mutex *mtxjkt;
    void __updateData(){
        this->mtxjkt->lock();
        JacketsMap jktMapTemp = *jktMap;
        this->mtxjkt->unlock();
        char msg[256];
        for (auto i : jktMapTemp){
            if(this->deleting) break;
            sprintf(msg, "$%d;%.7lf;%.7lf", i.first, i.second.lat, i.second.lon);
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

typedef unordered_map <int, Boat> BoatsMap;

const char splitter[2] = ";";