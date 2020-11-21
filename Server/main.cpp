#include <iostream>
#include <signal.h>
#include <opencv2/highgui/highgui.hpp>
#include <opencv2/core.hpp>
#include <opencv2/imgcodecs/imgcodecs.hpp>
#include <unordered_set>
#include "utils.hpp"
using namespace std;
bool on;
int c=0;
TCPServer *tcp;
World *w;
ShipsMap *ships;
SBoatsMap *sboats;
GCSMap *gcs;
fdsMap *fds;
Globe *globe;
int typeLength;
int LATMAXIDX, LONMAXIDX;
unsigned int numDetachedThread = 0;
mutex mtxNumDetachedThread, mtxShips, mtxSBoats;

void sigHandler(int s){
    printf("\n");
    on = false;
    tcp->turnOff();
    if(c++>3)exit(-1);
}

void searchShip(string boatID, int fd){
    mtxNumDetachedThread.lock();
    numDetachedThread += 1;
    mtxNumDetachedThread.unlock();
    char response0[30] = "LookingForHelpForYou";
    tcp->sendData(fd, response0 );
    string saverID;
    PQueue *pq = new PQueue;
    ShipsMap shipsCopy;
    mtxSBoats.lock();
    double d, maxRange = (double)(*sboats)[boatID].maxRange;
    double lat = (*sboats)[boatID].lat;
    double lon = (*sboats)[boatID].lon;
    mtxSBoats.unlock();
    int latIdx = globe->latToIndex(lat);
    int lonIdx = globe->lonToIndex(lon);
    int nextIdx;
    bool found = false;
    mtxShips.lock();
    World wCopy = (*w);
    shipsCopy = *ships;
    mtxShips.unlock();
    struct timeval s, e;
    gettimeofday(&s, NULL);
    pq->push(make_pair(0, make_pair(latIdx, lonIdx)));
    pair <double, pair <int, int> > node;
    pair <int, int> pos, posTemp;
    unordered_set <pair <int, int>, boost::hash <pair <int, int> > > visited;
    visited.insert(make_pair(latIdx, lonIdx));
    unsigned int maxSize = 0;
    while(pq->size() > 0 && (*sboats).find(boatID) != (*sboats).end()){
        if(pq->size() > maxSize) maxSize = pq->size();
        node = pq->top(); pq->pop();
        latIdx = node.second.first;
        lonIdx = node.second.second;
        lat = globe->latIndextoLat(latIdx);
        lon = globe->lonIndextoLon(lonIdx);
        pos = make_pair(latIdx, lonIdx);
        
        if(wCopy.find(pos) != wCopy.end()){
            saverID = wCopy[pos];
            found = true;
            break;
        }
        // if(!globe->mapMask.at<unsigned char>(latIdx, lonIdx)) { // if daratan
        //     found = true;
        //     break;
        // }
        
        nextIdx = (latIdx+1)%LATMAXIDX; // atas
        posTemp = make_pair(nextIdx, lonIdx);
        if(visited.find(posTemp) == visited.end() && globe->mapMask.at<unsigned char>(nextIdx, lonIdx)){
            // if not land
            d = node.first+getDistance(globe->latIndextoLat(nextIdx), lon, lat, lon);
            if(d < maxRange) {
                visited.insert(posTemp);
                pq->push(make_pair(d, posTemp));
            }
        }

        nextIdx = (lonIdx+1)%LONMAXIDX; // kanan
        posTemp = make_pair(latIdx, nextIdx);
        if(visited.find(posTemp) == visited.end() && globe->mapMask.at<unsigned char>(latIdx, nextIdx)){
            // if not land
            d = node.first+getDistance(lat, globe->lonIndextoLon(nextIdx), lat, lon);
            if(d < maxRange){
                visited.insert(posTemp);
                pq->push(make_pair(d, posTemp));
            }
        }

        if(latIdx > 0)nextIdx = latIdx-1; // bawah
        else nextIdx = LATMAXIDX-1;
        posTemp = make_pair(nextIdx, lonIdx);
        if(visited.find(posTemp) == visited.end() && globe->mapMask.at<unsigned char>(nextIdx, lonIdx)){
            // if not land
            d = node.first+getDistance(globe->latIndextoLat(nextIdx), lon, lat, lon);
            if(d < maxRange) {
                visited.insert(posTemp);
                pq->push(make_pair(d, posTemp));
            }
        }

        if(lonIdx > 0) nextIdx = lonIdx-1; // kiri
        else nextIdx = LONMAXIDX-1;
        posTemp = make_pair(latIdx, nextIdx);
        if(visited.find(posTemp) == visited.end() && globe->mapMask.at<unsigned char>(latIdx, nextIdx)){
            // if not land
            d = node.first+getDistance(lat, globe->lonIndextoLon(nextIdx), lat, lon);
            if(d < maxRange){
                visited.insert(posTemp);
                pq->push(make_pair(d, posTemp));
            }
        }
    }
    delete pq;
    gettimeofday(&e, NULL);
    // printf("%lf\n\n", (double)(e.tv_sec-s.tv_sec)+(double)(e.tv_usec-s.tv_usec)/1000000.0);
    mtxSBoats.lock();
    if((*sboats).find(boatID) != (*sboats).end()){
        char message[256];
        if(found && saverID.size() > 0){
            (*sboats)[boatID].saver = saverID;
            sprintf(message, "$%s;%.7lf;%.7lf", (*sboats)[boatID].saver.c_str(), shipsCopy[(*sboats)[boatID].saver].lat, shipsCopy[(*sboats)[boatID].saver].lon);
            (*sboats)[boatID].saverLat = shipsCopy[(*sboats)[boatID].saver].lat;
            (*sboats)[boatID].saverLon = shipsCopy[(*sboats)[boatID].saver].lon;
        }
        else{
            sprintf(message, "$!!");
        }
        mtxSBoats.unlock();
        // printf("%s\n", message);
        tcp->sendData(fd, message);
    }
    else mtxSBoats.unlock();
    (*sboats)[boatID].searching = false;
    mtxNumDetachedThread.lock();
    numDetachedThread -= 1;
    mtxNumDetachedThread.unlock();
}

