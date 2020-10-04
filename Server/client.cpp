#include <stdio.h> 
#include <sys/socket.h> 
#include <arpa/inet.h> 
#include <unistd.h> 
#include <string.h>
#include <stdlib.h> 
#define PORT 6969 

int main(int argc, char const *argv[]) 
{ 
	int sock = 0, valread; 
	struct sockaddr_in serv_addr; 
	char hello[8] = "$SHIP02"; 
	char buffer[1024] = {0}; 
	if ((sock = socket(AF_INET, SOCK_STREAM, 0)) < 0) 
	{ 
		printf("\n Socket creation error \n"); 
		return -1; 
	} 

	serv_addr.sin_family = AF_INET; 
	serv_addr.sin_port = htons(PORT); 
	
	// Convert IPv4 and IPv6 addresses from text to binary form 
	if(inet_pton(AF_INET, "127.0.0.1", &serv_addr.sin_addr)<=0) 
	{ 
		printf("\nInvalid address/ Address not supported \n"); 
		return -1; 
	} 

	if (connect(sock, (struct sockaddr *)&serv_addr, sizeof(serv_addr)) < 0) 
	{ 
		printf("\nConnection Failed \n"); 
		return -1; 
	}
    int i=0;
    char temp[50];
    while(true){
        strcpy(buffer, hello);
        sprintf(temp, "%d", i);
        strcat(buffer, temp);
        if(send(sock , buffer , strlen(buffer) , 0 ) < 1) break;
        printf("%s -- message sent\n", buffer); 
		memset(buffer, 0, sizeof(buffer));
        if(read( sock , buffer, 1024) < 1) break;; 
        printf("%s\n",buffer );
        i++;
        i%=1000;
        usleep(500000);
    }
	return 0; 
} 
