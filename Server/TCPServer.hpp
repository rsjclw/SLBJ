#include <stdio.h>
#include <stdlib.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <string.h>
#include <arpa/inet.h>
#include <fcntl.h> // for open
#include <unistd.h> // for close
#include <vector>
#include <thread>
#include <mutex>
#include <unordered_map>
#include <queue>
#include <utility>
#include <sys/time.h>

using namespace std;

class ClientHandler{
    public:
    ClientHandler(int socket, mutex *m, mutex *m0, queue <pair <int, char*> > *qData, queue <int> *qDeactivate, int messageSize=256, float timeout_usec=5000000, int minMessageLength=7){
        this->running = false;
        this->fd = socket;
        this->clientMessage = (char*)calloc(messageSize, sizeof(char));
        this->t = NULL;
        this->timeout = timeout_usec;
        this->msgSize = messageSize;
        this->minMsgLength = minMessageLength;
        this->mtx = m;
        this->mtx0 = m0;
        this->data = qData;
        this->deactivateClient = qDeactivate;
        struct timeval s, e;
        gettimeofday(&s, NULL);
        while(true){
            usleep(100);
            gettimeofday(&e, NULL);
            if((e.tv_sec-s.tv_sec)*1000000+(e.tv_usec-s.tv_usec)>=this->timeout){
                deactivate();
                return;
            }
            if(recv(this->fd , this->clientMessage , messageSize , 0) >= this->minMsgLength)  if(this->clientMessage[0] == '$') break;
        }
        char temp[30]; strcpy(temp, "Hello, ");
        char name[10]; strncpy(name, this->clientMessage+1, this->minMsgLength);
        strcat(temp, name); send(this->fd, temp, sizeof(temp), 0);
        this->t = new thread(&ClientHandler::run, this);
    }
    ~ClientHandler(){
        printf("TCPServer:: deleting client %d\n", this->fd);
        this->on = false;
        if(this->t != NULL){
            this->t->join();
            delete this->t;
        }
        shutdown(this->fd, SHUT_RDWR);
        close(this->fd);
        free(this->clientMessage);
        printf("TCPServer:: client %d deleted\n", this->fd);
    }
    bool isRunning(){
        return this->running;
    }
    bool isOn(){
        return this->on;
    }
    int sendData(char *message){
        int ret = send(this->fd, message, sizeof(message), 0);
        if(ret < 1) this->deactivateClient->push(this->fd);
        return ret;
    }
    
    private:
    int fd, msgSize, minMsgLength;
    float timeout;
    bool running, on;
    char *clientMessage;
    char *messageTemp;
    queue <pair <int, char*> > *data;
    queue <int> *deactivateClient;
    thread *t;
    mutex *mtx, *mtx0;

    void run(){
        this->running = true;
        this->on = true;
        char name[this->minMsgLength+1]; strncpy(name, this->clientMessage+1, this->minMsgLength);
        char sMsg[this->minMsgLength+15] = "Received, ";
        strcat(sMsg, name);
        struct timeval s, e;
        gettimeofday(&s, NULL);
        while(this->on){
            usleep(1000);
            gettimeofday(&e, NULL);
            if((e.tv_sec-s.tv_sec)*1000000+(e.tv_usec-s.tv_usec)>=this->timeout){
                deactivate();
                break;
            }
            // printf("TCPServer:: client %d receiving\n", this->fd);
            if(recv(this->fd , this->clientMessage , this->msgSize , 0) < this->minMsgLength) continue;
            if(this->clientMessage[0] != '$') continue;
            gettimeofday(&s, NULL);
            if(send(this->fd, sMsg, sizeof(sMsg), 0) < 1) continue;
            this->messageTemp = (char*)calloc(strlen(this->clientMessage)+1, sizeof(char));
            strcpy(this->messageTemp, this->clientMessage);
            this->mtx->lock();
            this->data->push(make_pair(this->fd, this->messageTemp));
            this->mtx->unlock();
        }
        this->running = false;
        printf("TCPServer:: client %d stopped\n", this->fd);
    }

    void deactivate(){
        this->on = false;
        this->mtx0->lock();
        this->deactivateClient->push(this->fd);
        this->mtx0->unlock();
    }
};

