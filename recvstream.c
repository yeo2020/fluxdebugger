#include <stdio.h> //printf
#include <string.h> //memset
#include <stdlib.h> //exit(0);
#include <arpa/inet.h>
#include <sys/socket.h>
     
//#define BUFLEN 1024  //Max length of buffer
#define BUFLEN 65535  //Max length of buffer
#define PORT 2333
      
void die(char *s){
    perror(s);
    exit(1);
}

char buf[BUFLEN];

int main(void)
{
    struct sockaddr_in si_me, si_other;
        
    int s, i, slen = sizeof(si_other) , recv_len;
    int total_len = 0;

    //create a UDP socket
    if ((s=socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)) == -1)
    {
        die("socket");
    }

    // zero out the structure
    memset((char *) &si_me, 0, sizeof(si_me));

    si_me.sin_family = AF_INET;
    si_me.sin_port = htons(PORT);
    si_me.sin_addr.s_addr = htonl(INADDR_ANY);

    //bind socket to port
    if( bind(s , (struct sockaddr*)&si_me, sizeof(si_me) ) == -1)
    {
        die("bind");
    }

    //keep listening for data
    while(1)
    {
        //printf("Waiting for data...");
        fflush(stdout);
         
        //try to receive some data, this is a blocking call
        if ((recv_len = recvfrom(s, buf, BUFLEN, 0, (struct sockaddr *) &si_other, &slen)) == -1)
        {
            die("recvfrom()");
        }
         
        //print details of the client/peer and the data received
        total_len += recv_len;
        //printf("Received %d bytes packet from %s:%d\n", total_len, inet_ntoa(si_other.sin_addr), ntohs(si_other.sin_port));
        //printf("Data: %s\n" , buf);

        write(1, buf, recv_len);
         
        // if (sendto(s, buf, recv_len, 0, (struct sockaddr*) &si_other, slen) == -1) {
        //     die("sendto()");
        // }
    }
 
    close(s);
    return 0;
}
