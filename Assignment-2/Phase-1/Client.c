#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <fcntl.h>
#include <pthread.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <arpa/inet.h>
#include <stdbool.h>
#include <signal.h>
#include <pulse/simple.h>
#include <pulse/error.h>
#include <pulse/gccmacro.h>
#include <errno.h>

#define BUFSIZE 2024001
//int requestFlag = 0;
//int acknowlegmentFlag=1;

//char chill[20]="CHILL";
//char request[20]="BUSY!";
//char acknowlegment[20]="DONE!";

void * reception(void * sockID){
		pa_simple *s2;
		pa_sample_spec ss;
		ss.format = PA_SAMPLE_S16NE;
		ss.channels = 2;
		ss.rate = 44100;
		int clientSocket = *((int *) sockID);
		while(1)
		{
			char data[1024];
			int read = recv(clientSocket,data,BUFSIZE,NULL);
	    	s2 = pa_simple_new(NULL,"talking",PA_STREAM_PLAYBACK,NULL,"talking",&ss,NULL,NULL,NULL);
			if( pa_simple_read(s2,data,BUFSIZE,NULL)){printf("error playing\n");}
			pa_simple_write(s2,data,BUFSIZE,NULL);
	    	pa_simple_flush(s2,NULL);
	    	pa_simple_free(s2);
		}


//		if(strcmp(read,request)){requestFlag=1;}
//		if(strcmp(read,acknowlegment)){acknowlegmentFlag=1;}



}


void catch(int dummy)
	{
     	char  c;
     	signal(dummy, SIG_IGN);
     	printf("EXIT? [y/n] ");
     	c = getchar();
     	if (c == 'y' || c == 'Y')
        	exit(0);
     	else
        	signal(SIGINT, catch);
     	getchar();
	}

int main(int argc,char *argv[]){

	int port;
	char username[100];
	
	port = atoi(argv[2]);
	strcpy(username,argv[1]);

	int clientSocket = socket(PF_INET, SOCK_STREAM, 0);

//	SETTING SERVER ATTRIBUTES
	struct sockaddr_in serverAddr;
	serverAddr.sin_family = AF_INET;
	serverAddr.sin_port = htons(port);
	serverAddr.sin_addr.s_addr = htonl(INADDR_ANY);

	if(connect(clientSocket, (struct sockaddr*) &serverAddr, sizeof(serverAddr)) == -1) return 0;

	printf("CONNECTED TO THE SERVER\n");

//	INTRODUCE MYSELF WITH USERNAME
	send(clientSocket,username,1024,0);

	pthread_t thread;
	pthread_create(&thread, NULL, reception, (void *) &clientSocket );

//	CATCHES THE SIGINT SIGNAL
	signal(SIGINT, catch);

//	DECLARING AND SETTING ATTRIBUTES OF AUDIO - SAMPLING AND NO OF CHANNELS
	pa_simple *s1;
	pa_sample_spec ss;
	ss.format = PA_SAMPLE_S16NE;
	ss.channels = 2;
	ss.rate = 28100;
	int buf[BUFSIZE];

//	RECORDS WHENEVER USER HITS ENTER

	char ch[2];
//	while(fgets(ch,2,stdin)&&(!request)&&(acknowlegment))
	while(fgets(ch,2,stdin))
	{

//	CREATING AND CONNECTING STREAMS FOR RECORDING AND PLAYBACK 
		s1 = pa_simple_new(NULL,"listen",PA_STREAM_RECORD,NULL,"listen",&ss,NULL,NULL,NULL);

//	READ RECORDED INTO BUFFER		
		printf("you're in!\n");
		if( pa_simple_read(s1,buf,BUFSIZE,NULL)){printf("error recording\n");}

//	FLUSH AND FREE THE STREAM
		pa_simple_flush(s1,NULL);
		pa_simple_free(s1);

//	SEND THE RECORDED AUDIO
		send(clientSocket,buf,BUFSIZE,NULL);

	}
}