class TCPServer{
    public:
    TCPServer(int port, int timeout_usec=5000000){
        struct sockaddr_in serverAddr;
        serverSocket = socket(AF_INET, SOCK_STREAM, 0);
        serverAddr.sin_family = AF_INET;
        serverAddr.sin_port = htons(port);
        serverAddr.sin_addr.s_addr = inet_addr("127.0.0.1");
        memset(serverAddr.sin_zero, '\0', sizeof serverAddr.sin_zero);
        this->timeout = timeout_usec;
        struct timeval timeoutTemp;
        int sec = this->timeout/1000000;
        int usec = this->timeout-sec*1000000;
        timeoutTemp.tv_sec = sec;
        timeoutTemp.tv_usec = usec;
        int flags  = fcntl(this->serverSocket, F_GETFL, 0);
        // fcntl(this->serverSocket, F_SETFL, (flags&~O_NONBLOCK));
        fcntl(this->serverSocket, F_SETFL, (flags|O_NONBLOCK));
        if(setsockopt (this->serverSocket, SOL_SOCKET, SO_RCVTIMEO, (char *)&timeoutTemp, sizeof(timeoutTemp)) < 0) printf("TCPServer:: setsockopt failed\n");
        if(setsockopt (this->serverSocket, SOL_SOCKET, SO_SNDTIMEO, (char *)&timeoutTemp, sizeof(timeoutTemp)) < 0) printf("TCPServer:: setsockopt failed\n");
        int reusable = 1;
        if(setsockopt(serverSocket, SOL_SOCKET, SO_REUSEADDR, &reusable, sizeof(int)) < 0) printf("setsockopt(SO_REUSEADDR) failed");
        bind(serverSocket, (struct sockaddr *) &serverAddr, sizeof(serverAddr));
        //Listen on the socket, with 40 max connection requests queued 
        if(listen(serverSocket, 50)==0) printf("TCPServer:: started\n");
        else printf("TCPServer:: Error\n");
        this->t = NULL;
    }
    ~TCPServer(){
        printf("TCPServer:: deleting server\n");
        this->on = false;
        if(this->t != NULL){
            this->t->join();
            delete this->t;
        }
        this->mtx0.lock();
        printf("TCPServer:: deleted\n");
        if(!this->clients.empty()){
            for (auto i : this->clients) delete this->clients[i.first];
            auto i = this->clients.begin();
            this->clients.erase(i, this->clients.end());
        }
        this->mtx0.unlock();
        printf("TCPServer:: clients deleted\n");
        while(this->data.size()){
            free(this->data.front().second);
            this->data.pop();
        }
        printf("TCPServer:: done\n");
    }
    void start(){
        this->t = new thread(&TCPServer::run, this);
    }
    void stopClient(int id){
        this->deactivateClient.push(id);
    }
    int sendData(int id, char *message){
        this->mtx0.lock();
        if(this->clients.find(id) == this->clients.end()) return -1;
        if(!this->clients[id]->isOn()) return -1;
        return this->clients[id]->sendData(message);
        this->mtx0.unlock();
    }
    int getData(char *dest, bool blocking=true){
        if(blocking) while(this->data.size() == 0 && this->on) usleep(20000);
        if(this->data.size() == 0) return -1;
        int ret = this->data.front().first;
        strcpy(dest, this->data.front().second);
        free(this->data.front().second);
        this->data.pop();
        return ret;
    }
    void turnOff(){
        this->on = false;
    }

    private:
    ClientHandler* client;
    unordered_map <int, ClientHandler*> clients;
    int serverSocket;
    int timeout;
    bool running, on;
    thread *t;
    mutex mtx, mtx0, mtx1;
    queue <pair <int, char*> > data;
    queue <int> deactivateClient;

    void run(){
        int fd, i;
        struct sockaddr_storage serverStorage;
        socklen_t addr_size;
        this->on = true;
        this->running = true;
        while(this->on){
            usleep(100000);
            addr_size = sizeof serverStorage;
            fd = accept(serverSocket, (struct sockaddr *) &serverStorage, &addr_size);
            while(this->deactivateClient.size()){
                deleteClient(this->deactivateClient.front());
                this->deactivateClient.pop();
            }
            if(fd<0) continue;
            client = new ClientHandler(fd, &this->mtx, &this->mtx1, &this->data, &this->deactivateClient);
            clients[fd] = client;
        }
        this->running = false;
    }

    void deleteClient(int id){
        this->mtx0.lock();
        delete this->clients[id];
        this->clients.erase(id);
        this->mtx0.unlock();
    }
};