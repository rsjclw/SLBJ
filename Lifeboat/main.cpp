#include <iostream>
#include <signal.h>
#include "utils.hpp"
using namespace std;
bool on;
int c=0;
TCPServer *tcp;
JacketsMap *jktMap;
BoatsMap *boatsMap;
int typeLength;
mutex mtxJkt;

void sigHandler(int s){
    printf("\n");
    on = false;
    tcp->turnOff();
    if(c++>3)exit(-1);
}

int main(){
    on = true;
    signal(SIGINT, sigHandler);
    {
        FILE *fp;
        char ip[16], t0[100], t1[100], t2[100], t3[100], t4[100], t5[100];
        int port;
        fp = fopen("lifeboat.cfg", "r");
        fscanf(fp, "%s%s%s%s%s%s%s%d", t0, t1, t2, t3, t4, t5, ip, &port);
        fclose(fp);
        tcp = new TCPServer(ip, port);
    }
    tcp->start();
    jktMap = new JacketsMap;
    boatsMap = new BoatsMap;
    char data[256];
    char *token;
    string id, clientType;
    struct timeval ts;
    typeLength = 4;
    int fd;
    double latTemp, lonTemp;
    pair <int, int> pos;
    while(on){
        fd = tcp->getData(data);
        if(fd < 1) continue;
        // printf("%s\n", data);
        if(data[0] == '!'){
            clientType.assign(data, 1, typeLength);
            if(clientType.compare("JCKT") == 0){
                mtxJkt.lock();
                jktMap->erase(fd);
                mtxJkt.unlock();
            }
            else if(clientType.compare("BOAT") == 0){
                boatsMap->erase(fd);
            }
            continue;
        }
        token = strtok(data+1, splitter);
        if(token == NULL) continue;
        id.assign(token, 0, strlen(token));
        clientType.assign(data, 1, typeLength);
        gettimeofday(&ts, NULL);
        if(clientType.compare("JCKT") == 0){
            token = strtok(NULL, splitter);
            if(token == NULL) continue;
            latTemp = atof(token);
            token = strtok(NULL, splitter);
            if(token == NULL) continue;
            lonTemp = atof(token);
            mtxJkt.lock();
            (*jktMap)[fd].lat = latTemp;
            (*jktMap)[fd].lon = lonTemp;
            mtxJkt.unlock();
        }
        else if(clientType.compare("BOAT") == 0){
            if((*boatsMap).find(fd) == (*boatsMap).end()) (*boatsMap)[fd].init(jktMap, tcp, &mtxJkt);
            if((*boatsMap)[fd].fd != fd) (*boatsMap)[fd].fd = fd;
            token = strtok(NULL, splitter);
            if(token == NULL) continue;
            char task = token[0];
            if(task == '0') (*boatsMap)[fd].updateData();
            else if(task == '1'){
                token = strtok(NULL, splitter);
                if(token == NULL) continue;
                tcp->sendData(atoi(token), "$!!");
            }
        }
        usleep(1000);
    }
    delete jktMap;
    delete boatsMap;
    delete tcp;
    cout << "done\n";
    return 0;
}