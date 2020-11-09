#include <stdio.h> 
#include <sys/socket.h> 
#include <arpa/inet.h> 
#include <unistd.h> 
#include <string.h>
#include <stdlib.h>
#include <sys/time.h>
#include <time.h>
#define PORT 6969 

// char buff8[9];
// char qq[256] = "$SHIP10\0";
// double l0 = 123.1234567;
// double l1 = 33.1234789;
// memcpy(buff8, &l0, 8);
// strcat(qq, buff8);
// memcpy(buff8, &l1, 8);
// strcat(qq, buff8);
// strcat(qq, "5123");
// printf("%s\n", qq);

// double la, lo;
// int r;
// char s;
// char nm[8];
// memcpy(nm, qq+1, 6);
// memcpy(&la, qq+7, 8);
// memcpy(&lo, qq+15, 8);
// s = qq[23];
// r = atoi(qq+24);
// // sscanf(qq, "%s %f %f %d %d", &nm, &la, &lo, &r, &s);
// printf("%s\n%.7lf, %.7lf\n%c\n%d\n", nm, la, lo, s, r);
// return 0;


// srand (time(NULL));
// char asdasd[256];
// double laa = (double)rand()/RAND_MAX*180.0-90.0;
// double loo = (double)rand()/RAND_MAX*360.0-180.0;
// printf("%.7lf_%.7lf\n\n", laa, loo);
// printf("%.3d_%.3d\n\n", (int)laa, (int)loo);
// double saverLatInt = (int)laa;
// double saverLonInt = (int)loo;
// sprintf(asdasd, "$%1d%7lf%3d%7lf", (int)saverLatInt, laa-saverLatInt, (int)saverLonInt, loo-saverLonInt);

int main(int argc, char const *argv[]) 
{ 
	int sock = 0, valread; 
	struct sockaddr_in serv_addr; 
	char hello[70] = "$SHIP02\0"; 
	char buffer[256];
	if ((sock = socket(AF_INET, SOCK_STREAM, 0)) < 0) 
	{ 
		printf("\n Socket creation error \n"); 
		return -1; 
	} 

	serv_addr.sin_family = AF_INET; 
	serv_addr.sin_port = htons(PORT); 
	
	// Convert IPv4 and IPv6 addresses from text to binary form 
	if(inet_pton(AF_INET, "192.168.1.9", &serv_addr.sin_addr)<=0) 
	{ 
		printf("\nInvalid address/ Address not supported \n"); 
		return -1; 
	} 

	if (connect(sock, (struct sockaddr *)&serv_addr, sizeof(serv_addr)) < 0) 
	{ 
		printf("\nConnection Failed \n"); 
		return -1; 
	}
	srand(time(NULL));
    while(true){
		sprintf(buffer, "%s;%.7lf;%.7lf", hello, (double)rand()/RAND_MAX*180.0-90.0, (double)rand()/RAND_MAX*360.0-180.0);
        if(send(sock , buffer , strlen(buffer) , 0 ) < 1) break;
        printf("%s -- message sent\n", buffer); 
		memset(buffer, 0, sizeof(buffer));
        if(read( sock , buffer, 1024) < 1) break;; 
        printf("%s\n",buffer );
        usleep(500000);
    }
	return 0; 
} 