int main(){
    on = true;
    signal(SIGINT, sigHandler);
    {
        FILE *fp;
        char ip[16], globeCfg[500];
        int port;
        fp = fopen("server.cfg", "r");
        fscanf(fp, "%s%d%s", ip, &port, globeCfg);
        fclose(fp);
        globe = new Globe(globeCfg);
        LATMAXIDX = globe->getLatLen();
        LONMAXIDX = globe->getLonLen();
        tcp = new TCPServer(ip, port);
    }
    tcp->start();
    w = new World;
    ships = new ShipsMap;
    sboats = new SBoatsMap;
    gcs = new GCSMap;
    fds = new fdsMap;
    char data[256], message[256];
    char *token;
    string id, clientType;
    struct timeval ts;
    typeLength = 4;
    int fd, minRequestDelay = 60;
    int latIndexTemp, lonIndexTemp;
    double latTemp, lonTemp;
    pair <int, int> pos;
    while(on){
        fd = tcp->getData(data);
        if(fd < 1) continue;
        // printf("%s\n", data);
        if(data[0] == '!'){
            clientType.assign((*fds)[fd], 0, typeLength);
            if(clientType.compare("SHIP") == 0){
                mtxShips.lock();
                (*w).erase(make_pair((*ships)[(*fds)[fd]].latIdx, (*ships)[(*fds)[fd]].lonIdx));
                (*ships).erase((*fds)[fd]);
                mtxShips.unlock();
            }
            else if(clientType.compare("BOAT") == 0){
                mtxSBoats.lock();
                (*sboats).erase((*fds)[fd]);
                mtxSBoats.unlock();
            }
            else if(clientType.compare("GCSt") == 0){
                (*gcs).erase((*fds)[fd]);
            }
            (*fds).erase(fd);
            continue;
        }
        token = strtok(data+1, splitter);
        if(token == NULL) continue;
        id.assign(token, 0, strlen(token));
        if((*fds).find(fd) == (*fds).end()) (*fds)[fd] = id;
        else if((*fds)[fd].compare(id) != 0) (*fds)[fd] = id;
        clientType.assign(data, 1, typeLength);
        gettimeofday(&ts, NULL);
        if(clientType.compare("SHIP") == 0){
            token = strtok(NULL, splitter);
            if(token == NULL) continue;
            latTemp = atof(token);
            token = strtok(NULL, splitter);
            if(token == NULL) continue;
            lonTemp = atof(token);
            mtxShips.lock();
            (*ships)[id].lat = latTemp;
            (*ships)[id].lon = lonTemp;
            if((*ships)[id].fd != fd) (*ships)[id].fd = fd;
            latIndexTemp = globe->latToIndex((*ships)[id].lat);
            lonIndexTemp = globe->lonToIndex((*ships)[id].lon);
            if(latIndexTemp != (*ships)[id].latIdx || lonIndexTemp != (*ships)[id].lonIdx){
                (*w).erase(make_pair((*ships)[id].latIdx, (*ships)[id].lonIdx));
                (*ships)[id].latIdx = latIndexTemp;
                (*ships)[id].lonIdx = lonIndexTemp;
                (*w)[make_pair((*ships)[id].latIdx, (*ships)[id].lonIdx)] = string(id);
            }
            mtxShips.unlock();
        }
        else if(clientType.compare("BOAT") == 0){
            token = strtok(NULL, splitter);
            if(token == NULL) continue;
            (*sboats)[id].lat = atof(token);
            token = strtok(NULL, splitter);
            if(token == NULL) continue;
            (*sboats)[id].lon = atof(token);
            token = strtok(NULL, splitter);
            if(token == NULL) continue;
            (*sboats)[id].maxRange = atoi(token+1)*1000;
            if((*sboats)[id].fd != fd) (*sboats)[id].fd = fd;
            if((*sboats)[id].status != token[0]) (*sboats)[id].status = token[0];
            // printf("%.7lf, %.7lf, %d, %c\n", (*sboats)[id].lat, (*sboats)[id].lon, (*sboats)[id].maxRange, (*sboats)[id].status);
            if((*sboats)[id].status == '3'){ // 1 picking up jackets, 2: going to land, 3: going to ship
                if((*sboats)[id].saver.size() > 0){
                    for (auto q : *ships){
                        cout << q.first << ", ";
                    }
                    cout << "<----->" << (*sboats)[id].saver << endl;
                    mtxShips.lock();
                    if((*ships).find((*sboats)[id].saver) != (*ships).end()){
                        printf("test\n");
                        sprintf(message, "$%s;%.7lf;%.7lf", (*sboats)[id].saver.c_str(), (*ships)[(*sboats)[id].saver].lat, (*ships)[(*sboats)[id].saver].lon);
                        (*sboats)[id].saverLat = (*ships)[(*sboats)[id].saver].lat;
                        (*sboats)[id].saverLon = (*ships)[(*sboats)[id].saver].lon;
                        mtxShips.unlock();
                        tcp->sendData(fd, message);
                    }
                    else{
                        mtxShips.unlock();
                        (*sboats)[id].saver = "";
                        if(!(*sboats)[id].searching){
                            (*sboats)[id].searching = true;
                            (*sboats)[id].timestamp = ts.tv_sec;
                            thread t(searchShip, id, fd);
                            t.detach();
                        }
                    }
                }
                else if(ts.tv_sec - (*sboats)[id].timestamp > minRequestDelay && !(*sboats)[id].searching){
                    (*sboats)[id].searching = true;
                    (*sboats)[id].timestamp = ts.tv_sec;
                    thread t(searchShip, id, fd);
                    t.detach();
                }
            }
        }
        else if(clientType.compare("GCSt") == 0){
            if((*gcs).find(id) == (*gcs).end()) (*gcs)[id].init(id, sboats, tcp, &mtxSBoats);
            if((*gcs)[id].fd != fd) (*gcs)[id].fd = fd;
            token = strtok(NULL, splitter);
            if(token == NULL) continue;
            char task = token[0];
            if(task == '0') (*gcs)[id].updateData();
            else{
                token = strtok(NULL, splitter);
                if(token == NULL) continue;
                string camID(token);
                if(task == '1'){
                    //turn on camera
                }
                else if(task == '2'){
                    //turn off camera
                }
            }
        }
        usleep(100);
    }
    while(numDetachedThread>0);
    delete w;
    delete gcs;
    delete ships;
    delete sboats;
    delete fds;
    delete globe;
    delete tcp;
    cout << "done\n";
    return 0;
}