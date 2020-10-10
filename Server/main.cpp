#include <sys/time.h>
#include <iostream>
#include <unistd.h>
#include <thread>
#include <signal.h>
#include <netdb.h>
#include "TCPServer.hpp"
using namespace std;
bool on;
TCPServer *tcp;
void sigHandler(int s){
    printf("\n");
    int c=0;
    on = false;
    tcp->turnOff();
    if(c++>3)exit(-1);
}
int main(){
    on = true;
    signal(SIGINT, sigHandler);
    tcp = new TCPServer("192.168.43.247", 6969);
    tcp->start();
    char data[256];
    while(on){
        if(tcp->getData(data) > 0) printf("%s\n", data);
    }
    delete tcp;
    cout << "done\n";
    return 0;
}